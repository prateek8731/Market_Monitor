# Market Monitor Phase 2 - Streamlit

This project upgrades the Phase 1 dashboard with **real-time data**, **backtesting**, **model comparisons**, and **paper trading**.
It is intentionally modular and includes optional heavy libraries for advanced modelling.

## Features added in Phase 2
- DataFeed abstraction supporting **Finnhub**, **AlphaVantage**, and **Polygon** (requires API keys set as env vars or provided in app).
- New "New to Investment" module wired to live quotes and the RandomForest baseline.
- Simple backtesting engine and a sample SMA strategy to simulate Buy/Hold/Sell rules.
- Model wrappers for RandomForest (built-in) and an LSTM wrapper (requires TensorFlow).
- Portfolio manager using SQLite for paper trading: place buy/sell orders and track P/L.
- Clear fallbacks and instructions for optional upgrades (Darts, NeuralProphet, vectorbt).

## Setup
1. Obtain API keys (recommended):
   - Finnhub: https://finnhub.io/
   - Alpha Vantage: https://www.alphavantage.co/
   - Polygon.io (optional)

2. Set environment variables (Linux/macOS):
```bash
export FINNHUB_API_KEY="your_key_here"
export ALPHAV_API_KEY="your_key_here"
export POLYGON_API_KEY="your_key_here"
```

3. Install core requirements:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

4. Optional (if you want LSTM / Darts / NeuralProphet):
```bash
# TensorFlow (heavy)
pip install tensorflow==2.14.0
# Darts / NeuralProphet / vectorbt - follow their docs for installs & CUDA optional support
```

5. Run the app:
```bash
streamlit run app.py
```

## Notes & Limitations
- Real-time streaming WebSockets require background workers and long-lived processes—this app uses polling for simplicity (Finnhub supports WebSocket, example code in data_feed.py).
- LSTM / Darts / NeuralProphet are optional and must be installed separately.
- The backtester provided is a simple, educational engine. For production-grade backtesting use `vectorbt` or `backtrader`.
- This is an **educational tool**, not financial advice. Test thoroughly before using any automated signals with real money.

## Next steps (recommended)
- Add robust rate-limit handling and caching for APIs.
- Add slippage and commission modeling to backtests.
- Add scheduled tasks for model retraining and live signal production (e.g., Cloud Run + Pub/Sub or Cron + GitHub Actions).
- Add authentication and per-user portfolio storage (switch SQLite -> Postgres).

## Start Early section

This new section surfaces **publicly disclosed** early signals: public insider transactions (Form 4), news buzz, and a quick ML prediction. It **does not** provide non-public insider information and should be used for monitoring public filings and signals only.
