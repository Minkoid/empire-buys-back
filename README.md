# S&S Analytics

A professional pullback strategy backtesting platform built with Streamlit.

## Overview

S&S Analytics allows you to:
- Analyse historical price data for multiple ETFs (QQQ, SPY, DIA, etc.)
- Simulate a pullback-and-rebound trading strategy
- Understand historical risk, returns, drawdowns, and trade behaviour
- Rapidly tune parameters and iterate based on visual feedback

## Strategy Overview

### Entry Logic
- Track the **all-time high (ATH)** price
- When price pulls back by **X%** from ATH, enter a long position

### Exit Logic (Configurable)
- **ATH Recovery**: Exit when price returns to ATH
- **Percent Rebound**: Exit when price rebounds **Y%** from entry price

### Risk Management
- Stop-loss: Exit if price drops **Z%** below entry
- Single position at a time
- Optional cool-off period after stop-loss

## Available Assets

| Ticker | Description |
|--------|-------------|
| QQQ | Nasdaq-100 (Tech-heavy) |
| SPY | S&P 500 |
| DIA | Dow Jones Industrial |
| IWM | Russell 2000 (Small Caps) |
| VTI | Total US Stock Market |
| VOO | Vanguard S&P 500 |
| TQQQ | 3x Leveraged Nasdaq-100 |
| ARKK | ARK Innovation ETF |

## Getting Started

### Prerequisites
- Python 3.9 or higher

### Installation

```bash
cd C:\Projects\qqq-pullback-backtest
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Running Locally

```bash
streamlit run app.py
```

## Configuration Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| Asset | ETF/Stock to backtest | QQQ |
| Pullback % | Enter when price drops this much from ATH | 5% |
| Stop-Loss % | Exit if position drops this much from entry | 10% |
| Exit Mode | ATH Recovery or Percent Rebound | ATH Recovery |
| Rebound % | Exit at this gain (Percent Rebound mode) | 5% |
| Initial Capital | Starting capital for simulation | $10,000 |
| Cool-off | Wait for new ATH after stop-loss | Off |

## Metrics

- **Total Return**: Overall percentage gain/loss
- **CAGR**: Compound Annual Growth Rate
- **Max Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profits to gross losses
- **Average Win/Loss**: Mean return for winning/losing trades
- **Time in Market**: Percentage of time with an open position

## Project Structure

```
qqq-pullback-backtest/
├── app.py              # Streamlit UI
├── backtest_engine.py  # Core backtesting logic
├── requirements.txt    # Python dependencies
├── README.md           # Documentation
├── .gitignore          # Git ignore rules
└── data/
    └── sample_qqq.csv  # Sample data for testing
```

## Disclaimer

This tool is for educational and research purposes only. It does not constitute financial advice. Past performance does not guarantee future results.

---

**S&S Analytics** | Snowy & Saunders
