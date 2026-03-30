# Hierarchical Agents in Langgraph

Medium article explaining this. [Hands-on guide to building a Hierarchical Multi Agent System](https://raghumb.medium.com/hands-on-guide-to-building-a-hierarchical-multi-agent-system-85ffd34f71de)

## Setup
- Activate an environment
- pip install -r requirements.txt
- Go to groq.com and register an API key for free.
- Go to https://finnhub.io/ and register an API key for free.
- Set up env var with the api key. 
    - export GROQ_API_KEY=<API_KEY>
    - export STOCK_API_KEY=<STOCK_API_KEY>

- Run streamlit app using command: 
streamlit run app/main.py

- Enter a text 'Provide me the price of <COMPANY NAME>' by providing the name of any company listed in NASDAQ and see the results.
- Enter a text 'Suggest me courses on System design' and check if the course names match that from courses catalog
- Enter a text 'Suggest me colleges on Cyber security in UK' and check if the course names match that from institution catalog


