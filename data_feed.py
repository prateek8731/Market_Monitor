import os, time, requests, pandas as pd, numpy as np
from datetime import datetime, timedelta
class DataFeed:
    """
    Abstracts multiple data providers. By default, uses Finnhub for quotes & historical (requires FINNHUB_API_KEY env var).
    Falls back to AlphaVantage for historical (set ALPHAV_API_KEY).
    """
    def __init__(self, api_keys=None):
        if api_keys is None:
            api_keys = {}
        self.finnhub = api_keys.get("FINNHUB", os.getenv("FINNHUB_API_KEY", ""))
        self.alphav = api_keys.get("ALPHAV", os.getenv("ALPHAV_API_KEY", ""))
        self.polygon = api_keys.get("POLYGON", os.getenv("POLYGON_API_KEY", ""))

    def get_quote(self, ticker, provider="Finnhub"):
        ticker = ticker.strip().upper()
        if provider.lower().startswith("finn"):
            if not self.finnhub:
                return {"error":"FINNHUB_API_KEY not set"}
            url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={self.finnhub}"
            r = requests.get(url, timeout=10)
            return r.json()
        elif provider.lower().startswith("alpha"):
            if not self.alphav:
                return {"error":"ALPHAV_API_KEY not set"}
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={self.alphav}"
            r = requests.get(url, timeout=10)
            data = r.json().get("Global Quote", {})
            # normalize
            return {"c": float(data.get("05. price", 0)), "h": float(data.get("03. high", 0)), "l": float(data.get("04. low", 0)), "o": float(data.get("02. open", 0)), "t": int(time.time())}
        elif provider.lower().startswith("poly"):
            if not self.polygon:
                return {"error":"POLYGON_API_KEY not set"}
            url = f"https://api.polygon.io/v1/last/stocks/{ticker}?apiKey={self.polygon}"
            r = requests.get(url, timeout=10)
            return r.json()
        else:
            return {"error":"unsupported provider"}

    def get_historical(self, ticker, provider="Finnhub", days=365):
        ticker = ticker.strip().upper()
        if provider.lower().startswith("finn"):
            if not self.finnhub:
                return pd.DataFrame()
            to_ts = int(datetime.utcnow().timestamp())
            frm_ts = int((datetime.utcnow() - timedelta(days=days)).timestamp())
            url = f"https://finnhub.io/api/v1/stock/candle?symbol={ticker}&resolution=D&from={frm_ts}&to={to_ts}&token={self.finnhub}"
            r = requests.get(url, timeout=20)
            data = r.json()
            if data.get("s") != "ok":
                return pd.DataFrame()
            df = pd.DataFrame({"date": pd.to_datetime(data["t"], unit='s'), "open": data["o"], "high": data["h"], "low": data["l"], "close": data["c"], "volume": data["v"]})
            return df
        elif provider.lower().startswith("alpha"):
            if not self.alphav:
                return pd.DataFrame()
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={ticker}&outputsize=full&apikey={self.alphav}"
            r = requests.get(url, timeout=20)
            data = r.json().get("Time Series (Daily)", {})
            if not data:
                return pd.DataFrame()
            rows = []
            for dt, vals in data.items():
                rows.append({"date": pd.to_datetime(dt), "open": float(vals["1. open"]), "high": float(vals["2. high"]), "low": float(vals["3. low"]), "close": float(vals["4. close"]), "volume": int(vals["6. volume"])})
            df = pd.DataFrame(rows).sort_values("date")
            cutoff = pd.Timestamp.utcnow() - pd.Timedelta(days=days)
            return df[df.date >= cutoff]
        else:
            return pd.DataFrame()


import feedparser, pandas as pd
# --- Insider trades via Finnhub public endpoint (if FINNHUB key available)
def get_insider_trades(self, ticker):
    """
    Returns recent insider transactions for ticker using Finnhub (requires FINNHUB_API_KEY).
    Falls back to an empty list with an explanatory message if API key is missing.
    """
    if not getattr(self, "finnhub", None):
        return {"error":"FINNHUB_API_KEY not set"}
    url = f"https://finnhub.io/api/v1/stock/insider-transactions?symbol={ticker}&token={self.finnhub}"
    try:
        r = requests.get(url, timeout=15)
        data = r.json()
        # Finnhub returns {'data': [...]} typically
        if isinstance(data, dict) and data.get("data") is not None:
            return data["data"]
        # else try to return the data as-is
        return data
    except Exception as e:
        return {"error": str(e)}

def fetch_news(self):
    """
    Fetch a set of RSS headlines from common tech/finance sources and return a DataFrame.
    """
    feeds = {
        "Reuters Business": "http://feeds.reuters.com/reuters/businessNews",
        "CNBC Tech": "https://www.cnbc.com/id/19854910/device/rss/rss.html",
        "The Verge": "https://www.theverge.com/rss/index.xml",
        "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "Yahoo Finance": "https://finance.yahoo.com/news/rssindex"
    }
    rows = []
    for src, url in feeds.items():
        try:
            d = feedparser.parse(url)
            for e in d.entries[:80]:
                rows.append({"source": src, "title": e.get("title",""), "link": e.get("link",""), "published": e.get("published","")})
        except Exception:
            continue
    return pd.DataFrame(rows)
