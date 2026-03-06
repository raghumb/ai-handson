import os
import json
from typing import TypedDict, Annotated, List
from llm import get_llm
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from IPython.display import Image, display
from pydantic import BaseModel, Field

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]
    draft: str
    feedback: str
    is_valid: bool
    topic: str
    
class ValidationResponse(BaseModel):
    is_valid: bool = Field(description="True if the post meets all 3 criteria, False otherwise.")
    feedback: str = Field(description="Specific instructions for the writer if valid is False.")
    
    
llm = get_llm()

def writer_node(state: AgentState):
    """Generates or updates the blog post based on feedback."""
    prompt = "You are a professional blog writer. "
    topic = state.get("topic")
    print('topic' + topic)
    feedback = state.get("feedback", "")
    current_draft = state.get("draft", "")
    if state.get("feedback"):
        prompt += f"Update the following blog post about '{topic}' based on this feedback: {feedback}"
    else:
        prompt += "Write a 300-word blog post about {topic}. Ensure it has a title and a conclusion."
    
    response = llm.invoke([HumanMessage(content=prompt + f"\n\nDraft: {current_draft}")])
    return {"draft": response.content, "messages": [AIMessage(content="I have updated the draft.")]}

def validator_node(state: AgentState):
    """Validates the blog post for quality and length."""
    prompt = f"""
    You are a professional editor. You are a data extraction tool. Evaluate the blog post based on the criteria. Do not provide a conversational response. 
    Output your findings only by calling the provided validation tool with the required schema.
    Evaluate this blog post.
    '{state['draft']}'
    
    Criteria:
    1. Must be over 200 words.
    2. Must include a catchy title.
    3. Must have a concluding 'Call to Action'.
    
    """
    structured_llm = llm.with_structured_output(ValidationResponse)
    response = structured_llm.invoke([HumanMessage(content=prompt)])
    return {"is_valid": response.is_valid, "feedback": response.feedback}

def should_continue(state: AgentState):
    if state["is_valid"]:
        return "end"
    return "rewrite"

def build_graph():
    # Build the Graph
    workflow = StateGraph(AgentState)

    workflow.add_node("writer", writer_node)
    workflow.add_node("validator", validator_node)

    workflow.set_entry_point("writer")

    workflow.add_edge("writer", "validator")
    workflow.add_conditional_edges(
        "validator",
        should_continue,
        {
            "rewrite": "writer",
            "end": END
        }
    )

    app = workflow.compile()
    return app

def run(topic: str):
    graph = build_graph()
    print(f"topic {topic}")
    
    initial_state = {
            "messages": [HumanMessage(content=f"Start blog on {topic}")],
            "topic": topic, 
            "draft": "",
            "feedback": "",
            "is_valid": False
        }
    

    final_state = graph.invoke(initial_state)
    return final_state


def run_streaming(topic: str):
    graph = build_graph()
    print(f"topic {topic}")
    
    initial_state = {
            "messages": [HumanMessage(content=f"Start blog on {topic}")],
            "topic": topic, 
            "draft": "",
            "feedback": "",
            "is_valid": False
        }
    

    for output in graph.stream(initial_state):
        yield output

                    

    