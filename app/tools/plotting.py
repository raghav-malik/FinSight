import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pydantic import BaseModel, Field
from langchain.tools import tool
from io import StringIO
import os
import time
import glob


def cleanup_old_charts(charts_dir: str, max_age_hours: int = 1):
    """
    Remove chart files older than max_age_hours to prevent disk space issues.
    This is called automatically when creating new charts.

    Args:
        charts_dir: Directory containing chart files
        max_age_hours: Maximum age of charts in hours (default: 1 hour)
    """
    try:
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600

        # Find all PNG files in the charts directory
        chart_files = glob.glob(os.path.join(charts_dir, "chart_*.png"))

        deleted_count = 0
        for filepath in chart_files:
            # Check file age
            file_age = current_time - os.path.getmtime(filepath)
            if file_age > max_age_seconds:
                try:
                    os.remove(filepath)
                    deleted_count += 1
                except Exception as e:
                    print(f"Warning: Could not delete old chart {filepath}: {e}")

        if deleted_count > 0:
            print(f"Cleaned up {deleted_count} old chart file(s)")

    except Exception as e:
        print(f"Warning: Chart cleanup failed: {e}")


class PlotInput(BaseModel):
    data_csv: str = Field(..., description="The CSV string of historical data, typically from `get_historical_data` or `calculate_technical_indicators`.")
    ticker: str = Field(..., description="The ticker symbol (e.g., 'AAPL') for the plot title.")
    plot_title: str = Field(..., description="A descriptive title for the plot, e.g., 'AAPL with 20-Day SMA'.")

@tool(args_schema=PlotInput)
def create_stock_plot(data_csv: str, ticker: str, plot_title: str) -> str:
    """
    Creates a plot of stock data and saves it as a PNG file.
    This tool takes the CSV output from 'get_historical_data' or
    'calculate_technical_indicators' and generates a chart.

    The tool plots EVERY column it is given (except 'Volume'),
    so it will automatically plot 'SMA_20', 'RSI_14', etc., if they are in the CSV.

    RSI indicators get their own subplot with overbought (70) and oversold (30) lines.

    Returns a special marker with the chart filename that your frontend can parse to display the image.
    This is much more efficient than base64 encoding and prevents token limit issues.
    """
    try:
        # 1. Convert the CSV string back into a DataFrame
        df = pd.read_csv(StringIO(data_csv), index_col=0, parse_dates=True)
        
        if df.empty:
            return "Error: Cannot plot empty data."
            
        # 2. Determine which columns to plot
        # Plot every column except 'Volume'
        plot_cols = [col for col in df.columns if col.lower() != 'volume']
        
        # Check if we have RSI, which needs a separate subplot
        rsi_cols = [col for col in plot_cols if col.lower().startswith('rsi')]
        price_cols = [col for col in plot_cols if not col.lower().startswith('rsi')]
        
        num_subplots = 2 if rsi_cols else 1
        
        # 3. Create the plot
        fig, axes = plt.subplots(
            num_subplots, 
            1, 
            figsize=(14, 7), 
            sharex=True, 
            gridspec_kw={'height_ratios': [3, 1] if num_subplots == 2 else [1]}
        )
        
        # Ensure 'axes' is always a list
        if num_subplots == 1:
            axes = [axes]
            
        ax_price = axes[0]
        
        # Plot all price-related columns
        df[price_cols].plot(ax=ax_price, legend=True, linewidth=2)
        ax_price.set_title(f"{ticker}: {plot_title}", fontsize=16, fontweight='bold')
        ax_price.set_ylabel("Price ($)", fontsize=12)
        ax_price.grid(True, alpha=0.3)
        ax_price.legend(loc='best', fontsize=10)
        
        # Plot RSI on a separate axis if it exists
        if rsi_cols:
            ax_rsi = axes[1]
            # Plot the first RSI column found
            df[rsi_cols[0]].plot(ax=ax_rsi, legend=True, color='purple', linewidth=2)
            ax_rsi.set_ylabel("RSI", fontsize=12)
            ax_rsi.set_ylim(0, 100)
            ax_rsi.axhline(70, color='red', linestyle='--', linewidth=1, alpha=0.7, label='Overbought (70)')
            ax_rsi.axhline(30, color='green', linestyle='--', linewidth=1, alpha=0.7, label='Oversold (30)')
            ax_rsi.axhline(50, color='gray', linestyle=':', linewidth=0.8, alpha=0.5)
            ax_rsi.legend(loc='best', fontsize=9)
            ax_rsi.grid(True, alpha=0.3)
        
        # Format the x-axis
        axes[-1].set_xlabel("Date", fontsize=12)
        axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.xticks(rotation=45)
        plt.tight_layout()

        # 4. Save the plot to a file (much more efficient than base64)
        # Generate unique filename using timestamp
        timestamp = int(time.time() * 1000)  # milliseconds for uniqueness
        filename = f"chart_{ticker}_{timestamp}.png"

        # Save to frontend/charts directory
        charts_dir = os.path.join(os.path.dirname(__file__), '../../frontend/charts')
        os.makedirs(charts_dir, exist_ok=True)

        # Clean up old charts to prevent disk space issues (keeps charts for 1 hour)
        cleanup_old_charts(charts_dir, max_age_hours=1)

        filepath = os.path.join(charts_dir, filename)

        # Save the figure
        fig.savefig(filepath, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)  # Close the figure to free up memory

        # 5. Return a special marker with the chart path
        # This is much more efficient than base64 and prevents token limit issues
        return f"[CHART_FILE]/charts/{filename}[/CHART_FILE]"

    except Exception as e:
        return f"Error during plot generation: {str(e)}"