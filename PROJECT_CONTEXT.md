# S&S Analytics - Project Context

**Last Updated:** 2026-02-13

This file captures essential context for continuing development if chat history is lost.

---

## Overview

**S&S Analytics** is a Streamlit web application for backtesting "buy the dip" pullback trading strategies and generating live signals.

**Live URL:** https://empire-buys-back.streamlit.app  
**GitHub Repo:** https://github.com/Minkoid/empire-buys-back

---

## Tech Stack

- **Frontend:** Streamlit (Python)
- **Backend/DB:** Supabase (PostgreSQL + Auth)
- **Data:** yfinance for historical/live prices
- **Hosting:** Streamlit Community Cloud (free)

---

## Key Files

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit app - all pages, UI, routing |
| `backtest_engine.py` | Core backtest logic, indicators (ATH, ATR, EMA), trade execution |
| `database.py` | Supabase client, auth functions, save/load settings |
| `requirements.txt` | Python dependencies |
| `.streamlit/secrets.toml` | Local secrets (gitignored) |

---

## Database (Supabase)

**Project:** xemmpxzbqufyngnlogxb  
**URL:** https://xemmpxzbqufyngnlogxb.supabase.co

### Tables

```sql
-- User settings (ticker configs, schedule)
user_settings (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users,
  ticker_settings JSONB,
  check_time VARCHAR(5),
  schedule_enabled BOOLEAN,
  created_at, updated_at TIMESTAMP
)

-- Signal check history
signal_history (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users,
  signals JSONB,
  checked_at TIMESTAMP
)
```

### Row Level Security
Users can only access their own data via `auth.uid() = user_id` policies.

### Streamlit Cloud Secrets
```toml
SUPABASE_URL = "https://xemmpxzbqufyngnlogxb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## App Pages

1. **Main/Backtest** - Manual strategy testing with parameter controls
2. **Strategy Finder** - Grid search optimization across parameter ranges
3. **Signal Dashboard** - Live price checking, BUY/SELL signals (ATH-based)
4. **Daily Signals** - Intraday signals based on today's open price
5. **Guide** - User documentation
6. **Changelog** - Version history (technical + user-friendly)
7. **Plan/Roadmap** - Future upgrade plans

---

## Authentication Flow

- Global auth required (check_authentication() runs before any page)
- Login/Register via Supabase Auth
- "Remember me" stores refresh token in URL query params
- Session restored on page reload

---

## Signal Dashboard Logic

Uses **rolling ATH** (cummax) matching backtest engine:
- `AT_ATH` - Price at all-time high
- `WATCHING` - Within 70% of pullback threshold
- `BUY` - Pullback threshold reached
- `HOLD` - In pullback but not deep enough
- `IN_POSITION` - User marked as holding
- `SELL` - Rebound target reached
- `STOP` - Stop-loss triggered

## Daily Signals Logic (v1.3.0)

Uses **today's opening price** instead of ATH:
- `ABOVE_OPEN` - Price above today's open (no signal)
- `WATCHING` - Within 70% of pullback threshold from open
- `BUY` - Dropped below open by pullback % threshold
- `HOLD` - Below open but not deep enough
- `IN_POSITION` - User marked as holding
- `SELL` - Rebound target reached
- `STOP` - Stop-loss triggered

---

## Key Users

- **Saunders** (you) - Developer/owner
- **Snowy** - Partner/tester, provides feedback

---

## Recent Work (Feb 2026)

1. Added global authentication with Supabase
2. Signal Dashboard with database persistence
3. Fixed RLS policy errors for saving settings
4. Aligned signal logic with backtest engine (rolling ATH)
5. Dark mode CSS fixes for light-mode browsers
6. Added changelog page

---

## Pending/Roadmap

- [ ] Automated scheduled checks (needs external scheduler like GitHub Actions)
- [ ] Notifications (Telegram recommended - free & easy)
- [ ] Paper trading integration (Alpaca API)

---

## Troubleshooting

**"Failed to save settings" RLS error:**  
- User must be logged in with valid session
- Session must be set on Supabase client (database.py handles this)

**White-on-white display issues:**  
- Added aggressive CSS `color-scheme: dark` overrides
- BaseWeb component specific selectors for dropdowns

**Signal logic mismatch:**  
- Signal Dashboard now uses cummax() for rolling ATH
- Matches backtest_engine.py approach

---

## To Resume Development

1. Open this project in Cursor
2. Share this file with new chat
3. State what you want to work on
4. The AI can read the codebase to fill in details

