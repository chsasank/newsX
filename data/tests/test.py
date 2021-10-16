from news_lib.scrape_news import get_db_conn, MoneyControlScraper, \
    BusinessLineScraper, BusinessStandardScraper, EconomicTimesScraper
from datetime import datetime, timedelta

min_date = datetime.now() - timedelta(days=2)


def test_money_control_scraper():
    with get_db_conn() as conn:
        scraper = MoneyControlScraper(conn)

        scraper.batch_get_archive(min_date)
        scraper.batch_fetch_html(min_date)

        article = scraper.collection.find_one({'website': scraper.website})
        scraper.parse_html(article)


def test_bussiness_line_scraper():
    with get_db_conn() as conn:
        scraper = BusinessLineScraper(conn)

        scraper.batch_get_archive(min_date)
        scraper.batch_fetch_html(min_date)

        article = scraper.collection.find_one({'website': scraper.website})
        scraper.parse_html(article)


def test_bussiness_standard_scraper():
    with get_db_conn() as conn:
        scraper = BusinessStandardScraper(conn)

        scraper.batch_get_archive(min_date)
        scraper.batch_fetch_html(min_date)

        article = scraper.collection.find_one({'website': scraper.website})
        print(article['url'])
        scraper.parse_html(article)


def test_economic_times_scraper():
    with get_db_conn() as conn:
        scraper = EconomicTimesScraper(conn)

        # scraper.batch_get_archive(min_date)
        # scraper.batch_fetch_html(min_date)

        article = scraper.collection.find_one({
            'website': scraper.website,
            'html': {'$exists': True}
        })
        scraper.parse_html(article)

if __name__ == "__main__":
    # test_money_control_scraper()
    # test_bussiness_line_scraper()
    # test_bussiness_standard_scraper()
    test_economic_times_scraper()