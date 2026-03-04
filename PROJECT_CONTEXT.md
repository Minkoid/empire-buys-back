# Snowy & Saunders Analytics - Project Context

**Last Updated:** 2026-02-25

This file captures essential context for continuing development if chat history is lost.

---

## Overview

**Snowy & Saunders Analytics** is a Streamlit web application for backtesting "buy the dip" pullback trading strategies and generating live signals.

**Live URL:** https://empire-buys-back.streamlit.app  
**GitHub Repo:** https://github.com/Minkoid/empire-buys-back  
**Local Path:** C:\Projects\qqq-pullback-backtest

---

## Tech Stack

- **Frontend:** Streamlit (Python)
- **Backend/DB:** Supabase (PostgreSQL + Auth)
- **Data:** yfinance for historical/live prices
- **Hosting:** Streamlit Community Cloud (free tier)
- **Email:** Resend API for signal notifications
- **Automation:** GitHub Actions (runs every 15 mins)
- **Font:** Roboto (Google Fonts)

---

## Key Files

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit app - all pages, UI, routing |
| `backtest_engine.py` | Core backtest logic, indicators (ATH, ATR, EMA), trade execution |
| `database.py` | Supabase client, auth functions, save/load settings |
| `send_signals.py` | GitHub Actions script - fetches users, calculates signals, sends emails |
| `.github/workflows/send_signals.yml` | GitHub Actions workflow - runs every 15 mins |
| `requirements.txt` | Python dependencies |
| `.streamlit/secrets.toml` | Local secrets (gitignored) |
| `.streamlit/config.toml` | Forces dark theme at app level |

---

## Database (Supabase)

**Project:** xemmpxzbqufyngnlogxb  
**URL:** https://xemmpxzbqufyngnlogxb.supabase.co

### Tables

```sql
-- User settings (ticker configs, automation)
user_settings (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users,
  ticker_settings JSONB,        -- ATH signal page ticker configs
  check_time VARCHAR(5),
  schedule_enabled BOOLEAN,
  automation_settings JSONB,    -- Email notification preferences
  created_at, updated_at TIMESTAMP
)
```

### automation_settings JSONB structure
```json
{
  "email_enabled": true,
  "notification_email": "user@example.com",
  "daily_signal_time": "10:15",
  "signal_types": ["ATH", "Daily"],
  "notify_buy_only": false
}
```

### Row Level Security (RLS)
- Users can only access their own data via `auth.uid() = user_id` policies
- **Important:** A public SELECT policy exists to allow GitHub Actions (anon key) to read all rows for email sending:
  ```sql
  -- "Allow service access to user_settings" policy
  -- roles: {public}, cmd: SELECT, qual: true
  ```
- All upsert calls must use `on_conflict='user_id'` to avoid duplicate key errors

