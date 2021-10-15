import argparse
import dateutil.parser
from datetime import datetime, timedelta
from news_lib.update_db import populate_articles, parse_articles_text, \
    fetch_articles_html
from news_lib.nlp import update_tags

parser = argparse.ArgumentParser()
parser.add_argument("action", default=None, nargs='?')
parser.add_argument("--min_date", default=None)
parser.add_argument("--website", default=None)
args = parser.parse_args()

if args.min_date is None:
    min_date = datetime.now() - timedelta(days=1)
else:
    min_date = dateutil.parser.parse(args.min_date)

kwargs = {
    'min_date': min_date,
    'website': args.website
}
if args.action == 'populate_articles':
    populate_articles(**kwargs)
elif args.action == 'fetch_html':
    fetch_articles_html(**kwargs)
elif args.action == 'parse_html':
    parse_articles_text(**kwargs)
elif args.action == 'update_tags':
    update_tags(**kwargs)
elif args.action is None:
    populate_articles(**kwargs)
    fetch_articles_html(**kwargs)
    parse_articles_text(**kwargs)
    update_tags(**kwargs)
else:
    raise NotImplementedError
