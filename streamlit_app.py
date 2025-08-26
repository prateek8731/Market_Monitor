import streamlit as st
from data_feed import DataFeed
from edgar import EdgarClient
from news_nlp import analyze_headlines, map_entities_to_ticker
from models.classifier_model import ClassifierModel
from tasks import send_webhook_alert, send_email_alert, send_sms_alert, retrain_and_save_model
import pandas as pd, os

st.set_page_config(page_title="Market Monitor Extended", layout="wide")
st.title("Market Monitor — Extended (EDGAR, NLP, Classifier, Alerts)")

API_KEYS = {"FINNHUB": os.getenv("FINNHUB_API_KEY",""), "ALPHAV": os.getenv("ALPHAV_API_KEY","")}
df = DataFeed(api_keys=API_KEYS)
edgar = EdgarClient()

st.header("Start Early — Advanced")
company = st.text_input("Company name or ticker (e.g., AAPL or Apple Inc.)")
cik = st.text_input("CIK (optional)")
if st.button("Scan Start-Early Signals"):
    st.info("Fetching EDGAR filings...")
    forms = edgar.get_form4_by_cik(cik) if cik else edgar.search_company_forms(company)
    st.dataframe(forms.head(50))
    st.info("Fetching headlines and analyzing...")
    news = df.fetch_rss_feeds()
    nlp = analyze_headlines(news)
    st.dataframe(nlp.head(50))
    st.info("Mapping entities to tickers...")
    mapping = map_entities_to_ticker(nlp, api_client=df)
    st.dataframe(mapping.head(50))
    st.info("Running classifier prediction...")
    primary = mapping['ticker'].iloc[0] if not mapping.empty and mapping['ticker'].notnull().any() else (company.upper() if company else "")
    hist = df.get_historical(primary, provider="Finnhub", days=365) if primary else pd.DataFrame()
    clf = ClassifierModel()
    res = clf.predict_from_signals(hist, forms_df=forms, headlines_df=nlp, horizon=3)
    st.metric("Start-Early probability", f"{res.get('prob_pos',0):.3f}")