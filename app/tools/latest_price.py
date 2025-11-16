import yfinance as yf
import pandas as pd
from pydantic import BaseModel, Field
from langchain.tools import tool


class LatestPriceInput(BaseModel):
    ticker: str = Field(..., description="The stock ticker symbol (e.g., 'AAPL', 'GOOGL').")

@tool(args_schema=LatestPriceInput)
def get_latest_price(ticker: str) -> str:
    """
    Fetches the latest (most recent) historical stock data (OHLCV) for a given ticker.
    This is for when a user asks "what is the price of apple" (singular).
    Returns a CSV string with only the MOST RECENT day's data.
    """
    try:
        stock = yf.Ticker(ticker)
        # Fetch 5 days to ensure we get the last trading day
        data = stock.history(period="5d", interval="1d", actions=False)

        if data.empty:
            return f"Error: No data found for ticker '{ticker}'. Please check if the ticker symbol is correct."

        # Remove timezone info if present
        if pd.api.types.is_datetime64_any_dtype(data.index) and data.index.tz is not None:
             data.index = data.index.tz_localize(None)

        # Select only OHLCV columns
        data = data[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
        
        # Round data for cleaner output
        data = data.round(2)
        
        # Return ONLY THE LAST ROW as a CSV string.
        # This keeps it consistent with our other tool.
        return data.tail(1).to_csv()

    except Exception as e:
        return f"Error: An unexpected error occurred while fetching data for {ticker}: {e}"