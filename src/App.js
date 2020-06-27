import React, {useEffect} from 'react';
import './App.css';
import NewsSection from './components/newsDeck'
import Header from './components/header'
import {
  BrowserRouter as Router,
  Switch,
  Route,
  Link,
  useParams,
  useLocation,
} from "react-router-dom";


function ScrollToTop() {
  const { pathname } = useLocation();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  return null;
}


function Home() {
  return <>
    <NewsSection tag="latest"/>
    <NewsSection tag="markets"/>
    <NewsSection tag="economy"/>
  </>
}

function TagPage() {
  let { tag } = useParams();
  if (tag == null){
    return <h2>Please select a tag</h2>
  }
  return <NewsSection tag={tag} numArticles={20}/>
}


function App() {
  return (
    <Router>
      <ScrollToTop />
      <div className="container">
        <Header/>

        <Switch>
          <Route exact path="/">
            <Home/>
          </Route>
          <Route path="/tag/:tag">
            <TagPage/>
          </Route>
        </Switch>
      </div>
    </Router>
  );
}

export default App;
