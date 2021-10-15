import gzip
import logging
import math
import multiprocessing.dummy
import re
import time
from datetime import datetime, timedelta, timezone

import dateutil.parser
import gridfs
import pymongo
import requests
from bs4 import BeautifulSoup
from tqdm.auto import tqdm

logger = logging.getLogger(__name__)


def daterange(start_date, end_date):
    start_date = datetime(start_date.year, start_date.month, start_date.day)
    return [
        start_date + timedelta(n)
        for n in range(int((end_date - start_date).days) + 1)
    ]


def get_db_conn():
    conn = pymongo.MongoClient(
        username="newsWriter", password="write", authSource="finance"
    )
    return conn


def parse_datetime(date_str):
    return dateutil.parser.parse(date_str)\
        .astimezone(timezone.utc).replace(tzinfo=None)


class NewsScraper:
    def __init__(self, conn):
        self.conn = conn
        self.collection = self.conn.finance.news
        self.fs = gridfs.GridFS(conn.finance)

    def _get_html_from_fs(self, article):
        article["html"] = gzip.decompress(self.fs.get(article["html"]).read())
        return article

    def url_to_id(self, url):
        raise NotImplementedError

    def get_archive(self, date):
        raise NotImplementedError

    def get_latest(self):
        raise NotImplementedError

    def verify_html_title(self, title):
        raise NotImplementedError

    def fetch_html(self, article):
        url = article["url"]
        try:
            r = requests.get(url)
            assert r.status_code == 200

            html_content = r.content
            soup = BeautifulSoup(html_content, "lxml")
            title = soup.find("title").text.lower()
            self.verify_html_title(title)

            html_content = gzip.compress(html_content)
            html_id = self.fs.put(
                html_content, file_name=article["_id"] + ".html.gz")

            self.collection.update_one(
                {"_id": article["_id"]},
                {"$set": {"html": html_id}})
        except (AttributeError, AssertionError,
                requests.exceptions.RequestException):
            logger.debug(f"ignored {article}")

    def parse_html(self, article):
        assert article['website'] == self.website
        article = self._get_html_from_fs(article)

        def _search_meta(meta_attributes, search_keys):
            for search_key in search_keys:
                for item in meta_attributes:
                    if item.get("name") == search_key or \
                            item.get("property") == search_key or \
                            item.get("http-equiv") == search_key:
                        return item["content"].strip()

        soup = BeautifulSoup(article["html"], "lxml")
        meta_attributes = [
            meta.attrs for meta in soup.find("head").find_all("meta")]
        search_keys_dict = {
            "title": ["twitter:title", "og:title", "title"],
            "description": ["twitter:description", "og:description",
                            "description"],
            "keywords": ["news_keywords", "keywords", "Keywords"],
            "date": ["Last-Modified", "last-modified",
                     "modified-date", "article:modified_time"],
            "image": ["twitter:image:src", "og:image"],
        }

        parsed_meta = {
            tag: _search_meta(meta_attributes, search_keys)
            for tag, search_keys in search_keys_dict.items()
        }

        parsed_meta["keywords"] = [
            x.strip().lower() for x in parsed_meta["keywords"].split(",")
        ]
        try:
            parsed_meta["date"] = parse_datetime(parsed_meta["date"])
        except dateutil.parser.ParserError:
            pass

        return parsed_meta, soup

    def batch_fetch_html(self, min_date=None):
        qry = {
            'html': {'$exists': False},
            'website': self.website
        }
        if min_date is not None:
            qry['date'] = {'$gt': min_date}

        articles = list(self.collection.find(qry, {'website': 1, 'url': 1}))

        with multiprocessing.dummy.Pool(16) as p:
            list(tqdm(
                p.imap(self.fetch_html, articles),
                total=len(articles),
                desc=f'fetching {self.website} html'
            ))

    def batch_get_archive(self, min_date=None):
        raise NotImplementedError


