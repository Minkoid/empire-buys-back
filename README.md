# ⚔️ The Empire Buys Back

*May the profits be with you.*

A Star Wars-themed Streamlit backtesting application for testing pullback-based trading strategies. Built for Snowy & Saunders Trading Consortium.

## 🎯 Purpose

This tool allows you to:
- Analyse historical price data for multiple ETFs (QQQ, SPY, DIA, etc.)
- Simulate a simple pullback-and-rebound strategy
- Understand historical risk, returns, drawdowns, and trade behaviour
- Rapidly tune parameters and iterate based on visual feedback

## 📈 Strategy Overview

*"Do or do not buy the dip. There is no try."* - Yoda, probably

### Entry Logic (When to Strike)
- Track the **all-time high (ATH)** price
- When price pulls back by **X%** from ATH, enter a long position

### Exit Logic (Choose Your Path)
- **ATH Recovery**: Exit when price returns to ATH
- **Percent Rebound**: Exit when price rebounds **Y%** from entry price

### Risk Management (Protect the Empire)
- If price drops **Z%** below entry, exit the trade (stop-loss)
- Only one open position at a time
- After a stop-loss, optionally remain in cash until a new ATH forms

## 🎯 Available Targets

| Ticker | Description |
|--------|-------------|
| **QQQ** | Nasdaq-100 (Tech-heavy) |
| **SPY** | S&P 500 |
| **DIA** | Dow Jones Industrial |
| **IWM** | Russell 2000 (Small Caps) |
| **VTI** | Total US Stock Market |
| **VOO** | Vanguard S&P 500 |
| **TQQQ** | 3x Leveraged Nasdaq-100 |
| **ARKK** | ARK Innovation ETF |

## 🚀 Getting Started

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)

### Installation

1. Navigate to the project:
```bash
cd C:\Projects\qqq-pullback-backtest
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Application

```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`.

## 🎛️ Imperial Controls

| Parameter | Description | Default |
|-----------|-------------|---------|
| Target Asset | ETF/Stock to backtest | QQQ |
| Pullback % | Enter when price drops this much from ATH | 5% |
| Stop-Loss % | Exit if position drops this much from entry | 10% |
| Exit Mode | ATH Recovery or Percent Rebound | ATH Recovery |
| Rebound % | (For Percent Rebound mode) Exit at this gain | 5% |
| Initial Capital | Starting capital for simulation | $10,000 |
| Cool-off | Wait for new ATH after stop-loss | Off |

## 📊 Mission Report Metrics

- **Total Return**: Overall percentage gain/loss
- **CAGR**: Compound Annual Growth Rate
- **Max Drawdown**: Largest peak-to-trough decline (Dark Side losses)
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profits to gross losses
- **Average Win/Loss**: Mean return for winning/losing trades
- **Time in Market**: Percentage of time with an open position

## 📁 Project Structure

```
qqq-pullback-backtest/
├── app.py              # Streamlit UI (The Empire Buys Back)
├── backtest_engine.py  # Core backtesting logic
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── .gitignore          # Git ignore rules
└── data/
    └── sample_qqq.csv  # Sample QQQ data for testing
```

## 🔮 Future Extensions (A New Hope)

- Multiple instruments in same backtest
- Leverage simulation
- Position sizing rules
- Live data integration
- Alerts
- Broker execution

## ⚠️ Disclaimer

*"I find your lack of due diligence disturbing."* - Darth Vader

This tool is for educational and research purposes only. It does not constitute financial advice. Past performance does not guarantee future results. Always do your own research before making investment decisions.

---

**Snowy & Saunders Trading Consortium** | *May the profits be with you* ⚔️
