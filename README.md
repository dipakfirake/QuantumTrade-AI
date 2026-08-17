<div align="center">
  <h1>🌌 QuantumTrade AI</h1>
  <p><strong>Institutional-Grade Algorithmic Market Screener & ML Signal Predictor</strong></p>
</div>

<br />

## 🚀 Overview
**QuantumTrade AI** is a real-time, high-performance stock market screening and analysis platform designed for the National Stock Exchange (NSE). It autonomously scans over 2,500 listed equities, filters them based on dynamic price and liquidity thresholds, and leverages a Machine Learning engine (XGBoost) to predict the validity of moving average crossover signals.

Designed to emulate institutional trading dashboards, it features an asynchronous data pipeline, simulated market depth fallbacks, and a stunning Glassmorphism UI built on Streamlit.

---

## ⚡ Key Features

- **🔴 Live Market Screening:** Continuously scans all NSE equities using the Yahoo Finance API, applying custom ₹30–₹500 price filters.
- **💧 Liquidity Threshold Engine:** Evaluates top-level order book depth (simulated mathematically from real tick volume to bypass paid API requirements).
- **📈 SMMA Crossover Detection:** Asynchronously fetches 5-minute Intraday OHLCV data to detect real-time crossovers between 20-period and 120-period Smoothed Moving Averages.
- **🤖 Machine Learning Prediction:** Uses an XGBoost Classifier trained on historical order book imbalances, ETQ (Execution Trade Quantity) acceleration, and volume metrics to predict if a crossover signal should be executed or ignored.
- **📊 Real-time Trade & P&L Tracking:** Automatically logs simulated entries and exits, calculates P&L, and visualizes historical performance in real-time.
- **🎨 Premium UI/UX:** Built with a fully custom CSS implementation bringing Dark Mode Glassmorphism to Streamlit for a highly modern, professional aesthetic.

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| **Core Framework** | Python 3.11, Streamlit |
| **Machine Learning** | XGBoost, Scikit-Learn, Pandas, NumPy |
| **Data Providers** | Yahoo Finance (`yfinance`), Requests (NSE Web Scraping) |
| **Concurrency** | `concurrent.futures.ThreadPoolExecutor`, `asyncio` |
| **Styling** | Vanilla CSS (Injected), HTML5 |

---

## 🏗️ System Architecture

1. **Data Pipeline (`data_provider/`)**: Batches 2,500+ symbols and retrieves real-time Last Traded Prices (LTP).
2. **Screener (`screener/`)**: Applies the price range filter and liquidity depth requirements.
3. **Indicator Engine (`indicators/`)**: Calculates SMMA(20) and SMMA(120) on 5-minute ticks.
4. **ML Predictor (`ml_model/`)**: Extracts real-time features (Bid-Ask imbalance, LTQ surges) and runs XGBoost inference.
5. **Dashboard (`dashboard/`)**: The frontend UI that auto-refreshes seamlessly every 60 seconds without disrupting the user experience.

---

## ⚙️ How to Run Locally

### 1. Clone the Repository
```bash
git clone https://github.com/dipakfirake/QuantumTrade-AI.git
cd QuantumTrade-AI
```

### 2. Install Dependencies
Make sure you have Python 3.9+ installed.
```bash
pip install -r requirements.txt
```

### 3. Start the Application
```bash
python -m streamlit run app.py
```
*The application will automatically open in your default browser at `http://localhost:8501`.*

---

## 📉 Trading Logic
- **Buy Signal (🟢):** Triggered when the Short SMMA(20) crosses **above** the Long SMMA(120). The ML model evaluates conviction based on order book volume.
- **Sell Signal (🔴):** Triggered when the Short SMMA(20) crosses **below** the Long SMMA(120). 
- **Exit Logic:** Trades are closed when an opposing crossover occurs, automatically logging the P&L in the Trade History tab.

---

<div align="center">
  <p>Built as an Advanced Technical Assessment for SSG Infotech.</p>
</div>
