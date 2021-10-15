import React, { useState, useEffect } from "react";
import Masonry from "react-masonry-css";
import axios from "axios";
import NewsCard from "./newsCard.js";
import InfiniteScroll from "react-infinite-scroller";
import { Link } from "react-router-dom";
import arrowRightSVG from "../assets/arrow-right.svg";

function Loading(props) {
  if (props.loading) {
    return (
      <div className="news-loading text-center">
        <div className="spinner-border" role="status">
          <span className="sr-only">Loading...</span>
        </div>
      </div>
    );
  } else {
    return <></>;
  }
}

function NewsCardDeck(props) {
  const breakPointsColumns = {
    default: 3,
    768: 2,
    576: 1,
  };
  let tag = props.sectionName
  return (
    <div className="news-section">
      <h2 className="news-section-header">
        <Link to={`/tag/${tag}`}>#{tag}</Link>
      </h2>
      <Masonry
        breakpointCols={breakPointsColumns}
        className="my-masonry-grid"
        columnClassName="my-masonry-grid_column"
      >
        {props.articlesList.map((article) => (
          <NewsCard key={article.url} article={article} />
        ))}
      </Masonry>
      <h5 className="news-section-read-more float-right">
        <Link to={`/tag/${tag}`}>
          Read more {tag} news <img src={arrowRightSVG}></img>
        </Link>
      </h5>
    </div>
  );
}

function NewsSection(props) {
  const [loading, setLoading] = useState(true);
  const [articlesList, setArticlesList] = useState([]);

  const tag = props.tag || "latest";
  const numArticles = props.numArticles || 9;
  const infiniteScroll = props.infiniteScroll || false;

  function loadMoreArticles() {
    setLoading(true);
    axios
      .get("/api/articles", {
        params: {
          tag: tag,
          offset: articlesList.length,
          limit: numArticles,
        },
      })
      .then((response) => {
        let newArticles = response.data;
        setArticlesList([...articlesList, ...newArticles]);
        setLoading(false);
      });
  }
  useEffect(() => loadMoreArticles(), []);

  if (infiniteScroll) {
    return (
      <InfiniteScroll
        loadMore={loadMoreArticles}
        hasMore={articlesList.length < 500}
        loader={<Loading key={0} loading={loading} />}
      >
        <NewsCardDeck articlesList={articlesList} sectionName={tag} />
      </InfiniteScroll>
    );
  } else {
    return (
      <>
        <NewsCardDeck articlesList={articlesList} sectionName={tag} />
        <Loading key={0} loading={loading} />
      </>
    );
  }
}

export default NewsSection;
