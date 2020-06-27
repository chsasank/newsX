import React, { useState, useEffect } from 'react';
import Masonry from 'react-masonry-css'
import axios from 'axios'
import NewsCard from './newsCard.js'


function Loading(props){
  if (props.loading){
    return <div class="news-loading text-center">
      <div class="spinner-border" role="status">
        <span class="sr-only">Loading...</span>
      </div>
    </div>
  }
  else {
    return <></>
  }
}


function NewsCardDeck(props){
  return (
    <div className="news-section">
      <h2 className="news-section-header">#{props.sectionName}</h2>
      {/* TODO: Breakpoint with width */}
      <Masonry breakpointCols={3} className="my-masonry-grid"
               columnClassName="my-masonry-grid_column">
        {props.articlesList.map(article =>
          <NewsCard key={article.url} article={article}/>
        )}
      </Masonry>
      <Loading loading={props.loading}/>
    </div>
  )
}

function NewsSection(props){
  const [loading, setLoading] = useState(true)
  const [articlesList, setarticlesList] = useState([])
  let tag = props.tag || 'latest'
  const numArticles = props.numArticles || 9

  useEffect(() => {
    setLoading(true);
    axios.get('/api/articles', {
        params: {
          tag: tag,
          offset: 0,
          limit: numArticles
        }
      })
      .then(response => {
        let newArticles = response.data
        setarticlesList(newArticles)
        setLoading(false)
      });
  }, [tag]);

  return <NewsCardDeck 
    articlesList={articlesList}
    loading={loading}
    sectionName={tag}
  />
}

export default NewsSection;