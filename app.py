# AIModified:2026-01-11T14:57:01Z
"""
The Empire Buys Back - Pullback Strategy Backtesting Tool

A Streamlit application for backtesting pullback-based trading strategies.
May the profits be with you!
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
    "ARKK": "ARK Innovation ETF",
}


# Page configuration
st.set_page_config(
    page_title="The Empire Buys Back",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with Star Wars theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Orbitron:wght@400;500;600;700;800;900&family=Outfit:wght@300;400;600;700&display=swap');
    
    :root {
        --bg-primary: #000000;
        --bg-secondary: #0a0a0a;
        --bg-card: #1a1a2e;
        --accent-green: #00ff00;
        --accent-red: #ff0000;
        --accent-blue: #00d4ff;
        --accent-amber: #ffe81f;
        --accent-imperial: #ff4444;
        --text-primary: #ffe81f;
        --text-secondary: #8b8b8b;
        --border-color: #333355;
        --glow-yellow: rgba(255, 232, 31, 0.3);
    }
    
    .stApp {
        background: linear-gradient(180deg, #000000 0%, #0a0a1a 50%, #000000 100%);
        background-attachment: fixed;
    }
    
    .stApp::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(white 1px, transparent 1px),
            radial-gradient(white 1px, transparent 1px);
        background-size: 100px 100px, 50px 50px;
        background-position: 0 0, 25px 25px;
        opacity: 0.03;
        pointer-events: none;
        z-index: 0;
    }
    
    .main .block-container {
        padding-top: 2rem;
        max-width: 1400px;
        position: relative;
        z-index: 1;
    }
    
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important;
    }
    
    .star-wars-title {
        font-family: 'Orbitron', monospace !important;
        font-weight: 900 !important;
        font-size: 2.8rem !important;
        color: #ffe81f !important;
        text-shadow: 
            0 0 10px rgba(255, 232, 31, 0.5),
            0 0 20px rgba(255, 232, 31, 0.3),
            0 0 30px rgba(255, 232, 31, 0.2);
        letter-spacing: 0.15em;
        text-transform: uppercase;
    }
    
    .metric-card {
        background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #333355;
        border-radius: 8px;
        padding: 1.25rem;
        margin: 0.5rem 0;
        box-shadow: 
            0 4px 20px rgba(0, 0, 0, 0.5),
            inset 0 1px 0 rgba(255, 232, 31, 0.1);
    }
    
    .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.75rem;
        font-weight: 600;
        margin: 0.25rem 0;
    }
    
    .metric-label {
        font-family: 'Orbitron', sans-serif;
        font-size: 0.75rem;
        color: #8b8b8b;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    .positive { color: #00ff00 !important; text-shadow: 0 0 10px rgba(0, 255, 0, 0.3); }
    .negative { color: #ff4444 !important; text-shadow: 0 0 10px rgba(255, 68, 68, 0.3); }
    .neutral { color: #00d4ff !important; text-shadow: 0 0 10px rgba(0, 212, 255, 0.3); }
    .warning { color: #ffe81f !important; text-shadow: 0 0 10px rgba(255, 232, 31, 0.3); }
    
    .trade-table {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
    }
    
    .section-header {
        font-family: 'Orbitron', sans-serif;
        font-size: 1.3rem;
        font-weight: 600;
        color: #ffe81f;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #ffe81f;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        text-shadow: 0 0 10px rgba(255, 232, 31, 0.3);
    }
    
    /* Sidebar styling - Imperial theme */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0a0a 0%, #1a1a2e 50%, #0a0a0a 100%);
        border-right: 1px solid #333355;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #ffe81f;
    }
    
    /* Input styling */
    .stSlider > div > div {
        background-color: #1a1a2e;
    }
    
    .stNumberInput input {
        font-family: 'JetBrains Mono', monospace;
        background-color: #1a1a2e;
        color: #ffe81f;
        border: 1px solid #333355;
    }
    
    .stSelectbox > div > div {
        background-color: #1a1a2e;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(180deg, #ffe81f 0%, #ccb800 100%) !important;
        color: #000000 !important;
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: 0.1em !important;
        border: none !important;
        box-shadow: 0 0 20px rgba(255, 232, 31, 0.3) !important;
    }
    
    .stButton > button:hover {
        box-shadow: 0 0 30px rgba(255, 232, 31, 0.5) !important;
        transform: translateY(-1px);
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


def create_equity_chart(result, df, ticker: str = "QQQ"):
    """Create the main equity curve and price chart."""
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.5, 0.3, 0.2],
        subplot_titles=("Portfolio Equity", f"{ticker} Price with Trade Markers", "Drawdown")
    )
    
    # Equity curve - Imperial Green
    fig.add_trace(
        go.Scatter(
            x=result.equity_curve.index,
            y=result.equity_curve['Equity'],
            mode='lines',
            name='Imperial Credits',
            line=dict(color='#00ff00', width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 255, 0, 0.1)'
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
            line=dict(color='#00d4ff', width=1.5)
        ),
        row=2, col=1
    )
    
    # ATH line - Star Wars Yellow
    fig.add_trace(
        go.Scatter(
            x=result.equity_curve.index,
            y=result.equity_curve['ATH'],
            mode='lines',
            name='All-Time High',
            line=dict(color='#ffe81f', width=1, dash='dot'),
            opacity=0.7
        ),
        row=2, col=1
    )
    
    # Trade markers
    for trade in result.trades:
        # Entry marker - Green lightsaber
        fig.add_trace(
            go.Scatter(
                x=[trade.entry_date],
                y=[trade.entry_price],
                mode='markers',
                name='Buy',
                marker=dict(
                    symbol='triangle-up',
                    size=12,
                    color='#00ff00',
                    line=dict(color='#003300', width=1)
                ),
                showlegend=False,
                hovertemplate=f"⚔️ EXECUTE ORDER<br>Date: {trade.entry_date.strftime('%Y-%m-%d')}<br>Price: ${trade.entry_price:.2f}<extra></extra>"
            ),
            row=2, col=1
        )
        
        # Exit marker - Red (loss) or Green (win)
        exit_color = '#00ff00' if trade.is_win else '#ff4444'
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
                hovertemplate=f"🛡️ EXIT ({trade.exit_reason})<br>Date: {trade.exit_date.strftime('%Y-%m-%d')}<br>Price: ${trade.exit_price:.2f}<br>P&L: {trade.pnl_percent:+.2f}%<extra></extra>"
            ),
            row=2, col=1
        )
    
    # Drawdown chart - Imperial Red
    fig.add_trace(
        go.Scatter(
            x=result.equity_curve.index,
            y=result.equity_curve['Drawdown_Pct'],
            mode='lines',
            name='Dark Side Losses',
            line=dict(color='#ff4444', width=1.5),
            fill='tozeroy',
            fillcolor='rgba(255, 68, 68, 0.2)'
        ),
        row=3, col=1
    )
    
    # Update layout - Star Wars dark theme
    fig.update_layout(
        height=800,
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(10, 10, 26, 0.9)',
        font=dict(family="JetBrains Mono, monospace", color='#ffe81f'),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(26, 26, 46, 0.9)',
            font=dict(color='#ffe81f')
        ),
        margin=dict(l=60, r=20, t=80, b=40)
    )
    
    # Update axes - Star Wars grid
    fig.update_xaxes(
        gridcolor='rgba(51, 51, 85, 0.5)',
        showgrid=True,
        zeroline=False
    )
    fig.update_yaxes(
        gridcolor='rgba(51, 51, 85, 0.5)',
        showgrid=True,
        zeroline=False
    )
    
    fig.update_yaxes(title_text="Imperial Credits ($)", row=1, col=1)
    fig.update_yaxes(title_text="Price ($)", row=2, col=1)
    fig.update_yaxes(title_text="Dark Side (%)", row=3, col=1)
    
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
            color='#00d4ff',
            line=dict(color='#0088aa', width=1)
        ),
        opacity=0.8
    ))
    
    fig.update_layout(
        title="⚔️ Battle Outcomes Distribution",
        xaxis_title="Return (%)",
        yaxis_title="Frequency",
        height=350,
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(10, 10, 26, 0.9)',
        font=dict(family="JetBrains Mono, monospace", color='#ffe81f'),
        margin=dict(l=60, r=20, t=60, b=40)
    )
    
    fig.update_xaxes(gridcolor='rgba(51, 51, 85, 0.5)')
    fig.update_yaxes(gridcolor='rgba(51, 51, 85, 0.5)')
    
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
    
    # Green for wins, Red for losses - lightsaber colors
    colors = ['#00ff00' if r > 0 else '#ff4444' for r in yearly_returns.values]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=yearly_returns.index.year,
        y=yearly_returns.values,
        marker=dict(color=colors),
        text=[f"{v:+.1f}%" for v in yearly_returns.values],
        textposition='outside',
        textfont=dict(color='#ffe81f', size=10)
    ))
    
    fig.update_layout(
        title="📅 Galactic Year Returns",
        xaxis_title="Year",
        yaxis_title="Return (%)",
        height=350,
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(10, 10, 26, 0.9)',
        font=dict(family="JetBrains Mono, monospace", color='#ffe81f'),
        margin=dict(l=60, r=20, t=60, b=40)
    )
    
    fig.update_xaxes(gridcolor='rgba(51, 51, 85, 0.5)', dtick=1)
    fig.update_yaxes(gridcolor='rgba(51, 51, 85, 0.5)')
    
    return fig


def main():
    """Main application entry point."""
    
    # Header with Star Wars theme
    st.markdown("""
    <div style="text-align: center; padding: 1.5rem 0 2rem 0;">
        <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">⚔️</div>
        <h1 class="star-wars-title">The Empire Buys Back</h1>
        <p style="color: #8b8b8b; font-size: 1rem; font-family: 'Orbitron', sans-serif; letter-spacing: 0.2em; margin-top: 0.5rem;">
            MAY THE PROFITS BE WITH YOU
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar - Parameters
    with st.sidebar:
        st.markdown("## ⚙️ Imperial Controls")
        
        st.markdown("### 🎯 Target Asset")
        selected_ticker = st.selectbox(
            "Choose your target",
            options=list(AVAILABLE_TICKERS.keys()),
            format_func=lambda x: f"{x} - {AVAILABLE_TICKERS[x]}",
            index=0,
            help="Select the ETF/stock to backtest"
        )
        
        st.markdown("### 📥 Entry Conditions")
        pullback_pct = st.slider(
            "Pullback from ATH (%)",
            min_value=1.0,
            max_value=30.0,
            value=5.0,
            step=0.5,
            help="Enter a long position when price drops this much from all-time high"
        )
        
        st.markdown("### 📤 Exit Conditions")
        exit_mode = st.radio(
            "Exit Mode",
            options=["ATH Recovery", "Percent Rebound"],
            index=0,
            help="Choose when to exit: when price returns to ATH, or after gaining X%"
        )
        
        rebound_pct = 5.0
        if exit_mode == "Percent Rebound":
            rebound_pct = st.slider(
                "Rebound Target (%)",
                min_value=1.0,
                max_value=30.0,
                value=5.0,
                step=0.5,
                help="Exit when position gains this percentage"
            )
        
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
        
        st.markdown("### 💰 Capital")
        initial_capital = st.number_input(
            "Initial Capital ($)",
            min_value=1000,
            max_value=10000000,
            value=10000,
            step=1000
        )
        
        st.markdown("---")
        
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
        
        run_button = st.button("⚔️ EXECUTE ORDER", type="primary", use_container_width=True)
        
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0; opacity: 0.6;">
            <div style="font-size: 0.7rem; color: #8b8b8b; font-family: 'Orbitron', sans-serif; letter-spacing: 0.1em;">
                SNOWY & SAUNDERS<br/>TRADING CONSORTIUM
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content
    if run_button or 'result' in st.session_state:
        
        if run_button:
            # Load data
            with st.spinner(f"Acquiring {selected_ticker} intel from the Galactic Network..."):
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
            
            # Store ticker in session
            st.session_state['ticker'] = selected_ticker
            
            # Configure backtest
            config = BacktestConfig(
                pullback_pct=pullback_pct,
                stop_loss_pct=stop_loss_pct,
                exit_mode=ExitMode.ATH_RECOVERY if exit_mode == "ATH Recovery" else ExitMode.PERCENT_REBOUND,
                rebound_pct=rebound_pct,
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
        st.markdown('<div class="section-header">📊 Mission Report</div>', unsafe_allow_html=True)
        
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
        st.markdown('<div class="section-header">📈 Galactic Charts</div>', unsafe_allow_html=True)
        
        equity_chart = create_equity_chart(result, df, selected_ticker)
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
        st.markdown('<div class="section-header">📋 Imperial Trade Logs</div>', unsafe_allow_html=True)
        
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
        # Show instructions when no backtest has been run - Star Wars themed
        st.markdown("""
        <div style="text-align: center; padding: 4rem 2rem; background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%); border-radius: 8px; border: 1px solid #333355; margin: 2rem 0; box-shadow: 0 0 30px rgba(255, 232, 31, 0.1);">
            <h2 style="color: #ffe81f; margin-bottom: 1rem; font-family: 'Orbitron', sans-serif; letter-spacing: 0.1em;">⚔️ WELCOME, COMMANDER</h2>
            <p style="color: #8b8b8b; font-size: 1rem; max-width: 600px; margin: 0 auto 1.5rem auto; font-family: 'Outfit', sans-serif;">
                Configure your battle strategy in the Imperial Controls panel, then execute your order to analyse historical market data.
            </p>
            <div style="display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap; margin-top: 2rem;">
                <div style="text-align: center;">
                    <div style="font-size: 2rem;">🎯</div>
                    <div style="color: #8b8b8b; font-size: 0.8rem; font-family: 'Orbitron', sans-serif;">SELECT<br/>TARGET</div>
                </div>
                <div style="font-size: 2rem; color: #ffe81f;">→</div>
                <div style="text-align: center;">
                    <div style="font-size: 2rem;">📥</div>
                    <div style="color: #8b8b8b; font-size: 0.8rem; font-family: 'Orbitron', sans-serif;">SET<br/>ENTRY</div>
                </div>
                <div style="font-size: 2rem; color: #ffe81f;">→</div>
                <div style="text-align: center;">
                    <div style="font-size: 2rem;">🛡️</div>
                    <div style="color: #8b8b8b; font-size: 0.8rem; font-family: 'Orbitron', sans-serif;">DEFINE<br/>RISK</div>
                </div>
                <div style="font-size: 2rem; color: #ffe81f;">→</div>
                <div style="text-align: center;">
                    <div style="font-size: 2rem;">⚔️</div>
                    <div style="color: #8b8b8b; font-size: 0.8rem; font-family: 'Orbitron', sans-serif;">EXECUTE<br/>ORDER</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Strategy explanation
        with st.expander("📜 THE SACRED JEDI TEXTS (How the Strategy Works)", expanded=True):
            st.markdown("""
            ### The Pullback Strategy
            
            *"Do or do not buy the dip. There is no try."* - Yoda, probably
            
            This strategy is based on a simple observation: **Markets trend upward over time but frequently experience short-term pullbacks from all-time highs**.
            
            #### Entry Logic (When to Strike)
            - Track the **all-time high (ATH)** price
            - When price **pulls back X%** from ATH, enter a long position
            
            #### Exit Logic (Choose Your Path)
            - **ATH Recovery**: Exit when price returns to the previous ATH
            - **Percent Rebound**: Exit when price rebounds Y% from your entry price
            
            #### Risk Management (Protect the Empire)
            - If price drops **Z% below entry**, exit the trade (stop-loss)
            - Only **one position** at a time
            - **100% capital** deployed per trade (compounding)
            
            #### What This Tool Shows You
            - Historical performance of the strategy
            - Win rate, drawdowns, and risk metrics
            - Visual trade markers on price charts
            - Yearly returns breakdown
            """)


if __name__ == "__main__":
    main()

