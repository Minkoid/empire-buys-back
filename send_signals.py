#!/usr/bin/env python3
"""
S&S Analytics - Automated Signal Email Sender

This script is run by GitHub Actions at scheduled times to:
1. Fetch all users with email notifications enabled
2. Calculate current signals for their tickers
3. Send email summaries via Resend

Environment variables required:
- SUPABASE_URL
- SUPABASE_KEY  
- RESEND_API_KEY
"""

import os
import json
import yfinance as yf
from datetime import datetime
import pytz
import resend

# Configuration from environment
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
RESEND_API_KEY = os.environ.get('RESEND_API_KEY')

# Initialize Resend
resend.api_key = RESEND_API_KEY


def get_supabase_client():
    """Get Supabase client."""
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def get_users_for_notification(current_hour_minute: str):
    """
    Get all users who have email notifications enabled for the current time.
    
    Args:
        current_hour_minute: Current time in HH:MM format (UK time)
    """
    client = get_supabase_client()
    
    # Get all user settings
    response = client.table('user_settings').select('*').execute()
    
    users_to_notify = []
    
    for row in response.data:
        automation = row.get('automation_settings')
        if not automation:
            continue
            
        settings = json.loads(automation) if isinstance(automation, str) else automation
        
        # Check if enabled and time matches
        if settings.get('email_enabled') and settings.get('daily_signal_time') == current_hour_minute:
            notification_email = settings.get('notification_email')
            if notification_email:
                users_to_notify.append({
                    'user_id': row.get('user_id'),
                    'email': notification_email,
                    'signal_types': settings.get('signal_types', ['ATH', 'Daily']),
                    'notify_buy_only': settings.get('notify_buy_only', False),
                    'ticker_settings': json.loads(row.get('ticker_settings', '{}')) if row.get('ticker_settings') else {}
                })
    
    return users_to_notify


def calculate_ath_signals(tickers: dict) -> dict:
    """Calculate ATH-based signals for given tickers."""
    results = {}
    
    for ticker, settings in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2y")
            
            if len(hist) > 0:
                hist['ATH'] = hist['Close'].cummax()
                current_price = hist['Close'].iloc[-1]
                current_ath = hist['ATH'].iloc[-1]
                pullback_pct = (current_ath - current_price) / current_ath * 100
                
                # Determine signal
                if settings.get('in_position'):
                    entry = settings.get('entry_price', 0)
                    if entry:
                        pnl_pct = (current_price - entry) / entry * 100
                        if pnl_pct >= settings['rebound']:
                            signal = 'SELL'
                        elif pnl_pct <= -settings['stop_loss']:
                            signal = 'STOP'
                        else:
                            signal = 'IN_POSITION'
                    else:
                        signal = 'IN_POSITION'
                else:
                    if pullback_pct >= settings['pullback']:
                        signal = 'BUY'
                    elif pullback_pct >= settings['pullback'] * 0.7:
                        signal = 'WATCHING'
                    elif abs(current_price - current_ath) / current_ath < 0.001:
                        signal = 'AT_ATH'
                    else:
                        signal = 'HOLD'
                
                results[ticker] = {
                    'signal': signal,
                    'price': current_price,
                    'ath': current_ath,
                    'pullback_pct': pullback_pct
                }
        except Exception as e:
            results[ticker] = {'signal': 'ERROR', 'error': str(e)}
    
    return results


