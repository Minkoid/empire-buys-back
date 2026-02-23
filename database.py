# AIModified:2026-01-30T12:00:00Z
"""
S&S Analytics - Database Module

Handles all Supabase interactions for user authentication,
ticker settings persistence, and signal history.
"""

import streamlit as st
from supabase import create_client, Client
from typing import Optional, Dict, List
import json
from datetime import datetime
import pytz


def get_supabase_client() -> Optional[Client]:
    """
    Get Supabase client using secrets from Streamlit.
    Returns None if not configured.
    Sets the session if user is logged in for RLS to work.
    """
    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
        
        if not url or not key:
            return None
        
        client = create_client(url, key)
        
        # Set session if we have one stored (required for RLS policies)
        session = st.session_state.get('session')
        if session:
            try:
                client.auth.set_session(session.access_token, session.refresh_token)
            except:
                pass  # Session might be expired, will fail gracefully
        
        return client
    except Exception as e:
        st.warning(f"Database not configured: {e}")
        return None


def is_database_configured() -> bool:
    """Check if Supabase is properly configured."""
    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
        return bool(url and key)
    except:
        return False


# ============== Authentication ==============

def sign_up(email: str, password: str) -> Dict:
    """
    Register a new user.
    Returns dict with 'success', 'user', or 'error'.
    """
    client = get_supabase_client()
    if not client:
        return {"success": False, "error": "Database not configured"}
    
    try:
        response = client.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if response.user:
            return {"success": True, "user": response.user}
        else:
            return {"success": False, "error": "Registration failed"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def sign_in(email: str, password: str) -> Dict:
    """
    Sign in an existing user.
    Returns dict with 'success', 'user', 'session', or 'error'.
    """
    client = get_supabase_client()
    if not client:
        return {"success": False, "error": "Database not configured"}
    
    try:
        response = client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            return {
                "success": True, 
                "user": response.user,
                "session": response.session
            }
        else:
            return {"success": False, "error": "Invalid credentials"}
    except Exception as e:
        error_msg = str(e)
        if "Invalid login credentials" in error_msg:
            return {"success": False, "error": "Invalid email or password"}
        return {"success": False, "error": error_msg}


def sign_out() -> bool:
    """Sign out the current user."""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        client.auth.sign_out()
        return True
    except:
        return False


def get_current_user():
    """Get the currently logged in user from session state."""
    return st.session_state.get('user', None)


def is_logged_in() -> bool:
    """Check if a user is currently logged in."""
    return get_current_user() is not None


# ============== Ticker Settings ==============

def save_ticker_settings(user_id: str, tickers: Dict) -> bool:
    """
    Save user's ticker settings to the database.
    
    Args:
        user_id: The user's ID
        tickers: Dict of ticker settings, e.g.:
            {'QQQ': {'pullback': 5.0, 'rebound': 5.0, 'stop_loss': 10.0, ...}}
    """
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        # Convert to JSON-safe format
        settings_json = json.dumps(tickers)
        
        # Upsert (insert or update)
        client.table('user_settings').upsert({
            'user_id': user_id,
            'ticker_settings': settings_json,
            'updated_at': datetime.now(pytz.UTC).isoformat()
        }).execute()
        
        return True
    except Exception as e:
        st.error(f"Failed to save settings: {e}")
        return False


def load_ticker_settings(user_id: str) -> Optional[Dict]:
    """
    Load user's ticker settings from the database.
    Returns None if not found or error.
    """
    client = get_supabase_client()
    if not client:
        return None
    
    try:
        response = client.table('user_settings').select('ticker_settings').eq('user_id', user_id).execute()
        
        if response.data and len(response.data) > 0:
            settings_json = response.data[0].get('ticker_settings')
            if settings_json:
                return json.loads(settings_json)
        
        return None
    except Exception as e:
        st.error(f"Failed to load settings: {e}")
        return None


def save_check_schedule(user_id: str, check_time: str, enabled: bool) -> bool:
    """
    Save user's preferred check schedule.
    
    Args:
        user_id: The user's ID
        check_time: Time in HH:MM format (24-hour, UK time)
        enabled: Whether scheduled checks are enabled
    """
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        client.table('user_settings').upsert({
            'user_id': user_id,
            'check_time': check_time,
            'schedule_enabled': enabled,
            'updated_at': datetime.now(pytz.UTC).isoformat()
        }).execute()
        
        return True
    except Exception as e:
        st.error(f"Failed to save schedule: {e}")
        return False


def load_check_schedule(user_id: str) -> Dict:
    """
    Load user's check schedule preferences.
    Returns dict with 'check_time' and 'enabled'.
    """
    client = get_supabase_client()
    if not client:
        return {"check_time": "20:30", "enabled": False}
    
    try:
        response = client.table('user_settings').select('check_time, schedule_enabled').eq('user_id', user_id).execute()
        
        if response.data and len(response.data) > 0:
            row = response.data[0]
            return {
                "check_time": row.get('check_time', '20:30'),
                "enabled": row.get('schedule_enabled', False)
            }
        
        return {"check_time": "20:30", "enabled": False}
    except:
        return {"check_time": "20:30", "enabled": False}


# ============== Signal History ==============

def save_signal_check(user_id: str, signals: Dict) -> bool:
    """
    Log a signal check to the database for history tracking.
    
    Args:
        user_id: The user's ID
        signals: Dict of signal results from the check
    """
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        uk_tz = pytz.timezone('Europe/London')
        
        client.table('signal_history').insert({
            'user_id': user_id,
            'signals': json.dumps(signals),
            'checked_at': datetime.now(uk_tz).isoformat()
        }).execute()
        
        return True
    except Exception as e:
        # Don't show error for history logging failures
        return False


def get_signal_history(user_id: str, limit: int = 50) -> List[Dict]:
    """
    Get recent signal history for a user.
    
    Returns list of dicts with 'checked_at' and 'signals'.
    """
    client = get_supabase_client()
    if not client:
        return []
    
    try:
        response = client.table('signal_history').select('*').eq('user_id', user_id).order('checked_at', desc=True).limit(limit).execute()
        
        results = []
        for row in response.data:
            results.append({
                'checked_at': row.get('checked_at'),
                'signals': json.loads(row.get('signals', '{}'))
            })
        
        return results
    except:
        return []


# ============== Automation Settings ==============

def save_automation_settings(user_id: str, settings: Dict) -> bool:
    """
    Save user's automation/notification settings.
    
    Args:
        user_id: The user's ID
        settings: Dict with telegram_enabled, telegram_bot_token, telegram_chat_id, etc.
    """
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        # Separate sensitive token from other settings
        settings_json = json.dumps({
            'telegram_enabled': settings.get('telegram_enabled', False),
            'daily_signal_time': settings.get('daily_signal_time', '20:30'),
            'signal_types': settings.get('signal_types', ['ATH', 'Daily']),
            'notify_buy_only': settings.get('notify_buy_only', False),
        })
        
        client.table('user_settings').upsert({
            'user_id': user_id,
            'automation_settings': settings_json,
            'telegram_bot_token': settings.get('telegram_bot_token', ''),
            'telegram_chat_id': settings.get('telegram_chat_id', ''),
            'updated_at': datetime.now(pytz.UTC).isoformat()
        }).execute()
        
        return True
    except Exception as e:
        st.error(f"Failed to save automation settings: {e}")
        return False


def load_automation_settings(user_id: str) -> Dict:
    """
    Load user's automation/notification settings.
    Returns dict with all automation preferences.
    """
    client = get_supabase_client()
    if not client:
        return {
            'telegram_enabled': False,
            'telegram_bot_token': '',
            'telegram_chat_id': '',
            'daily_signal_time': '20:30',
            'signal_types': ['ATH', 'Daily'],
            'notify_buy_only': False
        }
    
    try:
        response = client.table('user_settings').select(
            'automation_settings, telegram_bot_token, telegram_chat_id'
        ).eq('user_id', user_id).execute()
        
        if response.data and len(response.data) > 0:
            row = response.data[0]
            settings_json = row.get('automation_settings')
            
            result = {
                'telegram_bot_token': row.get('telegram_bot_token', ''),
                'telegram_chat_id': row.get('telegram_chat_id', ''),
            }
            
            if settings_json:
                parsed = json.loads(settings_json)
                result.update(parsed)
            else:
                result.update({
                    'telegram_enabled': False,
                    'daily_signal_time': '20:30',
                    'signal_types': ['ATH', 'Daily'],
                    'notify_buy_only': False
                })
            
            return result
        
        return {
            'telegram_enabled': False,
            'telegram_bot_token': '',
            'telegram_chat_id': '',
            'daily_signal_time': '20:30',
            'signal_types': ['ATH', 'Daily'],
            'notify_buy_only': False
        }
    except:
        return {
            'telegram_enabled': False,
            'telegram_bot_token': '',
            'telegram_chat_id': '',
            'daily_signal_time': '20:30',
            'signal_types': ['ATH', 'Daily'],
            'notify_buy_only': False
        }


# ============== Database Setup SQL ==============

def get_setup_sql() -> str:
    """
    Returns the SQL needed to set up the database tables.
    Run this in Supabase SQL Editor.
    """
    return """
-- User Settings Table
CREATE TABLE IF NOT EXISTS user_settings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
    ticker_settings JSONB,
    check_time VARCHAR(5) DEFAULT '20:30',
    schedule_enabled BOOLEAN DEFAULT FALSE,
    automation_settings JSONB,
    telegram_bot_token TEXT,
    telegram_chat_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- If table already exists, add new columns
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS automation_settings JSONB;
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS telegram_bot_token TEXT;
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS telegram_chat_id TEXT;

-- Signal History Table  
CREATE TABLE IF NOT EXISTS signal_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    signals JSONB NOT NULL,
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE signal_history ENABLE ROW LEVEL SECURITY;

-- Policies: Users can only access their own data
CREATE POLICY "Users can view own settings" ON user_settings
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own settings" ON user_settings
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own settings" ON user_settings
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own history" ON signal_history
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own history" ON signal_history
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id);
CREATE INDEX IF NOT EXISTS idx_signal_history_user_id ON signal_history(user_id);
CREATE INDEX IF NOT EXISTS idx_signal_history_checked_at ON signal_history(checked_at DESC);
"""
