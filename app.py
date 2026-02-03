# AIModified:2026-01-29T15:22:18Z
"""
S&S Analytics - Pullback Strategy Backtesting Tool

A Streamlit application for backtesting pullback-based trading strategies.
Supports ATH-based, ATR-based, and EMA-relative entry/exit modes.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

from backtest_engine import (
    BacktestConfig,
    ExitMode,
    run_backtest,
    load_data_from_csv,
    download_ticker_data
)

# Available tickers for backtesting
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
    "GLD": "Gold ETF",
    "SLV": "Silver ETF",
}


# Page configuration
st.set_page_config(
    page_title="S&S Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Page navigation
if 'page' not in st.session_state:
    st.session_state['page'] = 'backtest'

# Professional CSS theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Press+Start+2P&display=swap');
    
    :root {
        --bg-primary: #0f1419;
        --bg-secondary: #1a1f26;
        --bg-card: #232a33;
        --accent-green: #22c55e;
        --accent-red: #ef4444;
        --accent-blue: #3b82f6;
        --accent-amber: #f59e0b;
        --accent-teal: #14b8a6;
        --accent-purple: #a855f7;
        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
        --border-color: #334155;
    }
    
    .stApp {
        background: linear-gradient(135deg, var(--bg-primary) 0%, #1a1f2e 100%);
    }
    
    .main .block-container {
        padding-top: 2rem;
        max-width: 1400px;
    }
    
    h1, h2, h3 {
        font-family: 'Press Start 2P', cursive !important;
        font-weight: 400 !important;
        font-size: 0.9rem !important;
    }
    
    .app-title {
        font-family: 'Press Start 2P', cursive !important;
        font-weight: 400 !important;
        font-size: 1.6rem !important;
        color: #f8fafc !important;
        letter-spacing: 0.05em;
        text-shadow: 2px 2px 0px #3b82f6, 4px 4px 0px rgba(59, 130, 246, 0.3);
    }
    
    .app-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        color: #94a3b8;
        font-weight: 400;
    }
    
    .metric-card {
        background: linear-gradient(145deg, var(--bg-card) 0%, #2a323d 100%);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 1.25rem;
        margin: 0.5rem 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.75rem;
        font-weight: 600;
        margin: 0.25rem 0;
    }
    
    .metric-label {
        font-family: 'Press Start 2P', cursive;
        font-size: 0.5rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.02em;
        font-weight: 400;
    }
    
    .positive { color: #22c55e !important; }
    .negative { color: #ef4444 !important; }
    .neutral { color: #3b82f6 !important; }
    .warning { color: #f59e0b !important; }
    
    .section-header {
        font-family: 'Press Start 2P', cursive;
        font-size: 0.85rem;
        font-weight: 400;
        color: #f8fafc;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #3b82f6;
        text-shadow: 1px 1px 0px #3b82f6;
    }
    
    /* Hide sidebar */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    /* Control card styling */
    .control-card {
        background: linear-gradient(145deg, #232a33 0%, #1a1f26 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.25rem;
        height: 100%;
    }
    
    .control-card-header {
        font-family: 'Press Start 2P', cursive;
        font-size: 0.6rem;
        color: #3b82f6;
        margin-bottom: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Preset buttons */
    .preset-btn {
        background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .preset-btn:hover {
        border-color: #3b82f6;
        background: linear-gradient(145deg, #1e3a5f 0%, #1e293b 100%);
    }
    
    .preset-btn.active {
        border-color: #3b82f6;
        background: linear-gradient(145deg, #1e40af 0%, #1e3a5f 100%);
    }
    
    /* Compact toggle styling */
    .stToggle label {
        font-size: 0.85rem !important;
    }
    
    /* Input styling */
    .stSlider > div > div {
        background-color: var(--bg-card);
    }
    
    .stNumberInput input {
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
        color: #ffffff !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
    }
    
    /* Toggle section styling */
    .toggle-section {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    /* Logo styling */
    .logo-container {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    .logo-icon {
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, #3b82f6 0%, #14b8a6 100%);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.25rem;
    }
</style>
""", unsafe_allow_html=True)