class MoneyControlScraper(NewsScraper):
    def __init__(self, conn):
        super().__init__(conn)
        self.website = "moneycontrol"

    def url_to_id(self, url):
        assert self.website in url
        article_id = re.search(r"-(\d+)\.html$", url).group(1)
        return f"moneycontrol-{article_id}"

    def verify_html_title(self, title):
        title = title.lower()
        assert "moneycontrol" in title or "cnbc" in title

    def get_archive(self, page_num):
        archive_url = \
            f"https://www.moneycontrol.com/news/news-all/page-{page_num}/"
        r = requests.get(archive_url)
        html_content = r.content
        soup = BeautifulSoup(html_content, "lxml")

        archive_title = soup.find("title").text.lower()
        assert "latest news" in archive_title, f"{archive_title} {archive_url}"
        assert r.status_code == 200

        news_list = soup.find("ul", id="cagetory").findAll(
            "li", class_="clearfix")
        for news_item in news_list:
            try:
                title = news_item.find("h2").text.strip()
                url = news_item.find("a").attrs["href"]
                description = news_item.find("p").text.strip()
                date_str = news_item.find("span").text.strip()
                date = parse_datetime(date_str)
                img = news_item.find("img").attrs["data"]

                doc = {
                    "_id": self.url_to_id(url),
                    "url": url,
                    "title": title,
                    "date": date,
                    "description": description,
                    "website": self.website,
                    "image": img,
                }
                self.collection.insert_one(doc)
            except pymongo.errors.DuplicateKeyError:
                logger.debug(f"duplicate {page_num} {url}")
            except AttributeError:
                logger.info(f"issue {page_num} {url}")
                raise

    def get_latest(self):
        pass

    def parse_html(self, article):
        parsed, soup = super().parse_html(article)
        main_div = soup.find(id="article-main")
        parsed["text"] = "\n".join(
            x.text for x in main_div.find_all("p") if "ALSO READ" not in x.text
        )

        try:
            # date in meta is inaccurate
            date_str = soup.find(class_="arttidate").text
            date_str = re.search(r"\:(.*)\|", date_str).group(1)
            parsed["date"] = parse_datetime(date_str)
        except dateutil.parser.ParserError:
            date_str = soup.find(class_="arttidate_pub").text
            date_str = re.search(r"on (.*)$", date_str).group(1)
            parsed["date"] = parse_datetime(date_str)

        try:
            tags_div = soup.find("h3", class_="tag_txt").find_all("a")
            parsed["tags"] = [x.attrs["title"].strip().lower()
                              for x in tags_div]
        except AttributeError:
            parsed["tags"] = []

        category_div = soup.find(class_="brad_crum").find(
            class_="FL").find_all("a")
        parsed["category"] = category_div[-1].text.strip().lower()

        self.collection.update_one(
            {'_id': article['_id']}, {'$set': parsed}
        )

    def batch_get_archive(self, min_date=None):
        if min_date is None:
            page_nums = list(range(1, 32000))
        else:
            num_days = (datetime.today() - min_date).days
            page_nums = list(range(1, num_days * 20))

        with multiprocessing.dummy.Pool(16) as p:
            list(tqdm(
                p.imap(self.get_archive, page_nums),
                total=len(page_nums),
                desc='populating moneycontrol articles'
            ))


class BusinessLineScraper(NewsScraper):
    def __init__(self, conn):
        super().__init__(conn)
        self.website = "thehindubusinessline"

    def url_to_id(self, url):
        assert self.website in url
        article_id = re.search(r"article(\d+).ece", url).group(1)
        return f"thehindubusinessline-{article_id}"

    def verify_html_title(self, title):
        assert "businessline" in title.lower()

    def get_archive(self, date):
        archive_url = date.strftime("%Y/%m/%d")
        archive_url = \
            f"https://www.thehindubusinessline.com/archive/web/{archive_url}/"
        r = requests.get(archive_url)
        html_content = r.content
        soup = BeautifulSoup(html_content, "lxml")

        title = soup.find("title").text.lower()
        assert "archive news" in title, f"{title} {archive_url}"
        assert r.status_code == 200

        archive_list = soup.findAll("ul", class_="archive-list")
        for archive in archive_list:
            for link in archive.findAll("a"):
                try:
                    url = link.attrs["href"]
                    title = link.text
                    doc = {
                        "_id": self.url_to_id(url),
                        "url": url,
                        "title": title,
                        "date": date,
                        "website": self.website,
                    }
                    self.collection.insert_one(doc)
                except pymongo.errors.DuplicateKeyError:
                    logger.debug("duplicate", date, url)
                except AttributeError:
                    logger.exception("issue", date, url)

    def get_latest(self):
        latest_url = "https://www.thehindubusinessline.com/latest-news/"
        r = requests.get(latest_url)
        html_content = r.content
        soup = BeautifulSoup(html_content, "lxml")

        date_str = soup.find("h5", class_="lnewstodydat").text
        latest_news = soup.find("ul", class_="latest-news")
        for item in latest_news.find_all("li"):
            link = item.find("a")
            url = link.attrs["href"]
            title = link.text.strip()
            time_str = item.find("span", class_="l-datetime").text
            date = parse_datetime(f"{date_str} {time_str} IST")
            doc = {
                "_id": self.url_to_id(url),
                "url": url,
                "title": title,
                "date": date,
                "website": "thehindubusinessline",
            }
            try:
                self.collection.finance.news.insert_one(doc)
            except pymongo.errors.DuplicateKeyError:
                logger.debug("duplicate", url)

    def parse_html(self, article):
        parsed, soup = super().parse_html(article)

        main_div = soup.find("div", id=re.compile("content-body*"))
        parsed["text"] = main_div.get_text(separator="\n").strip()

        tags_div = soup.findAll("div", class_="tag-button-inscroll")
        parsed["tags"] = [x.text.strip().lower() for x in tags_div]

        category_div = soup.find("h4", class_="in-sl-title").find("a")
        parsed["category"] = category_div.text.strip().lower()

        self.collection.update_one(
            {'_id': article['_id']}, {'$set': parsed}
        )

    def batch_get_archive(self, min_date=None):
        self.get_latest()

        if min_date is None:
            min_date = datetime(2009, 8, 15)

        all_dates = daterange(min_date, datetime.today())

        desc = f'populating {self.website} articles'
        for date in tqdm(all_dates, desc=desc):
            self.get_archive(date)
            time.sleep(2)


