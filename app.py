import streamlit as st
from data_feed import DataFeed
from models.random_forest_model import RFModel
from backtest.simulator import Backtester
from portfolio.portfolio_manager import PortfolioManager
import pandas as pd
import numpy as np
import os
st.set_page_config(page_title="Market Monitor Phase 2", layout="wide")

API_KEYS = {
    "FINNHUB": os.getenv("FINNHUB_API_KEY", ""),
    "ALPHAV": os.getenv("ALPHAV_API_KEY", ""),
    "POLYGON": os.getenv("POLYGON_API_KEY", "")
}

st.title("Market Monitor — Phase 2 (Live Data • Backtest • Models • Portfolio)")

# Initialize services
df = DataFeed(api_keys=API_KEYS)
pm = PortfolioManager(db_path="portfolio.db")

tabs = st.tabs(["Live Data", "New to Investment (Live Signals)", "Backtest", "Models Comparison", "Portfolio & Paper trading"])

with tabs[0]:
    st.header("Live Market Data")
    ticker = st.text_input("Ticker (US/TSX):", value="AAPL").upper()
    provider = st.selectbox("Data Provider (live)", ["Finnhub", "AlphaVantage (polling)", "Polygon"], index=0)
    if st.button("Fetch Quote"):
        quote = df.get_quote(ticker, provider=provider)
        st.json(quote)
    st.markdown("Realtime WebSocket streaming requires background workers — here we provide polling endpoints and example code in `data_feed.py`.")

with tabs[1]:
    st.header("New to Investment — Live ML Signals")
    ticker2 = st.text_input("Ticker for signal:", value="AAPL", key="t2").upper()
    horizon = st.selectbox("Prediction horizon (days)", [1,2,3,5,7], index=1)
    lookback = st.slider("Lookback days for training", 60, 720, 180, step=30)
    buy_thresh = st.number_input("Buy threshold (%)", value=2.0, step=0.5)
    sell_thresh = st.number_input("Sell threshold (%)", value=-2.0, step=0.5)
    if st.button("Compute Signal"):
        hist = df.get_historical(ticker2, provider="Finnhub", days=lookback+horizon)
        if hist is None or hist.empty:
            st.error("Historical data unavailable. Check API key & ticker.")
        else:
            # baseline RF model
            model = RFModel()
            signal_res = model.run_full_pipeline(hist, horizon=horizon)
            st.subheader("Prediction summary (baseline RF)")
            st.write(signal_res["metrics"])
            st.metric("Predicted % change", f'{signal_res["pred_pct"]:.2f}%')
            recommendation = "HOLD"
            if signal_res["pred_pct"] >= buy_thresh:
                recommendation = "BUY"
            elif signal_res["pred_pct"] <= sell_thresh:
                recommendation = "SELL"
            st.markdown(f"## Recommendation: **{recommendation}**")
            st.line_chart(signal_res["recent_series"].set_index("date")["close"])

with tabs[2]:
    st.header("Backtest")
    bt_ticker = st.text_input("Backtest ticker", value="AAPL", key="bt")
    start = st.date_input("Start date", value=pd.to_datetime("2021-01-01"))
    end = st.date_input("End date", value=pd.to_datetime("2024-12-31"))
    initial_capital = st.number_input("Initial capital ($)", value=100000.0, step=1000.0)
    if st.button("Run Backtest"):
        hist = df.get_historical(bt_ticker, provider="AlphaVantage", days=2000)  # fallback to AV for history
        if hist is None or hist.empty:
            st.error("Historical data unavailable. Check API key & limits.")
        else:
            backtester = Backtester(initial_capital=initial_capital)
            res = backtester.run_signals(hist, strategy_simple_moving_average)
            st.write(res["summary"])
            st.line_chart(pd.DataFrame({"equity": res["equity_curve"]}))

with tabs[3]:
    st.header("Models Comparison (Baseline + Advanced)")
    st.markdown("This page will train multiple models and compare metrics. LSTM / Darts / NeuralProphet are optional — the code handles missing packages gracefully.")
    ticker3 = st.text_input("Ticker for models", value="AAPL", key="m1")
    if st.button("Train & Compare Models"):
        hist = df.get_historical(ticker3, provider="AlphaVantage", days=500)
        if hist is None or hist.empty:
            st.error("Historical data unavailable.")
        else:
            st.info("Training RandomForest (baseline). Advanced models will be attempted if libraries are installed.")
            rf = RFModel()
            rf_res = rf.run_full_pipeline(hist)
            st.write("RandomForest metrics:", rf_res["metrics"])
            # placeholders for advanced models
            st.write("LSTM and other advanced models will run if TensorFlow/Darts/NeuralProphet are installed. Check README for install instructions.")

with tabs[4]:
    st.header("Portfolio & Paper Trading")
    st.markdown("Your paper trading balance (stored locally in SQLite).")
    bal = pm.get_balance()
    st.metric("Paper Trading Balance", f"${bal:,.2f}")
    col1, col2 = st.columns(2)
    with col1:
        sym = st.text_input("Buy ticker", value="AAPL", key="buy_sym")
        qty = st.number_input("Quantity", value=1, step=1)
        if st.button("Place Buy Order"):
            quote = df.get_quote(sym)
            price = quote.get("c") or quote.get("price") or None
            if price is None:
                st.error("Price unavailable. Try again.")
            else:
                pm.place_order(symbol=sym, side="BUY", qty=qty, price=price)
                st.success(f"Bought {qty} {sym} @ {price}")
    with col2:
        sym2 = st.text_input("Sell ticker", value="AAPL", key="sell_sym")
        qty2 = st.number_input("Quantity to sell", value=1, step=1)
        if st.button("Place Sell Order"):
            quote = df.get_quote(sym2)
            price = quote.get("c") or quote.get("price") or None
            if price is None:
                st.error("Price unavailable. Try again.")
            else:
                pm.place_order(symbol=sym2, side="SELL", qty=qty2, price=price)
                st.success(f"Sold {qty2} {sym2} @ {price}")
    st.subheader("Open Positions")
    st.dataframe(pm.list_positions())
    st.subheader("Trade History")
    st.dataframe(pm.list_trades())


