import feedparser, requests, pandas as pd
class EdgarClient:
    def __init__(self):
        pass
    def get_form4_by_cik(self, cik, count=80):
        url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=4&owner=only&count={count}&output=atom"
        d = feedparser.parse(url)
        rows = []
        for e in d.entries:
            rows.append({"title": e.get("title"), "link": e.get("link"), "published": e.get("published")})
        return pd.DataFrame(rows)
    def search_company_forms(self, text, count=80):
        # lightweight fallback (returns empty df if not implemented)
        return pd.DataFrame()