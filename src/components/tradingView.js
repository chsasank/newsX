import React from "react";

export default class HomePageTVWidget extends React.PureComponent {
  constructor(props) {
    super(props);
    this._ref = React.createRef();
  }
  render() {
    return (
      <div class="tradingview-widget-container" ref={this._ref}>
        <div class="tradingview-widget-container__widget"></div>
      </div>
    );
  }
  componentDidMount() {
    const script = document.createElement("script");
    script.src =
      "https://s3.tradingview.com/external-embedding/embed-widget-tickers.js";
    script.async = true;
    script.innerHTML = JSON.stringify({
      "symbols": [
        {
          "description": "NIFTY50",
          "proName": "NSE:NIFTY"
        },
        {
          "description": "SENSEX",
          "proName": "BSE:SENSEX"
        }
      ],
      "colorTheme": "light",
      "isTransparent": true,
      "locale": "in"
    })
    this._ref.current.appendChild(script);
  }
}
