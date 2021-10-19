import React from "react";

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



export default Loading;