def calculate_daily_signals(tickers: dict) -> dict:
    """Calculate daily (today's open) signals for given tickers."""
    results = {}
    
    for ticker, settings in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            
            if len(hist) > 0:
                today_open = hist['Open'].iloc[-1]
                current_price = hist['Close'].iloc[-1]
                pullback_pct = (today_open - current_price) / today_open * 100
                
                # Determine signal
                if settings.get('in_position'):
                    entry = settings.get('entry_price', 0)
                    if entry:
                        pnl_pct = (current_price - entry) / entry * 100
                        if pnl_pct >= settings['rebound']:
                            signal = 'SELL'
                        elif pnl_pct <= -settings['stop_loss']:
                            signal = 'STOP'
                        else:
                            signal = 'IN_POSITION'
                    else:
                        signal = 'IN_POSITION'
                else:
                    if current_price > today_open:
                        signal = 'ABOVE_OPEN'
                    elif pullback_pct >= settings['pullback']:
                        signal = 'BUY'
                    elif pullback_pct >= settings['pullback'] * 0.7:
                        signal = 'WATCHING'
                    else:
                        signal = 'HOLD'
                
                results[ticker] = {
                    'signal': signal,
                    'price': current_price,
                    'open': today_open,
                    'pullback_pct': pullback_pct
                }
        except Exception as e:
            results[ticker] = {'signal': 'ERROR', 'error': str(e)}
    
    return results


def format_signal_email(user: dict, ath_signals: dict, daily_signals: dict) -> tuple:
    """Format the email subject and body."""
    signal_types = user.get('signal_types', ['ATH', 'Daily'])
    notify_buy_only = user.get('notify_buy_only', False)
    
    # Collect all signals
    all_buy_signals = []
    all_signals = []
    
    if 'ATH' in signal_types and ath_signals:
        for ticker, data in ath_signals.items():
            signal = data.get('signal', 'UNKNOWN')
            if signal == 'BUY':
                all_buy_signals.append(f"🟢 {ticker}: BUY (ATH) - {data.get('pullback_pct', 0):.1f}% below ATH")
            all_signals.append(('ATH', ticker, data))
    
    if 'Daily' in signal_types and daily_signals:
        for ticker, data in daily_signals.items():
            signal = data.get('signal', 'UNKNOWN')
            if signal == 'BUY':
                all_buy_signals.append(f"🟢 {ticker}: BUY (Daily) - {data.get('pullback_pct', 0):.1f}% below open")
            all_signals.append(('Daily', ticker, data))
    
    # If buy-only and no buy signals, skip
    if notify_buy_only and not all_buy_signals:
        return None, None
    
    # Build subject
    if all_buy_signals:
        subject = f"🟢 Snowy & Saunders: {len(all_buy_signals)} BUY Signal(s)!"
    else:
        subject = "📊 Snowy & Saunders: Daily Signal Summary"
    
    # Build body
    uk_tz = pytz.timezone('Europe/London')
    now = datetime.now(uk_tz)
    
    body_lines = [
        f"<h2 style='font-family: Georgia, serif; color: #1e3a5f;'>Snowy & Saunders Analytics</h2>",
        f"<h3 style='font-family: Georgia, serif; color: #334155;'>Signal Report</h3>",
        f"<p style='font-family: Georgia, serif;'><strong>Date:</strong> {now.strftime('%A, %d %B %Y')}</p>",
        f"<p style='font-family: Georgia, serif;'><strong>Time:</strong> {now.strftime('%H:%M')} UK</p>",
        "<hr>"
    ]
    
    if all_buy_signals:
        body_lines.append("<h3>🟢 BUY Signals</h3>")
        body_lines.append("<ul>")
        for sig in all_buy_signals:
            body_lines.append(f"<li>{sig}</li>")
        body_lines.append("</ul>")
        body_lines.append("<hr>")
    
    # ATH Signals section
    if 'ATH' in signal_types and ath_signals:
        body_lines.append("<h3>📡 ATH-Based Signals</h3>")
        body_lines.append("<table border='1' cellpadding='8' style='border-collapse: collapse;'>")
        body_lines.append("<tr><th>Ticker</th><th>Signal</th><th>Price</th><th>ATH</th><th>Pullback</th></tr>")
        for ticker, data in ath_signals.items():
            signal = data.get('signal', 'UNKNOWN')
            price = data.get('price', 0)
            ath = data.get('ath', 0)
            pullback = data.get('pullback_pct', 0)
            
            color = '#22c55e' if signal == 'BUY' else '#ef4444' if signal in ['SELL', 'STOP'] else '#f59e0b' if signal == 'WATCHING' else '#666'
            body_lines.append(f"<tr><td><strong>{ticker}</strong></td><td style='color:{color};'>{signal}</td><td>${price:.2f}</td><td>${ath:.2f}</td><td>-{pullback:.1f}%</td></tr>")
        body_lines.append("</table>")
    
    # Daily Signals section
    if 'Daily' in signal_types and daily_signals:
        body_lines.append("<h3>📅 Daily Signals (vs Today's Open)</h3>")
        body_lines.append("<table border='1' cellpadding='8' style='border-collapse: collapse;'>")
        body_lines.append("<tr><th>Ticker</th><th>Signal</th><th>Price</th><th>Open</th><th>Change</th></tr>")
        for ticker, data in daily_signals.items():
            signal = data.get('signal', 'UNKNOWN')
            price = data.get('price', 0)
            open_price = data.get('open', 0)
            pullback = data.get('pullback_pct', 0)
            
            color = '#22c55e' if signal == 'BUY' else '#ef4444' if signal in ['SELL', 'STOP'] else '#f59e0b' if signal == 'WATCHING' else '#666'
            change_str = f"+{abs(pullback):.2f}%" if pullback < 0 else f"-{pullback:.2f}%"
            body_lines.append(f"<tr><td><strong>{ticker}</strong></td><td style='color:{color};'>{signal}</td><td>${price:.2f}</td><td>${open_price:.2f}</td><td>{change_str}</td></tr>")
        body_lines.append("</table>")
    
    body_lines.append("<hr>")
    body_lines.append("<p style='color: #666; font-size: 12px; font-family: Georgia, serif;'>Sent by Snowy & Saunders Analytics. <a href='https://empire-buys-back.streamlit.app'>Open App</a></p>")
    
    return subject, "\n".join(body_lines)


