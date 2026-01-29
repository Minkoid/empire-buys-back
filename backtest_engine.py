# AIModified:2026-01-29T15:22:18Z
"""
S&S Analytics - Pullback Strategy Backtesting Engine

Core backtesting logic for simulating pullback-and-rebound strategies.
Supports ATH-based, ATR-based, and EMA-relative entry/exit modes.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Literal
from enum import Enum


class ExitMode(Enum):
    """Exit strategy options."""
    ATH_RECOVERY = "ath_recovery"  # Exit when price returns to ATH
    PERCENT_REBOUND = "percent_rebound"  # Exit when price rebounds Y% from entry
    ATR_REBOUND = "atr_rebound"  # Exit when price rebounds Y ATRs from entry


class EntryMode(Enum):
    """Entry strategy options - kept for backwards compatibility."""
    ATH_PULLBACK = "ath_pullback"  # Enter on % pullback from ATH
    ATR_PULLBACK = "atr_pullback"  # Enter on ATR pullback from EMA
    EITHER = "either"  # Enter on either condition (OR logic)


@dataclass
class Trade:
    """Represents a single completed trade."""
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    entry_price: float
    exit_price: float
    shares: float
    pnl: float
    pnl_percent: float
    is_win: bool
    exit_reason: str  # 'target', 'stop_loss', 'end_of_data'
    max_adverse_excursion: float  # Maximum drawdown during the trade
    days_held: int


@dataclass
class BacktestResult:
    """Complete results from a backtest run."""
    trades: List[Trade]
    equity_curve: pd.DataFrame  # Date, Equity, Drawdown, EMA, ATR
    
    # Summary metrics
    initial_capital: float
    final_equity: float
    total_return_pct: float
    cagr: float
    max_drawdown_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win_pct: float
    avg_loss_pct: float
    profit_factor: float
    avg_days_held: float
    
    # Time in market
    days_in_market: int
    total_days: int
    time_in_market_pct: float


@dataclass
class BacktestConfig:
    """Configuration parameters for the backtest."""
    # Entry toggles - either/or logic (enter if ANY enabled condition is met)
    use_ath_entry: bool = True  # Enable ATH pullback entry
    use_atr_entry: bool = False  # Enable ATR-based entry
    
    # ATH-based entry settings
    pullback_pct: float = 5.0  # Enter when price drops X% from ATH
    
    # ATR-based entry settings
    atr_entry_multiplier: float = 1.5  # Enter when price is X ATRs below EMA
    
    # Trend filter - only enter if MA is rising
    use_trend_filter: bool = False  # Only enter if trend MA is rising
    trend_ma_period: int = 50  # Period for trend moving average
    trend_lookback: int = 5  # Days to compare for "rising" check
    
    # Exit mode
    exit_mode: ExitMode = ExitMode.ATH_RECOVERY
    
    # Percent rebound exit
    rebound_pct: float = 5.0  # Exit at Y% gain from entry
    
    # ATR rebound exit
    atr_exit_multiplier: float = 1.0  # Exit when price rises Y ATRs from entry
    
    # EMA settings
    ema_period: int = 20  # EMA period for ATR-based strategies
    
    # ATR settings
    atr_period: int = 14  # ATR calculation period
    
    # Risk management
    stop_loss_pct: float = 10.0  # Exit if price drops Z% below entry
    initial_capital: float = 10000.0
    cooloff_after_stop: bool = False  # Wait for new ATH after stop-loss


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range (ATR).
    
    Args:
        df: DataFrame with High, Low, Close columns
        period: ATR period (default 14)
        
    Returns:
        Series with ATR values
    """
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    # True Range components
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    # True Range is max of the three
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # ATR is EMA of True Range
    atr = true_range.ewm(span=period, adjust=False).mean()
    
    return atr


def calculate_ema(series: pd.Series, period: int = 20) -> pd.Series:
    """
    Calculate Exponential Moving Average.
    
    Args:
        series: Price series
        period: EMA period
        
    Returns:
        Series with EMA values
    """
    return series.ewm(span=period, adjust=False).mean()


