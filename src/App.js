import React, { useEffect } from "react";
import NewsSection from "./components/newsDeck";
import Header from "./components/header";
import {TinyButton as ScrollUpButton} from "react-scroll-up-button";
import {
  BrowserRouter as Router,
  Switch,
  Route,
  useParams,
  useLocation,
} from "react-router-dom";
import "./App.css";

function ScrollToTop() {
  const { pathname } = useLocation();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  return null;
}

function Home() {
  return (
    <>
      <NewsSection tag="latest" />
      <NewsSection tag="markets" />
      <NewsSection tag="economy" />
      <NewsSection tag="companies" />
    </>
  );
}

function TagPage() {
  let { tag } = useParams();
  if (tag == null) {
    return <h2>Please select a tag</h2>;
  }
  return (
    <NewsSection key={tag} tag={tag} numArticles={20} infiniteScroll={true} />
  );
}


function App() {
  return (
    <Router>
      <ScrollToTop />
      <div className="container">
        <Header />

        <Switch>
          <Route exact path="/">
            <Home />
          </Route>
          <Route path="/tag/:tag">
            <TagPage />
          </Route>
        </Switch>
        <ScrollUpButton/>
      </div>
    </Router>
  );
}

export default App;