def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Send email via Resend."""
    try:
        params = {
            "from": "Snowy & Saunders Analytics <signals@resend.dev>",
            "to": [to_email],
            "subject": subject,
            "html": html_body
        }
        
        response = resend.Emails.send(params)
        print(f"Email sent to {to_email}: {response}")
        return True
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        return False


def main():
    """Main entry point for scheduled runs."""
    print("=" * 50)
    print("Snowy & Saunders Analytics - Signal Email Sender")
    print("=" * 50)
    
    # Get current UK time
    uk_tz = pytz.timezone('Europe/London')
    now = datetime.now(uk_tz)
    current_time = now.strftime('%H:%M')
    
    print(f"Current UK time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Looking for users scheduled at: {current_time}")
    
    # Get users to notify
    users = get_users_for_notification(current_time)
    print(f"Found {len(users)} user(s) to notify")
    
    if not users:
        print("No users to notify at this time.")
        return
    
    for user in users:
        print(f"\nProcessing user: {user['email']}")
        
        tickers = user.get('ticker_settings', {})
        if not tickers:
            print("  No tickers configured, skipping.")
            continue
        
        # Calculate signals
        ath_signals = None
        daily_signals = None
        
        if 'ATH' in user.get('signal_types', []):
            print("  Calculating ATH signals...")
            ath_signals = calculate_ath_signals(tickers)
        
        if 'Daily' in user.get('signal_types', []):
            print("  Calculating Daily signals...")
            daily_signals = calculate_daily_signals(tickers)
        
        # Format email
        subject, body = format_signal_email(user, ath_signals, daily_signals)
        
        if subject is None:
            print("  No signals to report (buy-only mode with no buys), skipping.")
            continue
        
        # Send email
        print(f"  Sending email: {subject}")
        if send_email(user['email'], subject, body):
            print("  ✓ Email sent successfully!")
        else:
            print("  ✗ Failed to send email")
    
    print("\n" + "=" * 50)
    print("Done!")


if __name__ == "__main__":
    main()
