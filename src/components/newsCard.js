import React from "react";
import moment from "moment";
import { Link } from "react-router-dom";

function RelatedNews(props) {
  if (props.relatedArticles == null) {
    return <></>;
  }
  return (
    <ul className="news-related list-group list-group-flush">
      {props.relatedArticles.map((article) => (
        <li className="list-group-item">
          <a href={article.url} target="_blank" rel="noopener noreferrer">
            {article.title}
          </a>
          <NewsMetadata article={article} />
        </li>
      ))}
    </ul>
  );
}

function NewsMetadata(props) {
  let website = props.article.website;
  let date = moment(props.article.date, "X").utc();
  let websiteLookup = {
    'moneycontrol': "Moneycontrol",
    'thehindubusinessline': "Business Line",
    'business-standard': "Business Standard",
    'economictimes': 'Economic Times'
  };
  return (
    <small>
      <span className="news-time" title={date.format("D MMMM Y h:mm A")}>
        {date.fromNow()}
      </span>{" "}
      - <span className="news-source">{websiteLookup[website]}</span>
    </small>
  );
}

function NewsCard(props) {
  let article = props.article;

  return (
    <div className="news-card card">
      <div className="card-body">
        <h5 className="news-title card-title">
          <a href={article.url} target="_blank" rel="noopener noreferrer">
            {article.title}
          </a>
        </h5>
        <div className="news-body">
          <p className="news-description">{article.description}</p>
          <p className="news-meta">
            <NewsMetadata article={article} />
          </p>
          <RelatedNews relatedArticles={article.related_articles} />
        </div>
        <div className="news-footer">
          <div className="news-tags">
            {article.tags.map((tag) => (
              <span className="news-hash-tag" key={tag}>
                <Link to={`/tag/${tag}`}>#{tag}</Link>
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default NewsCard;
