<div align="center">
  <h1>🌌 QuantumTrade AI</h1>
  <p><strong>Institutional-Grade Algorithmic Market Screener & ML Crossover Engine</strong></p>
  <p>Powered by Fyers API v3 WebSocket & XGBoost Machine Learning</p>
</div>

<br />

## 🚀 Overview
**QuantumTrade AI** is a real-time, institutional-grade stock market screening and quantitative analysis platform designed for the National Stock Exchange (NSE). It connects directly to the **Fyers API v3 WebSocket** to process live tick-by-tick data, 5-level market depth, and Last Traded Quantity (LTQ) surges.

The system filters the NSE universe dynamically (LTP ₹30–₹500, Bid/Ask Quantity > 10 Lakhs), computes rolling 20-period and 120-period Smoothed Moving Averages (SMMA), and uses a trained **XGBoost Classifier** to evaluate whether a crossover signal should be **ACCEPTED** or **AVOIDED** based on order book microstructure.

---

## ⚡ Key Features

- **🔴 Live Fyers WebSocket Stream:** Direct real-time tick streaming and 5-level market depth order book updates.
- **💧 Strict Liquidity Filter:** Enforces Bid Quantity > 10,00,000 and Ask Quantity > 10,00,000 to identify institutional liquidity.
- **📈 SMMA Crossover Detection:** Computes real-time SMMA(20) and SMMA(120) crossovers on intraday candles.
- **🤖 XGBoost ML Signal Filter:** Evaluates 14 quantitative features (LTQ 2m vs 5m ratio, ETQ acceleration, Bid-Ask imbalance, RSI, ATR) to predict profitable vs losing crossovers.
- **📊 Real-Time Trade & P&L Tracking:** Automatically tracks open positions, calculates exit P&L, and persists completed trades to CSV.
- **🎨 Glassmorphism Institutional UI:** Built with custom dark-mode CSS and Streamlit with auto-refresh and sub-second rendering.

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| **Broker Integration** | Fyers API v3 SDK (`fyers-apiv3`), FyersDataSocket (WebSocket) |
| **Machine Learning** | XGBoost Classifier, Scikit-Learn, SHAP Explainability |
| **Core & UI** | Python 3.11, Streamlit, Plotly, Pandas, NumPy |
| **Concurrency** | Asyncio, ThreadPoolExecutor, In-Memory Tick Buffer |
| **Styling** | Custom Dark Glassmorphism CSS, HTML5 |

---

## 🏗️ System Architecture

```
[ NSE Live Feed ] ──> [ Fyers WebSocket ] ──> [ In-Memory Tick Cache ]
                                                       │
                           ┌───────────────────────────┴───────────────────────────┐
                           ▼                                                       ▼
                [ SMMA 20/120 Engine ]                                    [ 5-Level Depth Filter ]
                           │                                                       │
                           └───────────────────────────┬───────────────────────────┘
                                                       ▼
                                          [ SMMA Crossover Detected ]
                                                       │
                                                       ▼
                                         [ XGBoost ML Inference (<1ms) ]
                                          ➔ ACCEPT / AVOID + Confidence %
                                                       │
                                                       ▼
                                         [ Live Trade & P&L Tracker ]
                                                       │
                                                       ▼
                                          [ Streamlit Live Dashboard ]
```

---

## ⚙️ How to Setup & Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Connect Fyers Account (One-Time Setup)
1. Create an App on [myapi.fyers.in](https://myapi.fyers.in/) (App Type: `Web App`, Redirect URI: `https://trade.fyers.in/api-login/redirect-uri/index.html`).
2. Run the authentication script:
```bash
python scripts/fyers_login.py
```
*Enter your App ID and Secret Key, log in via your browser, and paste the redirected auth code.*

### 3. Launch Dashboard
```bash
python -m streamlit run app.py
```
*The dashboard will launch at `http://localhost:8501` with live Fyers streaming data.*

---

## 📉 Trading & ML Evaluation Logic

- **Buy Signal (🟢):** SMMA(20) crosses **above** SMMA(120).
- **Sell Signal (🔴):** SMMA(20) crosses **below** SMMA(120).
- **ML Filter:** Evaluates order flow conviction. High LTQ surge + favorable Bid/Ask imbalance = **ACCEPT**; Divergent order flow = **AVOID**.
- **Exit Logic:** Position is closed on reverse crossover. $\text{P&L} = \text{Exit LTP} - \text{Entry LTP}$.

---

<div align="center">
  <p>Built for SSG Infotech Advanced Technical Assessment.</p>
</div>
