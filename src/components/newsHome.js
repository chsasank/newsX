import React from "react";
import InfiniteScroll from "react-infinite-scroller";
import { useState, useEffect } from "react";
import NewsSection from "./newsSection";
import Loading from "./loading";
import allTagsList from "../tagList.json"

function Home() {
  const [loadingnew, setLoadingNew] = useState(true);
  const [tagList, setTagList] = useState(allTagsList.slice(0, 4));

  function loadMoreTags() {
    setLoadingNew(true);
    let newTag = allTagsList[tagList.length];
    setTagList([...tagList, newTag]);
    setLoadingNew(false);
  }
  useEffect(() => loadMoreTags(), []);

  return (
    <InfiniteScroll
      loadMore={loadMoreTags}
      hasMore={tagList.length < 50}
      loader={<Loading key={0} loading={loadingnew} />}
    >
      {tagList.map((x) => (
        <NewsSection key={x} tag={x} />
      ))}
    </InfiniteScroll>
  );
}

export default Home;
