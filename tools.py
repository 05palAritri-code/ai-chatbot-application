from langchain_community.tools import DuckDuckGoSearchRun, tool
from typing import  Optional
import wikipedia
import math
import requests
from ingest import _get_retriever
import os 


@tool
def search(query: str) -> str:
    """Search the internet for real-time or recent latest information.

        Use this tool when the user asks about:
        - Latest news (global or location-specific, e.g., Kolkata, Mumbai, Delhi, Chennai)
        - Sports updates (cricket, football, matches, scores, tournaments)
        - Entertainment news (Bollywood, Hollywood, Tollywood, etc.)
        - Current events or trending topics in any country
        - Weather updates for any location

        Guidelines:
        - Use this tool for queries containing words like: "latest", "today", "current", "news", "update"
        - Prefer this tool for anything time-sensitive or recently changing
        - Do NOT use this tool for general knowledge or historical facts
        - Always pass a clear and specific search query
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
def rag_tool(query : str, thread_id : Optional[str]) -> str:
    """Use this tool to answer questions based on the content of an uploaded PDF document.
    always include the thread_id when invoking this tool to ensure the correct document retriever is used.

    Guidelines:
    - Use this tool when the user asks about information that may be contained in their uploaded PDF.
    - The query will be passed along with the thread_id to retrieve relevant information from the PDF.
    - If no retriever is found for the thread_id, return a message indicating that no document is available.
    """

    retriever = _get_retriever(thread_id)
   

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

    # context = "\n\n".join(
    #     [doc.page_content for doc in result]
    # )

    # sources = []

    # for doc in result:

    #     sources.append({
    #         "file": doc.metadata.get("filename"),
    #         "page": doc.metadata.get("page", 0) + 1
    #     })

    # return {
    #     "query": query,
    #     "context": context,
    #     "sources": sources
    # }

    context = [doc.page_content for doc in result]
    metadata = [doc.metadata for doc in result]

    return {
        'query': query,
        'context': context,
        'metadata': metadata,
        # 'source_file': _THREAD_METADATA.get(str(thread_id), {}).get('filename')
    }

    
tools = [search ,  calculator  , rag_tool , wiki_search]