# AIModified:2026-01-29T14:37:59Z
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
    EntryMode,
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
    initial_sidebar_state="expanded"
)

# Professional CSS theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
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
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
    }
    
    .app-title {
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        font-size: 2.2rem !important;
        color: #f8fafc !important;
        letter-spacing: -0.02em;
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
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 500;
    }
    
    .positive { color: #22c55e !important; }
    .negative { color: #ef4444 !important; }
    .neutral { color: #3b82f6 !important; }
    .warning { color: #f59e0b !important; }
    
    .section-header {
        font-family: 'Inter', sans-serif;
        font-size: 1.25rem;
        font-weight: 600;
        color: #f8fafc;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #3b82f6;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1f26 0%, #0f1419 100%);
        border-right: 1px solid #334155;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #f8fafc;
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


def create_equity_chart(result, df, ticker: str = "QQQ", show_ema: bool = True):
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


def main():
    """Main application entry point."""
    
    # Header
    st.markdown("""
    <div style="text-align: center; padding: 1.5rem 0 2rem 0;">
        <div class="logo-container" style="justify-content: center; margin-bottom: 0.5rem;">
            <div class="logo-icon">📊</div>
        </div>
        <h1 class="app-title">S&S Analytics</h1>
        <p class="app-subtitle">Pullback Strategy Backtesting Platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar - Parameters
    with st.sidebar:
        st.markdown("## ⚙️ Strategy Parameters")
        
        # Asset Selection
        st.markdown("### 🎯 Asset Selection")
        selected_ticker = st.selectbox(
            "Select Asset",
            options=list(AVAILABLE_TICKERS.keys()),
            format_func=lambda x: f"{x} - {AVAILABLE_TICKERS[x]}",
            index=0,
            help="Select the ETF/stock to backtest"
        )
        
        st.markdown("---")
        
        # Entry Mode Toggle
        st.markdown("### 📥 Entry Strategy")
        
        use_atr_entry = st.toggle(
            "Use ATR-Based Entry",
            value=False,
            help="Toggle between ATH % pullback (off) and ATR-based entry (on)"
        )
        
        if use_atr_entry:
            # ATR-based entry controls
            st.markdown("**ATR Entry Settings**")
            
            atr_entry_multiplier = st.slider(
                "ATR Pullback (× ATR below EMA)",
                min_value=0.1,
                max_value=5.0,
                value=1.5,
                step=0.1,
                help="Enter when price is X ATRs below the EMA"
            )
            
            ema_period = st.select_slider(
                "EMA Period",
                options=[10, 20, 50, 100, 150, 200],
                value=20,
                help="Period for the Exponential Moving Average"
            )
            
            atr_period = st.select_slider(
                "ATR Period",
                options=[7, 10, 14, 20, 30],
                value=14,
                help="Period for Average True Range calculation"
            )
            
            # Set entry mode
            entry_mode = EntryMode.ATR_PULLBACK
            pullback_pct = 5.0  # Not used but needed for config
            use_ema_filter = False  # Not needed for ATR mode
            
        else:
            # ATH-based entry controls
            st.markdown("**ATH Pullback Settings**")
            
            pullback_pct = st.slider(
                "Pullback from ATH (%)",
                min_value=1.0,
                max_value=30.0,
                value=5.0,
                step=0.5,
                help="Enter when price drops this much from all-time high"
            )
            
            use_ema_filter = st.checkbox(
                "Require price below EMA",
                value=False,
                help="Only enter if price is also below the EMA"
            )
            
            if use_ema_filter:
                ema_period = st.select_slider(
                    "EMA Period",
                    options=[10, 20, 50, 100, 150, 200],
                    value=20,
                    help="Period for the Exponential Moving Average"
                )
            else:
                ema_period = 20  # Default
            
            atr_period = 14  # Default
            atr_entry_multiplier = 1.5  # Not used
            entry_mode = EntryMode.ATH_PULLBACK
        
        st.markdown("---")
        
        # Exit Mode Toggle
        st.markdown("### 📤 Exit Strategy")
        
        exit_option = st.radio(
            "Exit Mode",
            options=["ATH Recovery", "Percent Rebound", "ATR Rebound"],
            index=0,
            help="Choose when to exit the position"
        )
        
        if exit_option == "ATH Recovery":
            exit_mode = ExitMode.ATH_RECOVERY
            rebound_pct = 5.0
            atr_exit_multiplier = 1.0
            
        elif exit_option == "Percent Rebound":
            exit_mode = ExitMode.PERCENT_REBOUND
            rebound_pct = st.slider(
                "Rebound Target (%)",
                min_value=1.0,
                max_value=30.0,
                value=5.0,
                step=0.5,
                help="Exit when position gains this percentage"
            )
            atr_exit_multiplier = 1.0
            
        else:  # ATR Rebound
            exit_mode = ExitMode.ATR_REBOUND
            atr_exit_multiplier = st.slider(
                "ATR Rebound (× ATR from entry)",
                min_value=0.1,
                max_value=5.0,
                value=1.0,
                step=0.1,
                help="Exit when price rises X ATRs from entry price"
            )
            rebound_pct = 5.0
        
        st.markdown("---")
        
        # Risk Management
        st.markdown("### 🛡️ Risk Management")
        stop_loss_pct = st.slider(
            "Stop-Loss (%)",
            min_value=1.0,
            max_value=50.0,
            value=10.0,
            step=0.5,
            help="Exit if position drops this much from entry"
        )
        
        cooloff = st.checkbox(
            "Cool-off after stop-loss",
            value=False,
            help="Wait for new ATH before re-entering after a stop-loss"
        )
        
        st.markdown("---")
        
        # Capital
        st.markdown("### 💰 Capital")
        initial_capital = st.number_input(
            "Initial Capital ($)",
            min_value=1000,
            max_value=10000000,
            value=10000,
            step=1000
        )
        
        st.markdown("---")
        
        # Data Source
        st.markdown("### 📊 Data Source")
        data_source = st.radio(
            "Data Source",
            options=["Download from Yahoo", "Sample Data"],
            index=0
        )
        
        if data_source == "Download from Yahoo":
            start_year = st.selectbox(
                "Start Year",
                options=list(range(2000, 2027)),
                index=10  # 2010
            )
        
        run_button = st.button("🚀 Run Backtest", type="primary", use_container_width=True)
        
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0; opacity: 0.6;">
            <div style="font-size: 0.75rem; color: #94a3b8;">
                S&S Analytics<br/>
                <span style="font-size: 0.65rem;">Snowy & Saunders</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content
    if run_button or 'result' in st.session_state:
        
        if run_button:
            # Load data
            with st.spinner(f"Loading {selected_ticker} data..."):
                try:
                    if data_source == "Download from Yahoo":
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
            st.session_state['show_ema'] = use_atr_entry or use_ema_filter
            
            # Configure backtest
            config = BacktestConfig(
                entry_mode=entry_mode,
                pullback_pct=pullback_pct,
                atr_entry_multiplier=atr_entry_multiplier,
                exit_mode=exit_mode,
                rebound_pct=rebound_pct,
                atr_exit_multiplier=atr_exit_multiplier,
                ema_period=ema_period,
                use_ema_filter=use_ema_filter,
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
        equity_chart = create_equity_chart(result, df, selected_ticker, show_ema=show_ema)
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
        <div style="text-align: center; padding: 4rem 2rem; background: linear-gradient(145deg, #232a33 0%, #1a1f26 100%); border-radius: 12px; border: 1px solid #334155; margin: 2rem 0;">
            <h2 style="color: #f8fafc; margin-bottom: 1rem; font-family: 'Inter', sans-serif;">Welcome to S&S Analytics</h2>
            <p style="color: #94a3b8; font-size: 1rem; max-width: 600px; margin: 0 auto 1.5rem auto; font-family: 'Inter', sans-serif;">
                Configure your strategy parameters in the sidebar, then click <strong>Run Backtest</strong> to analyse historical performance.
            </p>
            <div style="display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap; margin-top: 2rem;">
                <div style="text-align: center;">
                    <div style="font-size: 2rem;">🎯</div>
                    <div style="color: #94a3b8; font-size: 0.85rem;">Select<br/>Asset</div>
                </div>
                <div style="font-size: 2rem; color: #3b82f6;">→</div>
                <div style="text-align: center;">
                    <div style="font-size: 2rem;">📥</div>
                    <div style="color: #94a3b8; font-size: 0.85rem;">Set Entry<br/>Conditions</div>
                </div>
                <div style="font-size: 2rem; color: #3b82f6;">→</div>
                <div style="text-align: center;">
                    <div style="font-size: 2rem;">🛡️</div>
                    <div style="color: #94a3b8; font-size: 0.85rem;">Define<br/>Risk</div>
                </div>
                <div style="font-size: 2rem; color: #3b82f6;">→</div>
                <div style="text-align: center;">
                    <div style="font-size: 2rem;">🚀</div>
                    <div style="color: #94a3b8; font-size: 0.85rem;">Run<br/>Backtest</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Strategy explanation
        with st.expander("ℹ️ How the Strategy Works", expanded=True):
            st.markdown("""
            ### Entry Strategies
            
            **ATH Pullback Mode** (Default)
            - Track the **all-time high (ATH)** price
            - When price **pulls back X%** from ATH, enter a long position
            - Optional: Only enter if price is also below the EMA
            
            **ATR Pullback Mode** (Toggle on)
            - Calculate the **Exponential Moving Average (EMA)**
            - When price drops **X ATRs below the EMA**, enter a long position
            - ATR (Average True Range) measures volatility
            
            ### Exit Strategies
            
            - **ATH Recovery**: Exit when price returns to the previous ATH
            - **Percent Rebound**: Exit when price rebounds Y% from entry
            - **ATR Rebound**: Exit when price rises Y ATRs from entry
            
            ### Risk Management
            
            - **Stop-Loss**: Exit if price drops Z% below entry
            - **Cool-off**: Optionally wait for new ATH after stop-loss
            - **Single Position**: Only one position at a time
            """)


if __name__ == "__main__":
    main()