### Streamlit Cloud Secrets
```toml
SUPABASE_URL = "https://xemmpxzbqufyngnlogxb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### GitHub Actions Secrets (in repo settings)
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `RESEND_API_KEY`

---

## App Pages

1. **Main/Backtest** - Manual strategy testing with parameter controls
2. **Strategy Finder** - Grid search optimization across parameter ranges
3. **Signal Dashboard** - Live price checking, BUY/SELL signals (ATH-based), saves to DB
4. **Daily Signals** - Intraday signals based on today's open price (session state only, not saved to DB)
5. **Notifications** - Email notification setup (was "Automation"), schedule and signal type selection
6. **Guide** - User documentation
7. **Changelog** - Version history (technical + user-friendly descriptions)
8. **Plan/Roadmap** - Future upgrade plans

### Header Navigation Buttons
`app-title | ticker-selector | 🚀Run | 🔍Finder | 📡Signals | 📅Daily | 🔔Notify | 📋Guide | logout`

---

## Authentication Flow

- Global auth required (`check_authentication()` runs before any page)
- Login/Register via Supabase Auth
- "Remember me" stores refresh token in URL query params
- Session restored on page reload
- `get_supabase_client()` calls `client.auth.set_session()` to satisfy RLS

---

## Signal Dashboard Logic (ATH-based)

Uses **rolling ATH** (cummax over 2 years of data) matching backtest engine:
- `AT_ATH` - Price at all-time high (purple)
- `WATCHING` - Within 70% of pullback threshold (amber)
- `BUY` - Pullback threshold reached (green)
- `HOLD` - In pullback but not deep enough (grey)
- `IN_POSITION` - User marked as holding (blue)
- `SELL` - Rebound target reached (red)
- `STOP` - Stop-loss triggered (red)

Ticker settings saved to `user_settings.ticker_settings` in DB.

## Daily Signals Logic

Uses **today's opening price** instead of ATH:
- `ABOVE_OPEN` - Price above today's open (purple)
- `WATCHING` - Within 70% of pullback threshold from open (amber)
- `BUY` - Dropped below open by pullback % threshold (green)
- `HOLD` - Below open but not deep enough (grey)
- `IN_POSITION` - User marked as holding (blue)
- `SELL` - Rebound target reached (red)
- `STOP` - Stop-loss triggered (red)

**Note:** Daily Signals uses separate session state (`daily_signal_tickers`) and is NOT currently saved to the database. Uses same ticker_settings from DB for email signals.

---

## Email Notifications (Automated)

- GitHub Actions workflow runs every 15 minutes (`*/15 * * * *`)
- `send_signals.py` fetches all users with `email_enabled: true`
- Calculates ATH and/or Daily signals based on user's ticker_settings
- Sends HTML email via Resend API from `signals@resend.dev`
- **Test mode:** Trigger manually in GitHub Actions → Run workflow → set test_mode=true
- Email subject includes BUY count if any BUY signals present

---

## Available Tickers

```python
AVAILABLE_TICKERS = {
    "QQQ": "Nasdaq-100 (Tech-heavy)",
    "SPY": "S&P 500",
    "DIA": "Dow Jones Industrial",
    "IWM": "Russell 2000 (Small Caps)",
    "VTI": "Total US Stock Market",
    "VOO": "Vanguard S&P 500",
    "TQQQ": "3x Leveraged Nasdaq-100",
    "SOXL": "3x Semiconductors",
    "ARKK": "ARK Innovation ETF",
    "EEM": "Emerging Markets ETF",
    "GLD": "Gold ETF",
    "SLV": "Silver ETF",
    "^N225": "Nikkei 225 (Japan)",
}
```

---

## Backtest Engine Notes

- `run_backtest()` - Full backtest used by Manual Backtest page
- `run_backtest_fast()` - Optimised version used by Strategy Finder
- **Important fix (v1.6.1):** Both now use `start_idx = max(ema_period, atr_period)` to ensure matching CAGR results. Previously `run_backtest_fast` also included `trend_ma_period` causing discrepancies.

---

## Key Users

- **Saunders** (you) - Developer/owner
- **Snowy** - Partner/tester, provides feedback on strategy logic

---

## Current Version: 1.6.1

### Recent Changes (Feb 2026)
- v1.6.1 - Fixed CAGR discrepancy between Strategy Finder and Manual Backtest
- v1.6.0 - Automated email notifications live via GitHub Actions + Resend
- v1.5.1 - Fixed duplicate key upsert errors on all save functions
- v1.5.0 - Rebranded to "Snowy & Saunders Analytics", Roboto font
- v1.4.1 - Switched from Telegram to email notifications
- v1.4.0 - Notifications page (was Automation)
- v1.3.0 - Daily Signals page
- v1.2.x - Dark mode fixes, Supabase auth, RLS fixes
- v1.0.0 - Initial release

---

## Pending/Roadmap

- [ ] **Alpaca paper trading integration** - Auto-execute bracket orders (buy + take profit + stop loss) when signals fire. User needs to create free account at alpaca.markets and provide API key + secret.
- [ ] **Signal history logging** - Save signal results to DB each time email runs for historical reference and performance tracking
- [ ] **Separate Daily Signal ticker settings** - Currently Daily Signals uses same settings as ATH signals. Could add `daily_ticker_settings` column for separate thresholds.

---

## Troubleshooting

**"Failed to save settings" duplicate key error:**
- All upsert calls must include `on_conflict='user_id'`
- Fixed in database.py for all three save functions

**"Found 0 users" in GitHub Actions:**
- RLS was blocking anon key access
- Fixed by adding public SELECT policy in Supabase SQL Editor

**White-on-white display issues:**
- `.streamlit/config.toml` forces dark theme at app level
- Aggressive CSS overrides for BaseWeb components

**Streamlit Cloud not updating:**
- Go to app dashboard → Reboot app

---

## To Resume Development

1. Open `C:\Projects\qqq-pullback-backtest` in Cursor
2. Share this file with the new chat
3. State what you want to work on
4. The AI can read the codebase to fill in details
