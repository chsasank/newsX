import re
import fasttext
from .scrape_news import get_db_conn
from tqdm.auto import tqdm
from pyfasttext import FastText

def normalize_text(text):
    """Normalize text to remove all non word, space characters.

    Args:
        text(str): Text to be normalized.

    Returns:
        str: Normalized text.
    """
    text = re.sub('[^0-9a-zA-Z\.]+', ' ', text)
    text = text.lower()
    return text


def _ft_pred_to_final(labels, probs):
    # select top 4
    labels = labels[:4]
    probs = probs[:4]

    return [
        x.replace('__label__', '')
        for x, p in zip(labels, probs)
        if p > probs[0] / 2
    ]


def update_tags(min_date=None, website=None):
    model = fasttext.load_model('news_model.bin')
    qry = {'description': {'$exists': True}}

    if min_date is not None:
        qry['date'] = {'$gt': min_date}

    if website is not None:
        qry['website'] = website

    with get_db_conn() as conn:
        all_articles = conn.finance.news.find(qry, {'html': 0})

        for article in tqdm(all_articles):
            full_text = normalize_text(
                ' '.join(article[x] for x in ['title', 'description'])
            )
            labels, probs = model.predict(full_text, k=4, threshold=0.1)
            final_labels = _ft_pred_to_final(labels, probs)
            conn.finance.news.update_one(
                {'_id': article['_id']},
                {'$set': {'predicted_tags': final_labels}}
            )