def create_metric_card(label: str, value: str, color_class: str = "neutral") -> str:
    """Create an HTML metric card."""
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value {color_class}">{value}</div>
    </div>
    """


def format_currency(value: float) -> str:
    """Format value as currency."""
    return f"${value:,.2f}"


def format_percent(value: float, include_sign: bool = True) -> str:
    """Format value as percentage."""
    if include_sign and value > 0:
        return f"+{value:.2f}%"
    return f"{value:.2f}%"


@st.cache_data(ttl=3600)
def get_ticker_data(ticker: str, source: str, start_date: str = "2000-01-01"):
    """Load or download ticker data with caching."""
    if source == "download":
        return download_ticker_data(ticker_symbol=ticker, start_date=start_date)
    else:
        return load_data_from_csv(source)


def create_equity_chart(result, df, ticker: str = "QQQ", show_ema: bool = True, show_trend_ma: bool = False):
    """Create the main equity curve and price chart."""
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.5, 0.3, 0.2],
        subplot_titles=("Portfolio Equity", f"{ticker} Price with Trade Markers", "Drawdown")
    )
    
    # Equity curve
    fig.add_trace(
        go.Scatter(
            x=result.equity_curve.index,
            y=result.equity_curve['Equity'],
            mode='lines',
            name='Portfolio Value',
            line=dict(color='#22c55e', width=2),
            fill='tozeroy',
            fillcolor='rgba(34, 197, 94, 0.1)'
        ),
        row=1, col=1
    )
    
    # Price chart
    fig.add_trace(
        go.Scatter(
            x=result.equity_curve.index,
            y=result.equity_curve['Price'],
            mode='lines',
            name=f'{ticker} Price',
            line=dict(color='#3b82f6', width=1.5)
        ),
        row=2, col=1
    )
    
    # EMA line
    if show_ema and 'EMA' in result.equity_curve.columns:
        fig.add_trace(
            go.Scatter(
                x=result.equity_curve.index,
                y=result.equity_curve['EMA'],
                mode='lines',
                name='EMA',
                line=dict(color='#a855f7', width=1.5, dash='solid'),
                opacity=0.8
            ),
            row=2, col=1
        )
    
    # Trend MA line
    if show_trend_ma and 'Trend_MA' in result.equity_curve.columns:
        fig.add_trace(
            go.Scatter(
                x=result.equity_curve.index,
                y=result.equity_curve['Trend_MA'],
                mode='lines',
                name='Trend MA',
                line=dict(color='#14b8a6', width=2, dash='solid'),
                opacity=0.9
            ),
            row=2, col=1
        )
    
    # ATH line
    fig.add_trace(
        go.Scatter(
            x=result.equity_curve.index,
            y=result.equity_curve['ATH'],
            mode='lines',
            name='All-Time High',
            line=dict(color='#f59e0b', width=1, dash='dot'),
            opacity=0.7
        ),
        row=2, col=1
    )
    
    # Trade markers
    for trade in result.trades:
        # Entry marker
        fig.add_trace(
            go.Scatter(
                x=[trade.entry_date],
                y=[trade.entry_price],
                mode='markers',
                name='Buy',
                marker=dict(
                    symbol='triangle-up',
                    size=12,
                    color='#22c55e',
                    line=dict(color='#166534', width=1)
                ),
                showlegend=False,
                hovertemplate=f"BUY<br>Date: {trade.entry_date.strftime('%Y-%m-%d')}<br>Price: ${trade.entry_price:.2f}<extra></extra>"
            ),
            row=2, col=1
        )
        
        # Exit marker
        exit_color = '#22c55e' if trade.is_win else '#ef4444'
        fig.add_trace(
            go.Scatter(
                x=[trade.exit_date],
                y=[trade.exit_price],
                mode='markers',
                name='Sell',
                marker=dict(
                    symbol='triangle-down',
                    size=12,
                    color=exit_color,
                    line=dict(color='#333333', width=1)
                ),
                showlegend=False,
                hovertemplate=f"SELL ({trade.exit_reason})<br>Date: {trade.exit_date.strftime('%Y-%m-%d')}<br>Price: ${trade.exit_price:.2f}<br>P&L: {trade.pnl_percent:+.2f}%<extra></extra>"
            ),
            row=2, col=1
        )
    
    # Drawdown chart
    fig.add_trace(
        go.Scatter(
            x=result.equity_curve.index,
            y=result.equity_curve['Drawdown_Pct'],
            mode='lines',
            name='Drawdown',
            line=dict(color='#ef4444', width=1.5),
            fill='tozeroy',
            fillcolor='rgba(239, 68, 68, 0.2)'
        ),
        row=3, col=1
    )
    
    # Update layout
    fig.update_layout(
        height=800,
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(15, 20, 25, 0.9)',
        font=dict(family="Inter, sans-serif", color='#f8fafc'),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(35, 42, 51, 0.9)',
            font=dict(color='#f8fafc')
        ),
        margin=dict(l=60, r=20, t=80, b=40)
    )
    
    # Update axes
    fig.update_xaxes(
        gridcolor='rgba(51, 65, 85, 0.5)',
        showgrid=True,
        zeroline=False
    )
    fig.update_yaxes(
        gridcolor='rgba(51, 65, 85, 0.5)',
        showgrid=True,
        zeroline=False
    )
    
    fig.update_yaxes(title_text="Equity ($)", row=1, col=1)
    fig.update_yaxes(title_text="Price ($)", row=2, col=1)
    fig.update_yaxes(title_text="Drawdown (%)", row=3, col=1)
    
    return fig


def create_trade_distribution_chart(result):
    """Create a histogram of trade returns."""
    if not result.trades:
        return None
    
    returns = [t.pnl_percent for t in result.trades]
    
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=returns,
        nbinsx=20,
        marker=dict(
            color='#3b82f6',
            line=dict(color='#1e40af', width=1)
        ),
        opacity=0.8
    ))
    
    fig.update_layout(
        title="Trade Returns Distribution",
        xaxis_title="Return (%)",
        yaxis_title="Frequency",
        height=350,
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(15, 20, 25, 0.9)',
        font=dict(family="Inter, sans-serif", color='#f8fafc'),
        margin=dict(l=60, r=20, t=60, b=40)
    )
    
    fig.update_xaxes(gridcolor='rgba(51, 65, 85, 0.5)')
    fig.update_yaxes(gridcolor='rgba(51, 65, 85, 0.5)')
    
    return fig


def create_yearly_returns_chart(result):
    """Create a bar chart of yearly returns."""
    equity = result.equity_curve['Equity'].copy()
    
    # Resample to yearly and calculate returns
    yearly = equity.resample('YE').last()
    yearly_returns = yearly.pct_change() * 100
    yearly_returns = yearly_returns.dropna()
    
    if len(yearly_returns) == 0:
        return None
    
    colors = ['#22c55e' if r > 0 else '#ef4444' for r in yearly_returns.values]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=yearly_returns.index.year,
        y=yearly_returns.values,
        marker=dict(color=colors),
        text=[f"{v:+.1f}%" for v in yearly_returns.values],
        textposition='outside',
        textfont=dict(color='#f8fafc', size=10)
    ))
    
    fig.update_layout(
        title="Yearly Returns",
        xaxis_title="Year",
        yaxis_title="Return (%)",
        height=350,
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(15, 20, 25, 0.9)',
        font=dict(family="Inter, sans-serif", color='#f8fafc'),
        margin=dict(l=60, r=20, t=60, b=40)
    )
    
    fig.update_xaxes(gridcolor='rgba(51, 65, 85, 0.5)', dtick=1)
    fig.update_yaxes(gridcolor='rgba(51, 65, 85, 0.5)')
    
    return fig


def show_roadmap():
    """Display the roadmap/upgrade plan page."""
    
    # Back button
    if st.button("← Back to Backtester"):
        st.session_state['page'] = 'backtest'
        st.rerun()
    
    st.markdown("""
    <div style="text-align: center; padding: 1.5rem 0 2rem 0;">
        <div style="font-size: 2.5rem; margin-bottom: 1rem;">🚀</div>
        <h1 class="app-title">S&S Analytics</h1>
        <p class="app-subtitle">Platform Upgrade Plan - Multi-User & Paper Trading</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Current State
    st.markdown('<div class="section-header">📍 Where We Are Now</div>', unsafe_allow_html=True)
    st.markdown("""
    S&S Analytics is a web app that lets you test "buy the dip" trading strategies on historical stock data, 
    adjusting rules like how big a price drop triggers a buy and when to sell, then instantly shows you 
    how that strategy would have performed over the past 25 years.
    """)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">✅</div>
            <div class="metric-label">Strategy Backtesting</div>
            <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 0.5rem;">Test on 25 years of data</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">✅</div>
            <div class="metric-label">Multiple Assets</div>
            <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 0.5rem;">QQQ, SPY, Gold & more</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">✅</div>
            <div class="metric-label">Quick Presets</div>
            <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 0.5rem;">Conservative to Aggressive</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">✅</div>
            <div class="metric-label">Visual Analytics</div>
            <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 0.5rem;">Charts & trade markers</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # The Upgrade Plan
    st.markdown('<div class="section-header">🚀 The Upgrade Plan</div>', unsafe_allow_html=True)
    
    st.code("""
┌─────────────────────────────────────────────────────────────────┐
│                        LOGIN SCREEN                             │
│                                                                 │
│                   👤 Username: [________]                       │
│                   🔒 Password: [________]                       │
│                         [Login]                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────┬─────────────────────────────────┐
│   SAUNDERS' DASHBOARD         │   SNOWY'S DASHBOARD             │
├───────────────────────────────┼─────────────────────────────────┤
│   📁 My Saved Strategies      │   📁 My Saved Strategies        │
│   📈 My Paper Trades          │   📈 My Paper Trades            │
│   📊 My Backtest History      │   📊 My Backtest History        │
│   ⚙️  My Settings              │   ⚙️  My Settings                │
└───────────────────────────────┴─────────────────────────────────┘
    """, language=None)
    
    # Phase cards
    phases = [
        ("1", "User Accounts & Authentication", "Secure login system so you and Snowy each have your own private dashboard. Your strategies, trades, and history are completely separate."),
        ("2", "Cloud Database", "Store everything in a proper database - saved strategies, backtest results, paper trades, and performance history. Access from any device."),
        ("3", "Paper Trading Bot", "Once you've found a winning strategy, activate paper trading. The bot runs daily/hourly, checks live prices, and executes fake trades following your rules."),
        ("4", "Notifications & Alerts", "Get email alerts when your strategy triggers a buy or sell signal. Stay informed without constantly checking the app."),
    ]
    
    for num, title, desc in phases:
        st.markdown(f"""
        <div style="display: flex; align-items: flex-start; gap: 1.5rem; padding: 1.5rem; 
                    background: rgba(59, 130, 246, 0.05); border-radius: 10px; margin-bottom: 1rem; 
                    border-left: 4px solid #3b82f6;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.5rem; font-weight: 700; 
                        color: #3b82f6; background: rgba(59, 130, 246, 0.1); width: 50px; height: 50px; 
                        border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                {num}
            </div>
            <div>
                <h3 style="font-size: 1.1rem; margin-bottom: 0.5rem; color: #f8fafc;">{title}</h3>
                <p style="color: #94a3b8; font-size: 0.95rem; margin: 0;">{desc}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # New Features
    st.markdown('<div class="section-header">✨ New Features</div>', unsafe_allow_html=True)
    
    feat_col1, feat_col2, feat_col3, feat_col4 = st.columns(4)
    features = [
        ("🔐", "Secure Login", "Username/password with encryption"),
        ("💾", "Save Strategies", "Name and save your best setups"),
        ("📜", "Backtest History", "Every run logged with results"),
        ("📈", "Paper Trading", "Simulate with $10k fake money"),
        ("🤖", "Daily Bot", "Automated checks & execution"),
        ("📧", "Email Alerts", "Get notified on signals"),
        ("📊", "Live Dashboard", "Track performance real-time"),
        ("🏆", "Leaderboard", "Compare with your partner"),
    ]
    
    for i, (icon, title, desc) in enumerate(features):
        col = [feat_col1, feat_col2, feat_col3, feat_col4][i % 4]
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{icon}</div>
                <div class="metric-label">{title}</div>
                <div style="color: #94a3b8; font-size: 0.8rem; margin-top: 0.5rem;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # Technology Stack
    st.markdown('<div class="section-header">🛠️ Technology Stack</div>', unsafe_allow_html=True)
    
    tech_data = [
        ("Database", "Supabase (PostgreSQL)", "FREE", "500MB storage, built-in auth"),
        ("Web App", "Streamlit Cloud", "FREE", "Already using this"),
        ("Paper Trading", "Alpaca API", "FREE", "Unlimited paper trades"),
        ("Daily Bot", "GitHub Actions", "FREE", "2,000 mins/month free"),
        ("Email Alerts", "Resend / Gmail", "FREE", "100 emails/day free"),
    ]
    
    tech_df = pd.DataFrame(tech_data, columns=["Component", "Technology", "Cost", "Notes"])
    st.dataframe(tech_df, use_container_width=True, hide_index=True)
    
    # Cost summary
    cost_col1, cost_col2, cost_col3 = st.columns(3)
    with cost_col1:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem 2rem; background: rgba(34, 197, 94, 0.05); 
                    border: 1px solid #22c55e; border-radius: 10px;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 2rem; font-weight: 700; color: #22c55e;">£0</div>
            <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 0.25rem;">Monthly Cost</div>
        </div>
        """, unsafe_allow_html=True)
    with cost_col2:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem 2rem; background: rgba(34, 197, 94, 0.05); 
                    border: 1px solid #22c55e; border-radius: 10px;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 2rem; font-weight: 700; color: #22c55e;">£0</div>
            <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 0.25rem;">Setup Cost</div>
        </div>
        """, unsafe_allow_html=True)
    with cost_col3:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem 2rem; background: rgba(34, 197, 94, 0.05); 
                    border: 1px solid #22c55e; border-radius: 10px;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 2rem; font-weight: 700; color: #22c55e;">∞</div>
            <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 0.25rem;">Paper Trades</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # Implementation Steps
    st.markdown('<div class="section-header">📅 Implementation Steps</div>', unsafe_allow_html=True)
    
    steps = [
        ("Step 1: Database Setup", "Create Supabase account, set up tables and authentication"),
        ("Step 2: Login & User Dashboards", "Add login page, connect to database, create personal dashboards"),
        ("Step 3: Paper Trading Bot", "Connect Alpaca, build daily bot, add live trade tracking"),
    ]
    
    for title, desc in steps:
        st.markdown(f"""
        <div style="padding: 1rem; border-left: 3px solid #3b82f6; margin-bottom: 0.75rem; background: rgba(59, 130, 246, 0.03);">
            <h4 style="color: #f8fafc; margin: 0 0 0.25rem 0; font-size: 1rem;">{title}</h4>
            <p style="color: #94a3b8; margin: 0; font-size: 0.9rem;">{desc}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # CTA
    st.markdown("""
    <div style="text-align: center; padding: 2rem; background: linear-gradient(145deg, rgba(59, 130, 246, 0.1) 0%, rgba(20, 184, 166, 0.1) 100%); 
                border-radius: 12px; border: 1px solid #3b82f6; margin-top: 2rem;">
        <h3 style="font-family: 'Press Start 2P', cursive; font-size: 0.75rem; color: #3b82f6; margin-bottom: 1rem;">Ready to Upgrade?</h3>
        <p style="color: #94a3b8; max-width: 600px; margin: 0 auto;">
            The first step is to create a free Supabase account. Once that's done, 
            we can start building the multi-user system and paper trading features.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div style="text-align: center; margin-top: 3rem; padding-top: 2rem; border-top: 1px solid #334155;">
        <div style="font-family: 'Press Start 2P', cursive; font-size: 0.6rem; color: #3b82f6; margin-bottom: 0.5rem;">S&S Analytics</div>
        <p style="color: #94a3b8; font-size: 0.8rem;">Snowy & Saunders © 2026</p>
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main application entry point."""
    
    # Header row with title, ticker selector, and run button
    header_col1, header_col2, header_col3, header_col4 = st.columns([3, 2, 1, 1])
    
    with header_col1:
        st.markdown("""
        <div style="padding: 0.5rem 0;">
            <span class="app-title">S&S Analytics</span>
            <span class="app-subtitle" style="margin-left: 1rem;">Pullback Strategy Backtester</span>
        </div>
        """, unsafe_allow_html=True)
    
    with header_col2:
        selected_ticker = st.selectbox(
            "Asset",
            options=list(AVAILABLE_TICKERS.keys()),
            format_func=lambda x: f"{x} - {AVAILABLE_TICKERS[x]}",
            index=0,
            label_visibility="collapsed"
        )
    
    with header_col3:
        run_button = st.button("🚀 Run", type="primary", use_container_width=True)
    
    with header_col4:
        if st.button("📋 Roadmap", use_container_width=True):
            st.session_state['page'] = 'roadmap'
            st.rerun()
    
    st.markdown("")  # Spacing
    
    # Preset buttons row
    preset_col1, preset_col2, preset_col3, preset_col4 = st.columns(4)
    
    # Initialize preset in session state
    if 'preset' not in st.session_state:
        st.session_state['preset'] = 'balanced'
    
    with preset_col1:
        if st.button("🐢 Conservative", use_container_width=True):
            st.session_state['preset'] = 'conservative'
            st.rerun()
    with preset_col2:
        if st.button("⚖️ Balanced", use_container_width=True):
            st.session_state['preset'] = 'balanced'
            st.rerun()
    with preset_col3:
        if st.button("🔥 Aggressive", use_container_width=True):
            st.session_state['preset'] = 'aggressive'
            st.rerun()
    with preset_col4:
        if st.button("📈 Trend", use_container_width=True):
            st.session_state['preset'] = 'trend'
            st.rerun()
    
    # Apply preset values
    preset = st.session_state['preset']
    preset_values = {
        'conservative': {'pullback': 10.0, 'stop_loss': 15.0, 'exit': 'ATH Recovery', 'rebound': 5.0, 'use_trend': True},
        'balanced': {'pullback': 5.0, 'stop_loss': 10.0, 'exit': 'Percent Rebound', 'rebound': 5.0, 'use_trend': False},
        'aggressive': {'pullback': 3.0, 'stop_loss': 8.0, 'exit': 'Percent Rebound', 'rebound': 3.0, 'use_trend': False},
        'trend': {'pullback': 5.0, 'stop_loss': 10.0, 'exit': 'ATH Recovery', 'rebound': 5.0, 'use_trend': True},
    }
    pv = preset_values.get(preset, preset_values['balanced'])
    
    st.markdown("")  # Spacing
    
    # Control cards row - 4 columns
    ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns(4)
    
    # ENTRY CARD
    with ctrl_col1:
        st.markdown('<div class="control-card"><div class="control-card-header">📥 Entry</div>', unsafe_allow_html=True)
        
        use_ath_entry = st.toggle("ATH Pullback", value=True, key="ath_entry")
        if use_ath_entry:
            pullback_pct = st.slider("% from ATH", 1.0, 30.0, pv['pullback'], 0.5, key="pullback")
        else:
            pullback_pct = 5.0
        
        use_atr_entry = st.toggle("ATR Pullback", value=False, key="atr_entry")
        if use_atr_entry:
            atr_entry_multiplier = st.slider("× ATR", 0.1, 5.0, 1.5, 0.1, key="atr_mult")
            col_a, col_b = st.columns(2)
            with col_a:
                ema_period = st.selectbox("EMA", [10, 20, 50, 100, 150, 200], index=1, key="ema")
            with col_b:
                atr_period = st.selectbox("ATR", [7, 10, 14, 20, 30], index=2, key="atr")
        else:
            atr_entry_multiplier = 1.5
            ema_period = 20
            atr_period = 14
        
        if not use_ath_entry and not use_atr_entry:
            st.warning("⚠️ Enable one")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # EXIT CARD
    with ctrl_col2:
        st.markdown('<div class="control-card"><div class="control-card-header">📤 Exit</div>', unsafe_allow_html=True)
        
        exit_options = ["ATH Recovery", "Percent Rebound", "ATR Rebound"]
        exit_idx = exit_options.index(pv['exit']) if pv['exit'] in exit_options else 0
        exit_option = st.radio("Mode", exit_options, index=exit_idx, key="exit_mode", label_visibility="collapsed")
        
        if exit_option == "ATH Recovery":
            exit_mode = ExitMode.ATH_RECOVERY
            rebound_pct = 5.0
            atr_exit_multiplier = 1.0
        elif exit_option == "Percent Rebound":
            exit_mode = ExitMode.PERCENT_REBOUND
            rebound_pct = st.slider("Rebound %", 1.0, 30.0, pv['rebound'], 0.5, key="rebound")
            atr_exit_multiplier = 1.0
        else:
            exit_mode = ExitMode.ATR_REBOUND
            atr_exit_multiplier = st.slider("× ATR", 0.1, 5.0, 1.0, 0.1, key="atr_exit")
            rebound_pct = 5.0
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # RISK CARD
    with ctrl_col3:
        st.markdown('<div class="control-card"><div class="control-card-header">🛡️ Risk</div>', unsafe_allow_html=True)
        
        stop_loss_pct = st.slider("Stop-Loss %", 1.0, 50.0, pv['stop_loss'], 0.5, key="stop_loss")
        cooloff = st.toggle("Cool-off after stop", value=False, key="cooloff")
        
        st.markdown("")
        initial_capital = st.number_input("Capital $", 1000, 10000000, 10000, 1000, key="capital")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # FILTERS & DATA CARD
    with ctrl_col4:
        st.markdown('<div class="control-card"><div class="control-card-header">📊 Filters & Data</div>', unsafe_allow_html=True)
        
        use_trend_filter = st.toggle("Trend Filter (MA rising)", value=pv['use_trend'], key="trend_filter")
        if use_trend_filter:
            col_a, col_b = st.columns(2)
            with col_a:
                trend_ma_period = st.selectbox("MA", [20, 50, 100, 150, 200], index=1, key="trend_ma")
            with col_b:
                trend_lookback = st.number_input("Days", 1, 20, 5, key="trend_lookback")
        else:
            trend_ma_period = 50
            trend_lookback = 5
        
        st.markdown("")
        data_source = st.radio("Data", ["Yahoo Finance", "Sample"], index=0, key="data_src", horizontal=True)
        
        if data_source == "Yahoo Finance":
            start_year = st.selectbox("From", list(range(2000, 2027)), index=10, key="start_year")
        else:
            start_year = 2010
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("")  # Spacing
    
    # Main content - Results
    if run_button or 'result' in st.session_state:
        
        if run_button:
            # Load data
            with st.spinner(f"Loading {selected_ticker} data..."):
                try:
                    if data_source == "Yahoo Finance":
                        df = get_ticker_data(selected_ticker, "download", f"{start_year}-01-01")
                    else:
                        sample_path = os.path.join(os.path.dirname(__file__), "data", "sample_qqq.csv")
                        if os.path.exists(sample_path):
                            df = get_ticker_data(selected_ticker, sample_path)
                        else:
                            st.error("Sample data file not found. Please use Yahoo download.")
                            return
                except Exception as e:
                    st.error(f"Error loading data: {str(e)}")
                    return
            
            # Store settings in session
            st.session_state['ticker'] = selected_ticker
            st.session_state['show_ema'] = use_atr_entry
            st.session_state['show_trend_ma'] = use_trend_filter
            
            # Configure backtest
            config = BacktestConfig(
                use_ath_entry=use_ath_entry,
                use_atr_entry=use_atr_entry,
                pullback_pct=pullback_pct,
                atr_entry_multiplier=atr_entry_multiplier,
                use_trend_filter=use_trend_filter,
                trend_ma_period=trend_ma_period,
                trend_lookback=trend_lookback,
                exit_mode=exit_mode,
                rebound_pct=rebound_pct,
                atr_exit_multiplier=atr_exit_multiplier,
                ema_period=ema_period,
                atr_period=atr_period,
                stop_loss_pct=stop_loss_pct,
                initial_capital=float(initial_capital),
                cooloff_after_stop=cooloff
            )
            
            # Run backtest
            with st.spinner("Running backtest..."):
                result = run_backtest(df, config)
                st.session_state['result'] = result
                st.session_state['df'] = df
        else:
            result = st.session_state['result']
            df = st.session_state['df']
            selected_ticker = st.session_state.get('ticker', 'QQQ')
        
        # Summary Metrics
        st.markdown('<div class="section-header">📊 Performance Summary</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            color = "positive" if result.total_return_pct > 0 else "negative"
            st.markdown(create_metric_card(
                "Total Return",
                format_percent(result.total_return_pct),
                color
            ), unsafe_allow_html=True)
            
            st.markdown(create_metric_card(
                "CAGR",
                format_percent(result.cagr, include_sign=False),
                color
            ), unsafe_allow_html=True)
        
        with col2:
            st.markdown(create_metric_card(
                "Final Equity",
                format_currency(result.final_equity),
                "positive" if result.final_equity > result.initial_capital else "negative"
            ), unsafe_allow_html=True)
            
            st.markdown(create_metric_card(
                "Max Drawdown",
                format_percent(-result.max_drawdown_pct, include_sign=False),
                "negative"
            ), unsafe_allow_html=True)
        
        with col3:
            st.markdown(create_metric_card(
                "Total Trades",
                str(result.total_trades),
                "neutral"
            ), unsafe_allow_html=True)
            
            st.markdown(create_metric_card(
                "Win Rate",
                format_percent(result.win_rate, include_sign=False),
                "positive" if result.win_rate > 50 else "warning"
            ), unsafe_allow_html=True)
        
        with col4:
            st.markdown(create_metric_card(
                "Avg Win",
                format_percent(result.avg_win_pct),
                "positive"
            ), unsafe_allow_html=True)
            
            st.markdown(create_metric_card(
                "Avg Loss",
                format_percent(result.avg_loss_pct),
                "negative"
            ), unsafe_allow_html=True)
        
        # Secondary metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(create_metric_card(
                "Profit Factor",
                f"{result.profit_factor:.2f}" if result.profit_factor != float('inf') else "∞",
                "positive" if result.profit_factor > 1 else "negative"
            ), unsafe_allow_html=True)
        
        with col2:
            st.markdown(create_metric_card(
                "Avg Days Held",
                f"{result.avg_days_held:.1f}",
                "neutral"
            ), unsafe_allow_html=True)
        
        with col3:
            st.markdown(create_metric_card(
                "Time in Market",
                format_percent(result.time_in_market_pct, include_sign=False),
                "neutral"
            ), unsafe_allow_html=True)
        
        with col4:
            st.markdown(create_metric_card(
                "Win/Loss",
                f"{result.winning_trades}/{result.losing_trades}",
                "positive" if result.winning_trades > result.losing_trades else "warning"
            ), unsafe_allow_html=True)
        
        # Charts
        st.markdown('<div class="section-header">📈 Charts</div>', unsafe_allow_html=True)
        
        show_ema = st.session_state.get('show_ema', False)
        show_trend_ma = st.session_state.get('show_trend_ma', False)
        equity_chart = create_equity_chart(result, df, selected_ticker, show_ema=show_ema, show_trend_ma=show_trend_ma)
        st.plotly_chart(equity_chart, use_container_width=True)
        
        # Additional charts
        col1, col2 = st.columns(2)
        
        with col1:
            yearly_chart = create_yearly_returns_chart(result)
            if yearly_chart:
                st.plotly_chart(yearly_chart, use_container_width=True)
        
        with col2:
            dist_chart = create_trade_distribution_chart(result)
            if dist_chart:
                st.plotly_chart(dist_chart, use_container_width=True)
        
        # Trade Log
        st.markdown('<div class="section-header">📋 Trade Log</div>', unsafe_allow_html=True)
        
        if result.trades:
            trade_data = []
            for i, t in enumerate(result.trades, 1):
                trade_data.append({
                    "#": i,
                    "Entry Date": t.entry_date.strftime("%Y-%m-%d"),
                    "Exit Date": t.exit_date.strftime("%Y-%m-%d"),
                    "Entry $": f"${t.entry_price:.2f}",
                    "Exit $": f"${t.exit_price:.2f}",
                    "P&L %": f"{t.pnl_percent:+.2f}%",
                    "P&L $": f"${t.pnl:+,.2f}",
                    "Days": t.days_held,
                    "MAE %": f"{t.max_adverse_excursion:.2f}%",
                    "Exit Reason": t.exit_reason.replace("_", " ").title()
                })
            
            trade_df = pd.DataFrame(trade_data)
            
            st.dataframe(
                trade_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "P&L %": st.column_config.TextColumn("P&L %"),
                    "P&L $": st.column_config.TextColumn("P&L $"),
                    "MAE %": st.column_config.TextColumn("Max Drawdown"),
                }
            )
        else:
            st.info("No trades were executed with these parameters.")
    
    else:
        # Show instructions when no backtest has been run
        st.markdown("""
        <div style="text-align: center; padding: 3rem 2rem; background: linear-gradient(145deg, #232a33 0%, #1a1f26 100%); border-radius: 12px; border: 1px solid #334155; margin: 1rem 0;">
            <p style="color: #94a3b8; font-size: 1rem; max-width: 600px; margin: 0 auto; font-family: 'Inter', sans-serif;">
                Configure your strategy using the controls above, then click <strong>🚀 Run</strong> to backtest.
            </p>
            <p style="color: #64748b; font-size: 0.85rem; margin-top: 1rem; font-family: 'Inter', sans-serif;">
                💡 Try a preset to get started quickly, or customize each parameter.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Strategy explanation - collapsed by default
        with st.expander("ℹ️ How the Strategy Works"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                **📥 Entry Signals** (Either/Or)
                - **ATH Pullback**: Enter when price drops X% from all-time high
                - **ATR Pullback**: Enter when price is X ATRs below EMA
                
                **📤 Exit Strategies**
                - **ATH Recovery**: Exit at previous ATH
                - **Percent Rebound**: Exit after X% gain
                - **ATR Rebound**: Exit after X ATRs rise
                """)
            with col2:
                st.markdown("""
                **🛡️ Risk Management**
                - **Stop-Loss**: Exit if position drops X%
                - **Cool-off**: Wait for new ATH after stop
                
                **📊 Trend Filter**
                - Only enter if MA is rising over X days
                - Helps avoid downtrend entries
                """)


if __name__ == "__main__":
    # Page routing
    if st.session_state.get('page', 'backtest') == 'roadmap':
        show_roadmap()
    else:
        main()
