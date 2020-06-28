import gzip
from datetime import timezone

from flask import Flask, jsonify, request
from mongoengine import (DateTimeField, Document, FileField, ListField,
                         StringField)
from mongoengine import connect as mongodb_connect

app = Flask(__name__)

conn = mongodb_connect(
    db='finance',
    host='192.168.7.116',
    username='newsReader',
    password='read',
    authentication_source='finance'
)


class Article(Document):
    meta = {'collection': 'news'}
    id = StringField(db_field='_id', primary_key=True)
    url = StringField()
    title = StringField()
    description = StringField()
    website = StringField()
    date = DateTimeField()
    image = StringField()

    html = FileField()
    text = StringField()

    category = StringField()
    tags = ListField(StringField())
    keywords = ListField(StringField())

    predicted_tags = ListField(StringField())

    def get_html(self):
        return gzip.decompress(self.html.read())

    def put_html(self, html):
        self.html.put(
            gzip.compress(html),
            file_name=f'{self.id}.html.gz'
        )


@app.route('/api/articles')
def get_articles():
    tag = request.args.get('tag')
    limit = request.args.get('limit', default=9, type=int)
    offset = request.args.get('offset', default=0, type=int)

    if tag is None or tag == 'latest':
        articles = Article.objects()
    else:
        articles = Article.objects(predicted_tags=tag)

    articles = articles.order_by('-date')[offset: offset + limit]
    return jsonify([
        {
            'id': article.id,
            'url': article.url,
            'title': article.title,
            'website': article.website,
            'description': article.description,
            'date': article.date.replace(tzinfo=timezone.utc).timestamp(),
            'tags': article.predicted_tags,
        }
        for article in articles
    ])
