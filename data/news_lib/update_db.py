import multiprocessing.dummy
import time
from datetime import datetime
from functools import partial

from tqdm.auto import tqdm

from .scrape_news import get_db_conn, available_scrappers

DEFAULT_MIN_DATE = datetime(2009, 8, 15)


def populate_articles(min_date=DEFAULT_MIN_DATE, website=None):
    if website is None:
        scrapers = available_scrappers
    else:
        scrapers = {website: available_scrappers[website]}
    with get_db_conn() as conn:
        for website, scraper_class in scrapers.items():
            scraper = scraper_class(conn)
            scraper.batch_get_archive(min_date)


def fetch_articles_html(min_date=DEFAULT_MIN_DATE, website=None):
    if website is None:
        scrapers = available_scrappers
    else:
        scrapers = {website: available_scrappers[website]}

    with get_db_conn() as conn:
        for website, scraper_class in scrapers.items():
            scraper = scraper_class(conn)
            scraper.batch_fetch_html(min_date)


def _chunks(sequence, chunk_size):
    # Chunks of 1000 documents at a time.
    return [
        sequence[j:j + chunk_size]
        for j in range(0, len(sequence), chunk_size)
    ]


def _parse_chunk(articles_chunk):
    with get_db_conn() as conn:
        scrapers = {
            website: scraper(conn)
            for website, scraper in available_scrappers.items()
        }
        for article in articles_chunk:
            try:
                scrapers[article['website']].parse_html(article)
            except AttributeError:
                pass
            except Exception as e:
                print('ignored', e, article['url'], article['_id'])
                # raise


def parse_articles_text(min_date=DEFAULT_MIN_DATE, website=None):
    qry = {
        'html': {'$exists': True},
        'text': {'$exists': False},
        'date': {'$gt': min_date}
    }
    if website is not None:
        qry['website'] = website

    with get_db_conn() as conn:
        all_articles = list(conn.finance.news.find(
            qry, {'html': 1, 'website': 1, 'url': 1}
        ))
        article_chunks = _chunks(all_articles, chunk_size=1000)

    # with multiprocessing.Pool(8) as p:
    list(tqdm(
        map(_parse_chunk, article_chunks),
        total=len(article_chunks),
        desc="parsing html",
        unit_scale=1000,
    ))
