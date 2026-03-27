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
from langgraph.types import Send
import operator
from pydantic import BaseModel, Field

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
    colleges = {
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
    return colleges

# --- Initialize LLM ---
llm = get_llm(provider='groq')

# --- Define Shared State ---    
class AgentInput(TypedDict):
    """Simple input state for each subagent."""
    query: str


class AgentOutput(TypedDict):
    """Output from each subagent."""
    source: str
    result: str


class Classification(TypedDict):
    """A single routing decision: which agent to call with what query."""
    source: Literal["course_agent", "institution_agent"]
    query: str

class RouterState(TypedDict):
    query: str
    classifications: list[Classification]
    results: Annotated[list[AgentOutput], operator.add]  # Reducer collects parallel results
    final_answer: str


course_agent_prompt = ''' You are an expert course recommender. Use the available tools to fetch course catalog.
        Based on the user query, recommend a suitable course from amongst the catalog
        DO NOT INVENT COURSES. Recommend a course from the catalog.'''
        
institution_agent_prompt = ''' "You are an expert University/College recommender. Use the available tools to fetch institution catalog.
        Based on the user query, recommend a suitable institution from amongst the catalog.
        DO NOT INVENT Universities. Recommend a institution from the catalog.'''

course_recommender_agent = create_agent(
        llm, 
        tools=[get_course_catalog],
    system_prompt=(course_agent_prompt
    )
)

institution_recommender_agent = create_agent(
        llm, 
        tools=[get_institution_catalog],
    system_prompt=(institution_agent_prompt
    )
)
# Initialize router llm
router_llm = get_llm(provider='groq')

# Define structured output schema for the classifier
class ClassificationResult(BaseModel):
    """Result of classifying a user query into agent-specific sub-questions."""
    classifications: list[Classification] = Field(
        description="List of agents to invoke with their targeted sub-questions"
    )
    
    
def classify_query(state: RouterState) -> dict:
    """Classify query and determine which agents to invoke."""
    structured_llm = router_llm.with_structured_output(ClassificationResult)

    result = structured_llm.invoke([
        {
            "role": "system",
            "content": """Analyze this query and determine which knowledge bases to consult.
For each relevant source, generate a targeted sub-question optimized for that source.

Available sources:
- course_recommender_agent: Recommends a course based on user query
- institution_recommender_agent: Recommends a institution based on user query

Return ONLY the sources that are relevant to the query. Each source should have
a targeted sub-question optimized for that specific knowledge domain.
"""
        },
        {"role": "user", "content": state["query"]}
    ])

    return {"classifications": result.classifications}

def route_to_agents(state: RouterState) -> list[Send]:
    """Fan out to agents based on classifications."""
    return [
        Send(c["source"], {"query": c["query"]})
        for c in state["classifications"]
    ]

def invoke_course_agent(state):
    """
    """
    result = course_recommender_agent.invoke({"messages": [{"role": "user", "content": state["query"]}]})
    print('result of course agent')
    ai_msg = result["messages"][-1].content
    return {"results": [{"source": "course_agent", "result": result["messages"][-1].content}]}

def invoke_institution_agent(state):
    """
    
    """
    result = institution_recommender_agent.invoke({"messages": [{"role": "user", "content": state["query"]}]})
    print('result of institution agent')
    ai_msg = result["messages"][-1].content
    return {"results": [{"source": "institution_agent", "result": result["messages"][-1].content}]}

def synthesize_results(state: RouterState) -> dict:
    """Combine results from all agents into a coherent answer."""
    if not state["results"]:
        return {"final_answer": "No results found from any knowledge source."}

    formatted = [
        f"**From {r['source'].title()}:**\n{r['result']}"
        for r in state["results"]
    ]

    synthesis_response = router_llm.invoke([
        {
            "role": "system",
            "content": f"""Synthesize these search results to answer the original question: "{state['query']}"

- Combine information from multiple sources without redundancy
- Highlight the most relevant and actionable information
- Note any discrepancies between sources
- Keep the response concise and well-organized"""
        },
        {"role": "user", "content": "\n\n".join(formatted)}
    ])

    return {"final_answer": synthesis_response.content}


def build_graph():

    # --- Build the Graph ---
    workflow = StateGraph(RouterState)
    workflow.add_node("classify", classify_query) # Adds the new router agent to the flow
    workflow.add_node("course_agent", invoke_course_agent)
    workflow.add_node("institution_agent", invoke_institution_agent) # Adds the institution agent to the flow
    workflow.add_node("synthesize", synthesize_results)
    workflow.add_edge(START, "classify")
    workflow.add_conditional_edges("classify", route_to_agents, ["course_agent", "institution_agent"])
    workflow.add_edge("course_agent", "synthesize")
    workflow.add_edge("institution_agent", "synthesize")
    workflow.add_edge("synthesize", END)

    app = workflow.compile()
    return app


def invoke_recommender(user_query: str):
    app = build_graph()
    result = app.invoke({
        "query": user_query
    })
    print('--------------response from recommender-----------')
    print(result)
    return result