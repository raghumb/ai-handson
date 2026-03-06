# Langgraph - Building a React Agent - Blog post generator

Medium article explaining this.

## Setup
- Activate an environment
- pip install -r requirements.txt
- Go to groq.com and register an API key for free.
- Go to https://www.alphavantage.co/ and register an API key (premium) or use the API key provided for demo purpose for testing.
- Set up env var with the api key. 
    - export GROQ_API_KEY=<API_KEY>
    - export STOCK_API_KEY=<STOCK_API_KEY>
- Run MCP Server: python3 stock_server.py
- Run streamlit app: streamlit run app/main.py

- Enter a topic for the blog post and click 'Generate Blog Post'
