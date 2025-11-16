# FinSight – AI Financial Analyst Agent

FinSight is an AI-powered financial analysis agent built using LangChain, OpenAI GPT models, yFinance, and custom tools.  
It can understand natural language queries and fetch real-time market data, compute technical indicators, and process them into structured insights.

---

## Features

- Retrieve **latest stock prices** (OHLCV)
- Fetch **historical market data**
- Compute technical indicators:
  - SMA (Simple Moving Average)
  - EMA (Exponential Moving Average)
  - RSI (Relative Strength Index)
- Intelligent **tool-chaining** powered by LangChain
- Natural language understanding for stock-related queries
- Clean and structured **system prompt design** for predictable behavior

---

## Tech Stack

- **AI/LLM**: OpenAI GPT-4o-mini  
- **Backend**: Python, LangChain  
- **Market Data**: yFinance  
- **Data Processing**: Pandas, NumPy  
- **Environment Management**: python-dotenv  

---


---

## How FinSight Works

1. User asks a natural language financial question  
2. LangChain agent interprets the user's intent  
3. Agent automatically selects the correct tool:
   - Latest price  
   - Historical data  
   - Compute indicators  
   - (Optional) Plotting  
4. Tools return structured results (CSV strings)  
5. LLM forms the final user-friendly response  

This creates an end-to-end agentic system similar to how real financial analysts operate.

---

## Example Queries

- **“What is the current price of Apple?”**  
- **“Show me Tesla stock for the last 1 month.”**  
- **“Give me Microsoft with SMA 20 and 50.”**  
- **“Get NVIDIA prices for the last 3 months.”**

---

## Setup Instructions

### 1. Install dependencies

### 2. Add your OpenAI API key
Create a `.env` file:

### 3. Run the agent

---

## Key Concepts Used

- **LangChain Tools**  
- **Agent tool-chaining**  
- **System prompt engineering**  
- **Technical analysis (SMA, EMA, RSI)**  
- Data engineering using **Pandas & yFinance**  
- LLM-based reasoning + API integration  