# ----------------------------
# Start Early — Public Insider Signals & Early indicators
# ----------------------------
st.header("🚀 Start Early — Public Insider Signals & Early Indicators")
st.markdown("""**Important legal note:** This section only surfaces **publicly disclosed** information (e.g., Form 4 filings, press releases, job postings, public news). I cannot and will not help obtain or act on non‑public insider information. Use this section to monitor *public* early signals only.""")

se_ticker = st.text_input("Ticker to scan for early signals (public data):", value="AAPL", key="start_early_ticker").upper()
if st.button("Scan Start-Early Signals"):
    # 1) Insider trades (public filings) via Finnhub (if available)
    insiders = df.get_insider_trades(se_ticker)
    if isinstance(insiders, dict) and insiders.get("error"):
        st.warning(f"Insider data unavailable: {insiders.get('error')}")
        insiders_df = None
    else:
        try:
            import pandas as _pd
            insiders_df = _pd.DataFrame(insiders)
            if insiders_df.empty:
                st.info("No recent insider transactions found (public).")
            else:
                st.subheader("Recent Public Insider Transactions (Form 4 / Filings)")
                st.dataframe(insiders_df.head(50))
        except Exception as e:
            st.error(f"Error parsing insider data: {e}")
            insiders_df = None

    # 2) News buzz (reuse simple RSS fetcher if available)
    news_df = None
    try:
        news_df = df.fetch_news()
    except Exception:
        pass

    # compute simple signals
    insider_buy_score = 0
    insider_sell_score = 0
    if insiders_df is not None and not insiders_df.empty:
        # heuristic: count 'Buy' vs 'Sell' transactions (different providers use different fields)
        for col in insiders_df.columns:
            pass
        # try common keys
        if "transactionType" in insiders_df.columns:
            insider_buy_score = int((insiders_df["transactionType"].str.lower() == "buy").sum())
            insider_sell_score = int((insiders_df["transactionType"].str.lower() == "sell").sum())
        elif "transaction" in insiders_df.columns:
            insider_buy_score = int((insiders_df["transaction"].str.lower().str.contains("buy")).sum())
            insider_sell_score = int((insiders_df["transaction"].str.lower().str.contains("sell")).sum())
        else:
            # fallback: try 'change' or 'shares' direction if available
            if "change" in insiders_df.columns:
                insider_buy_score = int((insiders_df["change"].astype(float) > 0).sum())
                insider_sell_score = int((insiders_df["change"].astype(float) < 0).sum())

    news_buzz = 0
    if news_df is not None and not news_df.empty:
        # count keywords in recent headlines (72h)
        import pandas as _pd, numpy as _np, re as _re, datetime as _dt
        now = _pd.Timestamp.utcnow()
        if "published" in news_df.columns:
            try:
                news_df["published_dt"] = _pd.to_datetime(news_df["published"], errors="coerce")
                recent = news_df[news_df["published_dt"] >= now - _pd.Timedelta(hours=72)]
            except Exception:
                recent = news_df
        else:
            recent = news_df
        keywords = ["acquir","merger","buyback","insider","partnership","contract","earnings","surge","growth","breakthrough","approval","patent","launch","hiring","expansion","ai","chip","semiconductor"]
        cnt = 0
        for k in keywords:
            cnt += recent["title"].str.lower().str.count(k).fillna(0).sum() if "title" in recent.columns else 0
        news_buzz = int(cnt)

    # 3) Simple ML signal from RF baseline (quick predictive view)
    pred_pct = None
    try:
        from models.random_forest_model import RFModel
        hist = df.get_historical(se_ticker, provider="Finnhub", days=180)
        if hist is not None and not hist.empty:
            model = RFModel()
            res = model.run_full_pipeline(hist, horizon=3)
            pred_pct = res.get("pred_pct", None)
            st.metric("Model predicted % change (3d horizon)", f"{pred_pct:.2f}%" if pred_pct is not None else "N/A")
    except Exception as e:
        st.info("Prediction unavailable: " + str(e))

    # Combine heuristic score (weights adjustable)
    score = 0.0
    score += 2.0 * insider_buy_score
    score -= 1.0 * insider_sell_score
    score += 0.2 * news_buzz
    if pred_pct is not None:
        # scale predicted pct to score
        score += 0.5 * max(min(pred_pct, 20), -20)

    st.subheader("Start-Early Composite Score")
    st.write(f"Insider buy count: {insider_buy_score}, sell count: {insider_sell_score}, news buzz: {news_buzz}, model pred %: {pred_pct}")
    st.metric("Composite early-opportunity score", round(score,2))

    if score >= 10:
        st.success("Signal: **High** — public filings + buzz + model suggest early opportunity. (Public data only)")
    elif score >= 2:
        st.info("Signal: **Moderate** — watch closely; consider further due diligence.")
    else:
        st.warning("Signal: **Low** — no strong public early indicators found.")

