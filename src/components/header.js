import React from "react";

function Header(props) {
  const buttonchange = () =>{
    props.onButton();
  }
  
  return (
<nav className="navbar sticky-top navbar-expand-lg navbar-light news-header">
  <div className="row flex-nowrap justify-content align-items-center py-3">
  <div className="col-4 pt-1">
     <a className="text-muted" href="#">
        <img src="../../logo192.png" width="30" height="30" alt="" />
       </a>
         </div>
        <div className="col-4 text-center title_navbar-center nav_text_title">
          <a className="navbar-title " href="/"> NewsX</a>
        </div>
        <div className="col-4 d-flex justify-content-end align-items-center title_navbar-right">
           <button className="btn btn-sm btn-outline-secondary" onClick={buttonchange}>
             Dark mode
           </button>
         </div>
  </div>
</nav>
  );
}

export default Header;