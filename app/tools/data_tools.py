import yfinance as yf
import pandas as pd
from typing import Literal
from pydantic import BaseModel, Field
from langchain.tools import tool


class HistoricalDataInput(BaseModel):
    ticker: str = Field(..., description="The stock ticker symbol (e.g., 'AAPL', 'GOOGL').")
    period: str = Field(..., description="The period to fetch data for. Examples: '1d', '5d', '15d', '1mo', '3mo', '1y', 'ytd', 'max'.")
    interval: Literal['1d', '5d', '1wk', '1mo', '3mo'] = Field(
        default='1d', description="The data interval (e.g., '1d' for daily)."
    )
    
@tool(args_schema=HistoricalDataInput)
def get_historical_data(
    ticker: str, 
    period: str,
    interval: Literal['1d', '5d', '1wk', '1mo', '3mo'] = '1d'
) -> str:
    """
    Fetches historical stock data (OHLCV) for a given ticker, period, and interval.
    Returns a CSV string with columns: Date, Open, High, Low, Close, Volume.
    """
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period, interval=interval, actions=False)

        if data.empty:
            return f"Error: No data found for ticker '{ticker}' for period '{period}'. Please check if the ticker symbol is correct."

        # Remove timezone info if present
        if pd.api.types.is_datetime64_any_dtype(data.index) and data.index.tz is not None:
            data.index = data.index.tz_localize(None)

        # Select only OHLCV columns
        data = data[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
        
        # Round data for cleaner output
        data = data.round(2)
        
        # OPTIMIZATION: If data is too large (>100 rows), return summary + limited data
        if len(data) > 100:
            summary = f"Retrieved {len(data)} rows from {data.index[0]} to {data.index[-1]}\n"
            summary += f"Latest Close: ${data['Close'].iloc[-1]:.2f}\n"
            summary += f"Period High: ${data['High'].max():.2f}, Low: ${data['Low'].min():.2f}\n\n"
            # Only return last 50 rows + first 10 rows
            limited_data = pd.concat([data.head(10), data.tail(50)])
            return summary + limited_data.to_csv()
        
        # Return as CSV string for smaller datasets
        return data.to_csv()

    except Exception as e:
        return f"Error: An unexpected error occurred while fetching data for {ticker}: {e}"