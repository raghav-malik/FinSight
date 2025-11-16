import pandas as pd
import numpy as np
from pydantic import BaseModel, Field
from langchain.tools import tool
from typing import List, Optional
from io import StringIO


def sma(series: pd.Series, window: int) -> pd.Series:
    """Calculates Simple Moving Average (SMA)"""
    return series.rolling(window=window, min_periods=1).mean()

def ema(series: pd.Series, span: int) -> pd.Series:
    """Calculates Exponential Moving Average (EMA)"""
    return series.ewm(span=span, adjust=False).mean()

def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """Calculates Relative Strength Index (RSI)"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0.0)).fillna(0.0)
    loss = (-delta.where(delta < 0, 0.0)).fillna(0.0)
    avg_gain = gain.ewm(alpha=1.0/window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0/window, adjust=False).mean()
    rs = avg_gain / (avg_loss.replace(0, np.nan))
    rsi_series = 100 - (100 / (1 + rs))
    return rsi_series.fillna(50.0)  # Fill initial NaNs with 50 (neutral)


class IndicatorInput(BaseModel):
    data_csv: str = Field(..., description="The CSV string of historical data, typically from `get_historical_data`.")
    sma_windows: Optional[List[int]] = Field(None, description="List of windows for SMA (e.g., [20, 50]).")
    ema_spans: Optional[List[int]] = Field(None, description="List of spans for EMA (e.g., [20]).")
    rsi_windows: Optional[List[int]] = Field(None, description="List of windows for RSI (e.g., [14]).")

@tool(args_schema=IndicatorInput)
def calculate_technical_indicators(
    data_csv: str, 
    sma_windows: Optional[List[int]] = None, 
    ema_spans: Optional[List[int]] = None, 
    rsi_windows: Optional[List[int]] = None
) -> str:
    """
    Calculates technical indicators (SMA, EMA, RSI) from a CSV string of stock data.
    
    This tool takes the CSV output from 'get_historical_data' and adds new columns 
    for each requested indicator.
    
    Returns the new, enhanced data as a CSV string.
    """
    try:
        # 1. Convert the CSV string back into a DataFrame
        # Use index_col=0 to handle the first column (Date) as index
        df = pd.read_csv(StringIO(data_csv), index_col=0, parse_dates=True)
        
        if df.empty:
            return "Error: Input CSV is empty."
        
        if 'Close' not in df.columns:
            return f"Error: Input CSV must contain a 'Close' column. Found columns: {list(df.columns)}"
            
        out_df = df.copy()

        # 2. Calculate requested indicators and add them as new columns
        if sma_windows:
            for w in sma_windows:
                out_df[f'SMA_{w}'] = sma(out_df['Close'], w)
        
        if ema_spans:
            for s in ema_spans:
                out_df[f'EMA_{s}'] = ema(out_df['Close'], s)
        
        if rsi_windows:
            for r in rsi_windows:
                out_df[f'RSI_{r}'] = rsi(out_df['Close'], r)

        # 3. Round all data for clean output
        out_df = out_df.round(2)
        
        # 4. Convert the new DataFrame back to a CSV string
        return out_df.to_csv()
        
    except Exception as e:
        return f"Error during indicator calculation: {str(e)}"