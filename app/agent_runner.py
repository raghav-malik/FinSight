import os
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from dotenv import load_dotenv


from .tools.data_tools import get_historical_data
from .tools.latest_price import get_latest_price
from .tools.calculate_indicators import calculate_technical_indicators
from .tools.plotting import create_stock_plot

from .agent_prompts import SYSTEM_PROMPT_STRING


load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")


llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=api_key,
    temperature=0
)

tools = [get_historical_data, 
         get_latest_price, 
         calculate_technical_indicators,
         create_stock_plot
         ]

agent_executor = create_agent(
    model=llm,
    tools=tools,
    system_prompt=SYSTEM_PROMPT_STRING,
    debug=False  
)


def main():
    print("=" * 60)
    print("Welcome to FinSight - Your Financial Analyst Agent!")
    print("=" * 60)
    print("\nType 'exit' to quit, 'clear' to clear history\n")
    print("Examples:")
    print("  📊 Data Queries:")
    print("    • 'what is the current price of Apple?'")
    print("    • 'show me Tesla stock for the last month'")
    print("    • 'get NVIDIA prices for the last 3 months'")
    print("\n  📈 Technical Analysis:")
    print("    • 'give me Microsoft with SMA 20 and 50'")
    print("    • 'show Tesla with RSI for last 2 months'")
    print("    • 'Apple stock with EMA 12 and RSI'")
    print("\n  📉 Visualizations:")
    print("    • 'plot Amazon stock for the last year'")
    print("    • 'chart Google with moving averages'")
    print("    • 'visualize Netflix with SMA 20, 50 and RSI'\n")
    
    messages = []

    while True:
        try:
            user_input = input("\n💬 You: ")
            
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("\n👋 Goodbye!")
                break
            
            if user_input.lower() == "clear":
                messages = []
                print("\n✨ Chat history cleared!")
                continue

            # Add user message
            messages.append({"role": "user", "content": user_input})

            print(f"\n🤖 FinSight: ", end="", flush=True)
            
            # Track if we've printed anything yet
            has_printed = False
            
            # Stream with "values" mode but only show final response
            for step in agent_executor.stream(
                {"messages": messages},
                stream_mode="values"
            ):
                # Get the last message in the step
                last_msg = step["messages"][-1]
                
                # Only print the final AI response (not tool calls)
                if (hasattr(last_msg, 'type') and 
                    last_msg.type == "ai" and 
                    not (hasattr(last_msg, 'tool_calls') and last_msg.tool_calls)):
                    
                    if not has_printed:
                        print(last_msg.content, flush=True)
                        messages.append({"role": "assistant", "content": last_msg.content})
                        has_printed = True
            
            if not has_printed:
                print("(No response generated)")
            
            print()  # Add spacing after response

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    if not api_key:
        print("❌ ERROR: Please set your OPENAI_API_KEY in .env file")
    else:
        main()
        