import React, { useState,useEffect } from "react";
import NewsSection from "./components/newsSection";
import Home from "./components/newsHome";
import Header from "./components/header";
import { TinyButton as ScrollUpButton } from "react-scroll-up-button";
import {
  BrowserRouter as Router,
  Switch,
  Route,
  useParams,
  useLocation,
} from "react-router-dom";


import "./App.css";
import"./index.css";

function ScrollToTop() {
  const { pathname } = useLocation();


  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  return null;
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
  const [isdark, setIsDark] = useState(getDarkMode);
  
  const toggleDarkMode = () => setIsDark(!isdark);
  useEffect(() => {
    localStorage.setItem("dark", JSON.stringify(isdark));
  }, [isdark]);

  function getDarkMode() {
    const savedmode = JSON.parse(localStorage.getItem("dark"));
    console.log(savedmode)
    return savedmode || false;
  }
  return (
  <div className='App' data-theme={isdark ? "dark" : "light"}>
    <Router>
    <ScrollToTop />
      <div className="container">
        <Header onButton={toggleDarkMode}/>
        <Switch>
          <Route exact path="/">
            <Home />
          </Route>
          <Route path="/tag/:tag">
            <TagPage />
          </Route>
        </Switch>
        <ScrollUpButton />
      </div>
    </Router>
  </div>
  );
}

export default App;