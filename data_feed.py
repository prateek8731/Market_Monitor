import os, requests, pandas as pd, time
from datetime import datetime, timedelta
import feedparser

class DataFeed:
    def __init__(self, api_keys=None):
        if api_keys is None:
            api_keys = {}
        self.finnhub = api_keys.get("FINNHUB", os.getenv("FINNHUB_API_KEY",""))
        self.alphav = api_keys.get("ALPHAV", os.getenv("ALPHAV_API_KEY",""))

    def fetch_rss_feeds(self):
        feeds = {
            "Reuters Business":"http://feeds.reuters.com/reuters/businessNews",
            "CNBC Tech":"https://www.cnbc.com/id/19854910/device/rss/rss.html",
            "The Verge":"https://www.theverge.com/rss/index.xml",
            "CoinDesk":"https://www.coindesk.com/arc/outboundfeeds/rss/"
        }
        rows = []
        for name,url in feeds.items():
            try:
                d = feedparser.parse(url)
                for e in d.entries[:200]:
                    rows.append({"source":name,"title":e.get("title"),"link":e.get("link"),"published":e.get("published")})
            except Exception:
                continue
        df = pd.DataFrame(rows)
        if not df.empty:
            try:
                df['published'] = pd.to_datetime(df['published'], errors='coerce')
            except Exception:
                pass
        return df

    def get_historical(self, ticker, provider="AlphaVantage", days=365):
        ticker = ticker.strip().upper() if ticker else ""
        if not ticker:
            return pd.DataFrame()
        if provider.lower().startswith("alpha") and self.alphav:
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={ticker}&outputsize=full&apikey={self.alphav}"
            r = requests.get(url, timeout=20)
            data = r.json().get("Time Series (Daily)",{})
            rows = []
            for dt,vals in data.items():
                rows.append({"date":pd.to_datetime(dt),"open":float(vals["1. open"]),"high":float(vals["2. high"]),"low":float(vals["3. low"]),"close":float(vals["4. close"]),"volume":int(vals["6. volume"])})
            df = pd.DataFrame(rows).sort_values("date")
            cutoff = pd.Timestamp.utcnow() - pd.Timedelta(days=days)
            return df[df.date>=cutoff]
        # fallback: try Finnhub API
        if provider.lower().startswith("finn") and self.finnhub:
            to_ts = int(datetime.utcnow().timestamp())
            frm_ts = int((datetime.utcnow() - timedelta(days=days)).timestamp())
            url = f"https://finnhub.io/api/v1/stock/candle?symbol={ticker}&resolution=D&from={frm_ts}&to={to_ts}&token={self.finnhub}"
            r = requests.get(url, timeout=20)
            data = r.json()
            if data.get("s") != "ok":
                return pd.DataFrame()
            df = pd.DataFrame({"date":pd.to_datetime(data["t"],unit='s'),"open":data["o"],"high":data["h"],"low":data["l"],"close":data["c"],"volume":data["v"]})
            return df
        return pd.DataFrame()