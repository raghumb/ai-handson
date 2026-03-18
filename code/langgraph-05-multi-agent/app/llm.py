import getpass
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq


    
def get_llm(provider: str):
    """     llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    ) """
    llm = None
    if provider == 'openai':
        key = os.environ["OPENAI_API_KEY"]
        llm = ChatOpenAI(
            model="gpt-4o",
            openai_api_key=key,
            base_url="https://models.github.ai/inference"
        )
    if provider == 'groq':
        if "GROQ_API_KEY" not in os.environ:
            os.environ["GROQ_API_KEY"] = getpass.getpass("Enter your Groq API key: ")
        llm = ChatGroq(
            model="openai/gpt-oss-120b",
            temperature=1,
            max_tokens=8192,
            top_p=1,
            reasoning_format="parsed",
            timeout=None,
            max_retries=2
    )
    if provider == 'google':
        llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        ) 
    return llm