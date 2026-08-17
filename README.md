# SSG Infotech — AI/ML Stock Market Screening & Analysis System

A Python-based real-time stock market screening and analysis application that:
- Scans all NSE-listed stocks filtered by price range (₹30–₹500) and liquidity (Bid/Ask Qty > 10 Lakh)
- Calculates and displays SMMA(20) and SMMA(120) technical indicators
- Tracks Exchange Traded Quantity (ETQ) over 5, 20, and 60 minute windows
- Displays average LTP over 20 and 60 minute windows
- Shows real-time market depth (Bid/Ask price and quantity)
- Uses AI/ML (XGBoost) to predict whether SMMA crossover signals will be profitable
- Provides a live auto-refreshing dashboard with trading signals, P&L tracking, and ML explanations

---

## Quick Start

### Prerequisites
- Python 3.9 or higher
- Internet connection (for fetching market data)

### Installation

```bash
# Navigate to the project directory
cd "d:\Company Assessments\SSG Infotech"

# Install dependencies
pip install -r requirements.txt
```

### Train the ML Model (Optional but Recommended)

```bash
# Train with 50 symbols (takes ~5-10 minutes)
python scripts/train_model.py --symbols 50

# Or with fewer symbols for a quick test
python scripts/train_model.py --symbols 10
```

The model will be saved to `ml_model/model.pkl`. If not trained, the system falls back to a rule-based prediction engine.

### Run the Dashboard

```bash
streamlit run app.py
```

The dashboard will open at `http://localhost:8501` with auto-refresh.

---

## Build Executable (.exe)

```bash
python scripts/build_exe.py
```

The executable will be created at `dist/StockScreener/StockScreener.exe`.

---

## Project Structure

```
├── app.py                      # Streamlit dashboard entry point
├── config.py                   # Configuration constants
├── run_app.py                  # PyInstaller wrapper
├── requirements.txt            # Dependencies
│
├── data_provider/              # Market data abstraction layer
│   ├── base.py                 # Abstract DataProvider interface
│   ├── nse_provider.py         # yfinance + NSE implementation
│   └── cache.py                # Tick cache & time-windowed aggregations
│
├── screener/                   # Stock screening logic
│   ├── stock_screener.py       # Price & liquidity filters
│   └── nse_symbols.py          # NSE symbol list management
│
├── indicators/                 # Technical indicators
│   ├── smma.py                 # SMMA, RSI, ATR calculators
│   └── crossover.py            # SMMA crossover detection
│
├── trading/                    # Trade management
│   ├── signal_tracker.py       # Open position & P&L tracking
│   └── trade_log.py            # Persistent CSV trade history
│
├── ml_model/                   # AI/ML prediction engine
│   ├── feature_engineer.py     # 14 quantitative features
│   ├── trainer.py              # XGBoost training pipeline
│   └── predictor.py            # Live inference + explanations
│
├── dashboard/                  # UI components
│   ├── components.py           # Streamlit widgets
│   └── styles.py               # Custom CSS (dark theme)
│
├── scripts/                    # Build & training scripts
│   ├── build_exe.py            # PyInstaller build
│   └── train_model.py          # Standalone model training
│
└── data/                       # Runtime data (auto-generated)
    ├── nse_symbols.csv          # Cached symbol list
    ├── historical_crossovers.csv # ML training data
    └── trade_history.csv        # Trade log
```

## Technical Details

### SMMA (Smoothed Moving Average)
- `SMMA[0..N-1] = SMA of first N values`
- `SMMA[i] = (SMMA[i-1] × (N-1) + Close[i]) / N`
- Two periods: SMMA(20) [fast] and SMMA(120) [slow]

### Crossover Logic
- **Buy Signal**: SMMA(20) crosses above SMMA(120)
- **Sell Signal**: SMMA(20) crosses below SMMA(120)
- **Buy P&L**: Exit LTP − Entry LTP
- **Sell P&L**: Entry LTP − Exit LTP

### ML Features (14 total)
| Feature | Description |
|---------|-------------|
| ltq_ratio_2m_5m | Avg LTQ (2 min) / Avg LTQ (5 min) |
| ltq_ratio_5m_20m | Avg LTQ (5 min) / Avg LTQ (20 min) |
| etq_5m, etq_20m, etq_60m | Total ETQ in time windows |
| etq_acceleration | ETQ(5m) / (ETQ(20m)/4) |
| bid_ask_imbalance | (Bid - Ask) / (Bid + Ask) |
| spread_pct | (Ask - Bid) / LTP × 100 |
| smma_gap_pct | (SMMA20 - SMMA120) / SMMA120 × 100 |
| price_vs_avg20m | LTP / Avg LTP (20m) |
| price_vs_avg60m | LTP / Avg LTP (60m) |
| volume_surge | Current vol / 20-bar avg vol |
| rsi_14 | Relative Strength Index |
| atr_pct | ATR(14) / LTP × 100 |

### ML Algorithm
- **XGBoost** (Gradient Boosted Decision Trees)
- Time-based train/test split (no future leakage)
- Rule-based fallback when model is not trained

---

## Security Note
All trading credentials, API keys, and passwords have been removed. This application uses only free, public data sources.