def run_backtest(df: pd.DataFrame, config: BacktestConfig) -> BacktestResult:
    """
    Run the pullback strategy backtest on historical data.
    
    Args:
        df: DataFrame with 'Date', 'Open', 'High', 'Low', 'Close' columns
        config: Backtest configuration parameters
        
    Returns:
        BacktestResult with trades, equity curve, and summary metrics
    """
    # Prepare data
    df = df.copy()
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date')
    df = df.sort_index()
    
    # Calculate indicators
    df['EMA'] = calculate_ema(df['Close'], config.ema_period)
    df['ATR'] = calculate_atr(df, config.atr_period)
    df['Trend_MA'] = calculate_ema(df['Close'], config.trend_ma_period)
    
    # Initialize tracking variables
    capital = config.initial_capital
    ath = df['Close'].iloc[0]
    
    in_position = False
    entry_price = 0.0
    entry_date = None
    entry_atr = 0.0  # ATR at entry for ATR-based exits
    shares = 0.0
    ath_at_entry = 0.0
    max_adverse_excursion = 0.0
    waiting_for_new_ath = False
    
    trades: List[Trade] = []
    equity_history = []
    
    # Skip initial rows where indicators aren't ready
    start_idx = max(config.ema_period, config.atr_period)
    
    for i, (date, row) in enumerate(df.iterrows()):
        price = row['Close']
        ema = row['EMA']
        atr = row['ATR']
        
        # Update ATH
        if price > ath:
            ath = price
            waiting_for_new_ath = False
        
        # Track equity
        if in_position:
            current_equity = shares * price
        else:
            current_equity = capital
        
        trend_ma = row['Trend_MA']
        
        equity_history.append({
            'Date': date,
            'Equity': current_equity,
            'Price': price,
            'ATH': ath,
            'EMA': ema,
            'ATR': atr,
            'Trend_MA': trend_ma,
            'In_Position': in_position
        })
        
        # Skip trading logic until indicators are ready
        if i < start_idx:
            continue
        
        if pd.isna(atr) or pd.isna(ema) or pd.isna(trend_ma):
            continue
        
        if in_position:
            # Check for exit conditions
            current_pnl_pct = (price - entry_price) / entry_price * 100
            
            # Track max adverse excursion (worst drawdown during trade)
            if current_pnl_pct < max_adverse_excursion:
                max_adverse_excursion = current_pnl_pct
            
            exit_triggered = False
            exit_reason = ''
            
            # Stop-loss check (always applies)
            if current_pnl_pct <= -config.stop_loss_pct:
                exit_triggered = True
                exit_reason = 'stop_loss'
                if config.cooloff_after_stop:
                    waiting_for_new_ath = True
            
            # Target exit check based on exit mode
            elif config.exit_mode == ExitMode.ATH_RECOVERY:
                if price >= ath_at_entry:
                    exit_triggered = True
                    exit_reason = 'target'
                    
            elif config.exit_mode == ExitMode.PERCENT_REBOUND:
                if current_pnl_pct >= config.rebound_pct:
                    exit_triggered = True
                    exit_reason = 'target'
                    
            elif config.exit_mode == ExitMode.ATR_REBOUND:
                # Exit when price rises X ATRs from entry
                atr_move = (price - entry_price) / entry_atr if entry_atr > 0 else 0
                if atr_move >= config.atr_exit_multiplier:
                    exit_triggered = True
                    exit_reason = 'target'
            
            if exit_triggered:
                # Close position
                exit_price = price
                pnl = shares * (exit_price - entry_price)
                pnl_pct = (exit_price - entry_price) / entry_price * 100
                
                trade = Trade(
                    entry_date=entry_date,
                    exit_date=date,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    shares=shares,
                    pnl=pnl,
                    pnl_percent=pnl_pct,
                    is_win=pnl > 0,
                    exit_reason=exit_reason,
                    max_adverse_excursion=max_adverse_excursion,
                    days_held=(date - entry_date).days
                )
                trades.append(trade)
                
                capital = shares * exit_price
                in_position = False
                shares = 0.0
        
        else:
            # Check for entry condition
            if waiting_for_new_ath:
                continue
            
            entry_signal = False
            
            # Check entry signals - either/or logic
            ath_signal = False
            atr_signal = False
            
            # ATH pullback check
            if config.use_ath_entry:
                pullback_pct_val = (ath - price) / ath * 100
                if pullback_pct_val >= config.pullback_pct:
                    ath_signal = True
            
            # ATR pullback check
            if config.use_atr_entry and atr > 0:
                atr_distance = (ema - price) / atr
                if atr_distance >= config.atr_entry_multiplier:
                    atr_signal = True
            
            # Check if either entry signal triggered
            if ath_signal or atr_signal:
                # Apply trend filter if enabled
                if config.use_trend_filter:
                    # Check if trend MA is rising (compare to X days ago)
                    lookback_idx = max(0, i - config.trend_lookback)
                    trend_ma_prev = df['Trend_MA'].iloc[lookback_idx]
                    if not pd.isna(trend_ma_prev) and trend_ma > trend_ma_prev:
                        entry_signal = True  # Trend is rising, allow entry
                    # else: trend not rising, don't enter
                else:
                    entry_signal = True  # No trend filter, allow entry
            
            if entry_signal:
                # Enter position
                entry_price = price
                entry_date = date
                entry_atr = atr  # Store ATR at entry for ATR-based exits
                shares = capital / price
                ath_at_entry = ath
                max_adverse_excursion = 0.0
                in_position = True
    
    # Close any open position at end of data
    if in_position:
        final_price = df['Close'].iloc[-1]
        final_date = df.index[-1]
        pnl = shares * (final_price - entry_price)
        pnl_pct = (final_price - entry_price) / entry_price * 100
        
        trade = Trade(
            entry_date=entry_date,
            exit_date=final_date,
            entry_price=entry_price,
            exit_price=final_price,
            shares=shares,
            pnl=pnl,
            pnl_percent=pnl_pct,
            is_win=pnl > 0,
            exit_reason='end_of_data',
            max_adverse_excursion=max_adverse_excursion,
            days_held=(final_date - entry_date).days
        )
        trades.append(trade)
        capital = shares * final_price
    
    # Build equity curve DataFrame
    equity_df = pd.DataFrame(equity_history)
    equity_df['Date'] = pd.to_datetime(equity_df['Date'])
    equity_df = equity_df.set_index('Date')
    
    # Calculate drawdown
    equity_df['Peak'] = equity_df['Equity'].cummax()
    equity_df['Drawdown_Pct'] = (equity_df['Equity'] - equity_df['Peak']) / equity_df['Peak'] * 100
    
    # Calculate summary metrics
    final_equity = capital
    total_return_pct = (final_equity - config.initial_capital) / config.initial_capital * 100
    
    # CAGR
    total_days = (df.index[-1] - df.index[0]).days
    years = total_days / 365.25
    if years > 0 and final_equity > 0:
        cagr = (pow(final_equity / config.initial_capital, 1 / years) - 1) * 100
    else:
        cagr = 0.0
    
    max_drawdown_pct = abs(equity_df['Drawdown_Pct'].min())
    
    total_trades = len(trades)
    winning_trades = sum(1 for t in trades if t.is_win)
    losing_trades = total_trades - winning_trades
    
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
    
    wins = [t.pnl_percent for t in trades if t.is_win]
    losses = [t.pnl_percent for t in trades if not t.is_win]
    
    avg_win_pct = np.mean(wins) if wins else 0.0
    avg_loss_pct = np.mean(losses) if losses else 0.0
    
    total_wins = sum(t.pnl for t in trades if t.is_win)
    total_losses = abs(sum(t.pnl for t in trades if not t.is_win))
    profit_factor = (total_wins / total_losses) if total_losses > 0 else float('inf')
    
    avg_days_held = np.mean([t.days_held for t in trades]) if trades else 0.0
    
    days_in_market = sum(t.days_held for t in trades)
    time_in_market_pct = (days_in_market / total_days * 100) if total_days > 0 else 0.0
    
    return BacktestResult(
        trades=trades,
        equity_curve=equity_df,
        initial_capital=config.initial_capital,
        final_equity=final_equity,
        total_return_pct=total_return_pct,
        cagr=cagr,
        max_drawdown_pct=max_drawdown_pct,
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        win_rate=win_rate,
        avg_win_pct=avg_win_pct,
        avg_loss_pct=avg_loss_pct,
        profit_factor=profit_factor,
        avg_days_held=avg_days_held,
        days_in_market=days_in_market,
        total_days=total_days,
        time_in_market_pct=time_in_market_pct
    )


def load_data_from_csv(filepath: str) -> pd.DataFrame:
    """Load price data from a CSV file."""
    df = pd.read_csv(filepath, parse_dates=['Date'])
    return df


def download_ticker_data(ticker_symbol: str = "QQQ", start_date: str = "2000-01-01", end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Download historical data for any ticker using yfinance.
    
    Args:
        ticker_symbol: The ticker symbol to download (e.g., QQQ, SPY, DIA)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (defaults to today)
        
    Returns:
        DataFrame with Date, Open, High, Low, Close, Volume columns
    """
    import yfinance as yf
    
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(start=start_date, end=end_date)
    df = df.reset_index()
    df = df.rename(columns={'index': 'Date'})
    df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
    
    return df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]


# Keep old function name for backwards compatibility
def download_qqq_data(start_date: str = "2000-01-01", end_date: Optional[str] = None) -> pd.DataFrame:
    """Backwards compatible wrapper for download_ticker_data."""
    return download_ticker_data("QQQ", start_date, end_date)