class BusinessStandardScraper(NewsScraper):
    def __init__(self, conn):
        super().__init__(conn)
        self.website = "business-standard"

    def url_to_id(self, url):
        assert self.website in url
        article_id = re.search(r"-(\d+)_1\.html", url).group(1)
        return f"business-standard-{article_id}"

    def verify_html_title(self, title):
        assert "business standard" in title.lower()

    def get_archive(self, date):
        archive_url = (
            f'https://www.business-standard.com/latest-news?'
            f'print_dd={date.day:02d}&'
            f'print_mm={date.month:02d}&'
            f'print_yy={date.year}')
        r = requests.get(archive_url)
        html_content = r.content
        soup = BeautifulSoup(html_content, "lxml")

        title = soup.find("title").text.lower()
        assert "latest news" in title, f"{title} {archive_url}"
        assert r.status_code == 200

        date_html = soup.find(id='dateb').attrs['value']
        date_html = dateutil.parser.parse(date_html, dayfirst=False)
        assert (date - date_html).days == 0

        archive_list = soup.findAll("ul", class_="aticle-txt")
        for archive in archive_list:
            for item in archive.find_all('h2'):
                url = item.find('a').attrs['href']
                url = 'https://www.business-standard.com' + url

                search = re.search(r"([\d\:]+) \| (.*)", item.text)
                time = search.group(1)
                title = search.group(2).strip()

                article_date = datetime.strptime(
                    date.strftime("%Y/%m/%d") + ' ' + time,
                    "%Y/%m/%d %H:%M"
                ).astimezone(timezone.utc).replace(tzinfo=None)

                try:
                    doc = {
                        "_id": self.url_to_id(url),
                        "url": url,
                        "title": title,
                        "date": article_date,
                        "website": self.website
                    }
                    self.collection.insert_one(doc)
                except pymongo.errors.DuplicateKeyError:
                    logger.debug("duplicate", date, url)
                except AttributeError:
                    print('ignored', date, url)

    def parse_html(self, article):
        parsed, soup = super().parse_html(article)

        main_div = soup.find("div", class_='story-content')
        parsed["text"] = '\n'.join(
            x.text for x in main_div.find_all('p')
        )

        tags_div = soup.findAll("div", class_="readmore_tagBG")
        parsed["tags"] = [x.text.strip().lower() for x in tags_div]

        # TODO: switch all categories to list
        category_div = soup.find("div", class_="breadcrum").find_all("a")
        parsed["category"] = [x.text.strip().lower() for x in category_div]

        self.collection.update_one(
            {'_id': article['_id']}, {'$set': parsed}
        )

    def batch_get_archive(self, min_date=None):
        if min_date is None:
            min_date = datetime(2009, 8, 15)

        all_dates = daterange(min_date, datetime.today())

        desc = f'populating {self.website} articles'
        for date in tqdm(all_dates, desc=desc):
            self.get_archive(date)


