from langchain_community.tools import DuckDuckGoSearchRun, tool
from typing import  Optional
import wikipedia
import math
import requests
import os 
from ingest import _get_retriever
from langchain_core.runnables import RunnableConfig

@tool
def search(query: str) -> str:
   
    """ Search the internet for real-time or recent information including
    news, current events, weather, sports, and general topics.
    
    """
   
    try:
        result = DuckDuckGoSearchRun().run(query)

        if not result:
            return "No recent information found."
        return result

    except Exception:
        return "Search temporarily unavailable."


@tool
def wiki_search(query: str) -> str:
    """Search Wikipedia for general knowledge.

    Use this tool for:
    - historical facts
    - definitions
    - people, places, concepts
    - science, technology, etc.

    Do NOT use this for:
    - latest news
    - real-time updates
    """

    try:
        summary = wikipedia.summary(query, sentences=3)
        return summary
    except Exception:
        return ""

@tool
def calculator(expression: str) -> str:
    """Perform mathematical calculations."""

    try:

        allowed_names = {
            "sqrt": math.sqrt,
            "log": math.log,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "pi": math.pi,
            "e": math.e,
            "abs": abs,
            "round": round,
            "pow": pow
        }

        expression = expression.strip()

        if not expression:
            return "Invalid expression."

        expression = expression.replace("^", "**")

        result = eval(
            expression,
            {"__builtins__": {}},
            allowed_names
        )

        return str(result)

    except Exception:
        return "Calculation error."
    
@tool
def get_stock_price(symbol : str) -> dict:
    """it fetches the current stock price for a given stock symbol using the Alpha Vantage API."""

    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={os.getenv('ALPHA_VANTAGE_API_KEY')}"
    response = requests.get(url)
    return response.json()



@tool
# def rag_tool(query : str, thread_id : Optional[str]) -> str:
def rag_tool(query: str, config: RunnableConfig) -> str:

    """Use this tool to answer questions based on the content of an uploaded PDF document.
        If no retriever is found return a message indicating that no document is available.

    """

    thread_id = config.get("configurable", {}).get("thread_id")
    
    print("FULL CONFIG:", config) 

    print("RAG TOOL THREAD:", thread_id)

    retriever = _get_retriever(thread_id)   

    print("RAG TOOL CALLED")

    if not retriever:
        return {
            "error": "No document indexed for this chat.",
            "query": query,
        }

    result = retriever.invoke(query)

    if not result:
        return {
            "query": query,
            "answer": "No relevant information found in the uploaded document."
        }


    context = "\n\n".join([doc.page_content for doc in result])

    sources = [
            {
                "file": doc.metadata.get("filename"),
                "page": doc.metadata.get("page", 0) + 1
            }
            for doc in result
        ]

    return {
            "query": query,
            "context": context,
            "sources": sources
        }
    # return {
    #         "document_context": context,
    #         "sources": metadata,
    #         "document_name": metadata[0].get("filename")
    #     }

    
tools = [search ,  calculator  , rag_tool , wiki_search , get_stock_price]
