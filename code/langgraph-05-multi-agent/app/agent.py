import os
from typing import TypedDict
from typing import Literal
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict, Annotated, List, Optional
from langchain.tools import tool

from llm import get_llm
from crewai_tools import SerperDevTool
from langchain.agents import create_agent, AgentState
from langgraph.graph.message import add_messages

# --- Define Tool ---
@tool
def get_course_catalog(user_query: str):
    """Returns a list of curated courses from the catalog along with hash tags, course specification details"""
    courses = {
       "Beginners course on System Design": {
            "specs": "10-hour video series covering Load Balancers, Caching, and Database Sharding. Includes 5 hands-on projects.",
            "tags": ["#SystemDesign", "#SoftwareEngineering", "#Scalability"]
        },
        "Architecting Scalable systems": {
            "specs": "Advanced workshop focusing on Microservices, Event-driven architecture, and Multi-region deployment.",
            "tags": ["#Architecture", "#Microservices", "#CloudComputing"]
        },
        "Programming Best practices": {
            "specs": "Interactive coding labs teaching SOLID principles, Clean Code, and Unit Testing across multiple languages.",
            "tags": ["#CleanCode", "#SOLID", "#Programming"]
        },
        "Programming for Beginners": {
            "specs": "Interactive coding labs teaching fundamentals of Programming in Python.",
            "tags": ["#Programming Basics", "#Algorithms", "#Programming"]
        }
    }
    return courses

@tool
def get_institution_catalog(user_query: str):
    """Returns a list of curated institutions who offer masters courses for working professionals"""
    courses = {
       "Georgia Tech University": {
            "specs": "Online Masters in Artificial Intelligence, Machine Learning, Software Engineering. Highly Ranked amongst online masters.",
            "country": ["US"]
        },
         "Liverpool University": {
            "specs": "Online Masters in Artificial Intelligence, Machine Learning, Cyber Security",
            "country": ["UK"]
        },
        "Texas University": {
            "specs": "Online Masters in Machine Learning, Software Engineering",
            "country": ["US"]
        },
        "Illinois University": {
            "specs": "Online Masters in Artificial Intelligence, Machine Learning",
            "country": ["US"]
        },
    }
    return courses

# --- Initialize LLM ---
llm = get_llm(provider='groq')

# --- Define Shared State ---
class AgentState(TypedDict):
    user_query: str
    #answer: str
    messages: Annotated[list, add_messages]



course_agent_prompt = ''' You are an expert course recommender. Use the available tools to fetch course catalog.
        Based on the user query, recommend a suitable course from amongst the catalog
        DO NOT INVENT COURSES. Recommend a course from the catalog.'''
        
institution_agent_prompt = ''' "You are an expert University/College recommender. Use the available tools to fetch institution catalog.
        Based on the user query, recommend a suitable institution from amongst the catalog.
        DO NOT INVENT Universities. Recommend a institution from the catalog.'''

course_agent = create_agent(
        llm, 
        tools=[get_course_catalog],
    system_prompt=(course_agent_prompt
    )
)

institution_agent = create_agent(
        llm, 
        tools=[get_institution_catalog],
    system_prompt=(institution_agent_prompt
    )
)

def course_agent_react(state):
    """
    
    """
    result = course_agent.invoke({"messages": state["user_query"]})
    print('result of course agent')
    ai_msg = result["messages"][-1].content
    return {"messages": result["messages"]}

def institution_agent_react(state):
    """
    
    """
    result = institution_agent.invoke({"messages": state["user_query"]})
    print('result of institution agent')
    ai_msg = result["messages"][-1].content
    return {"messages": result["messages"]}

# --- Define Router Agent ---
def router_agent(state: AgentState) -> str:
    """
    Captures a user query from the command line and updates the state.

    This function acts as an input node in the LangGraph workflow. It prompts the user
    to enter a query via the console, then stores that input in the shared state under
    the 'user_query' key.

    Args:
        state (AgentState): The current state dictionary (can be empty or partially filled).

    Returns:
        dict: Updated state containing the user's query.
    """
    print("--- Router Node ---")
    state['user_query'] = input("Input user query: ")
    return state

# --- Define Agents DocString ---
agent_docs = {
    "course_agent": course_agent_prompt,
    "institution_agent": institution_agent_prompt
}

# --- Define Routing Logic ---
def routing_logic(state: AgentState) -> Literal["institution_agent", "course_agent"]:
    """
    Uses the LLM to choose between 'institution_agent' and 'course_agent'
    based on the intent of the user query and the agents' docstrings.

    Args:
        state (AgentState): The current state containing the user query.

    Returns:
        str: The name of the next node to route to.
    """
    prompt = f"""
    You are a router agent. Your task is to choose the best agent for the job.
    Here is the user query: {state['user_query']}

    You can choose from the following agents:
    - institution_agent: {agent_docs['institution_agent']}
    - course_agent: {course_agent_prompt}

    Which agent should handle this query? Respond with just the agent name.
    """
    response = llm.invoke(prompt)
    decision = response.content.strip().lower()
    return "institution_agent" if "institution" in decision else "course_agent"

   

# --- Build the Graph ---
workflow = StateGraph(AgentState)
workflow.add_node("router_agent", router_agent) # Adds the new router agent to the flow
workflow.add_node("course_agent", course_agent_react)
workflow.add_node("institution_agent", institution_agent_react) # Adds the institution agent to the flow

workflow.add_edge(START, "router_agent")
workflow.add_conditional_edges("router_agent", routing_logic)
workflow.add_edge("course_agent", END)
workflow.add_edge("institution_agent", END)

app = workflow.compile()


# --- Run the App ---
if __name__ == "__main__":
    result = app.invoke({})
    print('--------------response-----------')
    print(result['messages'][-1])