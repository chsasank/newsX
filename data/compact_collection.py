import gzip

import bson
import gridfs
from pymongo import MongoClient
from tqdm.auto import tqdm

db = MongoClient().finance
fs = gridfs.GridFS(db)


def transform(article):
    try:
        html = article['html']
    except KeyError:
        return

    if isinstance(html, bson.objectid.ObjectId):
        return

    html = gzip.compress(html)
    html_id = fs.put(html, file_name=article['_id'] + '.html.gz')

    db.news.update_one(
        {'_id': article['_id']},
        {'$set': {'html': html_id}}
    )


all_articles = db.news.find()
num_articles = db.news.count()

for article in tqdm(all_articles, total=num_articles):
    transform(article)