class EconomicTimesScraper(NewsScraper):
    def __init__(self, conn):
        super().__init__(conn)
        self.website = "economictimes"

    def verify_html_title(self, title):
        assert "economic times" in title.lower()

    def url_to_id(self, url):
        assert self.website in url
        article_id = re.search(r"\/(\d+)\.cms", url).group(1)
        return f"{self.website}-{article_id}"

    def _date_to_archive_starttime(self, date):
        date = datetime(date.year, date.month, date.day)
        ref = datetime(1899, 12, 30, 0, 0)  # from ET JS
        return math.floor((date - ref).total_seconds() / 86400)

    def get_archive(self, date):
        archive_url = (
            f'https://economictimes.indiatimes.com/archivelist/'
            f'year-{date.year},month-{date.month},'
            f'starttime-{self._date_to_archive_starttime(date)}.cms'
        )
        r = requests.get(archive_url)
        assert r.status_code == 200

        html_content = r.content
        soup = BeautifulSoup(html_content, "lxml")
        title = soup.find("title").text.lower()
        assert "breaking news" in title, f"{title} {archive_url}"

        date_html = soup.find('td', class_='contentbox5').find_all('b')[-1]
        date_html = parse_datetime(date_html.text)
        assert (date - date_html).days == 0

        archive_list = soup.findAll("ul", class_="content")
        for archive in archive_list:
            for item in archive.find_all('li'):
                url = item.find('a').attrs['href']
                url = 'https://economictimes.indiatimes.com' + url
                title = item.text.strip()

                try:
                    doc = {
                        "_id": self.url_to_id(url),
                        "url": url,
                        "title": title,
                        "date": date,
                        "website": self.website
                    }
                    self.collection.insert_one(doc)
                except pymongo.errors.DuplicateKeyError:
                    logger.debug("duplicate", date, url)
                except AttributeError:
                    print('ignored', date, url)

    def get_latest(self):
        for idx in tqdm(range(0, 20), 
                        desc=f'populating latest {self.website} articles'):
            latest_url = (
                f'https://economictimes.indiatimes.com/'
                f'etlatestnewsupdate.cms?curpg={idx}'
            )
            r = requests.get(latest_url)
            assert r.status_code == 200

            html_content = r.content
            soup = BeautifulSoup(html_content, "lxml")
            for item in soup.find_all('li'):
                link = item.find('a')
                url = 'https://economictimes.indiatimes.com' + \
                    link.attrs['href']
                title = link.text
                date = parse_datetime(item.find(class_='timestamp').text)
                description = item.find('p').text

                try:
                    doc = {
                        "_id": self.url_to_id(url),
                        "url": url,
                        "title": title,
                        "date": date,
                        "description": description,
                        "website": self.website
                    }
                    self.collection.insert_one(doc)
                except pymongo.errors.DuplicateKeyError:
                    logger.debug("duplicate", date, url)
                except AttributeError:
                    print('ignored', date, url)

    def parse_html(self, article):
        try:
            parsed, soup = super().parse_html(article)
            date = soup.find(class_='publish_on').text.replace(
                'Last Updated: ', '').replace('.', ':')
            parsed['date'] = parse_datetime(date)
        except (dateutil.parser.ParserError, TypeError):
            logger.info('ignored', article['url'])
            return

        main_div = soup.find('div', class_='artText')
        parsed["text"] = main_div.get_text(separator="\n").strip()

        tags_div = soup.findAll("div", class_="rdMrBulDiv")
        parsed["tags"] = [x.text.strip().lower() for x in tags_div]

        category_div = soup.find("div", class_="breadCrumb").find_all(
            "a", itemprop="item")
        parsed["category"] = [x.text.strip().lower() for x in category_div]

        self.collection.update_one(
            {'_id': article['_id']}, {'$set': parsed}
        )

    def batch_get_archive(self, min_date=None):
        self.get_latest()
        if min_date is None:
            min_date = datetime(2009, 8, 15)

        all_dates = daterange(min_date, datetime.today())

        desc = f'populating {self.website} articles'
        for date in tqdm(all_dates, desc=desc):
            self.get_archive(date)


available_scrappers = {
    'moneycontrol': MoneyControlScraper,
    'thehindubusinessline': BusinessLineScraper,
    'business-standard': BusinessStandardScraper,
    'economictimes': EconomicTimesScraper
}
