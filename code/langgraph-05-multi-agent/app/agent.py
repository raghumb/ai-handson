import os
from typing import TypedDict
from typing import Literal
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict, Annotated, List, Optional
from langchain.tools import tool

from llm import get_llm
import os
from crewai_tools import SerperDevTool
from langchain.agents import create_agent, AgentState
from langgraph.graph.message import add_messages
import finnhub
from recommender_agent import invoke_recommender

# --- Define Tools ---
@tool
def get_stock_data(symbol: str):
    """Get Stock information for symbol."""
    api_key = os.environ["STOCK_API_KEY"]
    finnhub_client = finnhub.Client(api_key=api_key)
    
    data = finnhub_client.quote('AAPL')
    
    return data
    
    

@tool
def recommender_agent(user_query: str):
    """Returns recommendation of courses and institutions based on user query"""
    print("in recomm agent" + user_query)
    return invoke_recommender(user_query)


# --- Initialize LLM ---
llm = get_llm(provider='groq')

main_agent = create_agent(
    model=llm, 
    tools=[get_stock_data, recommender_agent],
    system_prompt=(
                 "You are a helpful personal assistant. "
                 "You can tell the price of a stock and recommend courses and institutions. "
                 "Break down user requests into appropriate tool calls and coordinate the results. "
                 "When a request involves multiple actions, use multiple tools in sequence."
    )
)

# --- Define Shared State ---
class AgentState(TypedDict):
    user_query: str
    #answer: str
    messages: Annotated[list, add_messages]



# --- Run the App ---
def invoke2(query: str):
   #query = "Show me price of ORCL stock"
   #query = "Suggest a good course on system design"
   #query = "Suggest a good college for masters in security"
   for step in main_agent.stream(
        {"messages": [{"role": "user", "content": query}]}
   ):
        for update in step.values():
            for message in update.get("messages", []):
                message.pretty_print()
                
def run(query: str):
   #query = "Show me price of ORCL stock"
   #query = "Suggest a good course on system design"
   #query = "Suggest a good college for masters in security"
   return main_agent.invoke(
        {"messages": [{"role": "user", "content": query}]})
   
