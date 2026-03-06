import getpass
import os
from langchain_groq import ChatGroq

if "GROQ_API_KEY" not in os.environ:
    os.environ["GROQ_API_KEY"] = getpass.getpass("Enter your Groq API key: ")
    
def get_llm():
    llm = ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=1,
        max_tokens=8192,
        top_p=1,
        reasoning_format="parsed",
        timeout=None,
        max_retries=2
    )
    return llm