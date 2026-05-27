from langchain_groq import ChatGroq
from langgraph.graph import StateGraph,START,END
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage,HumanMessage
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

import requests
import random
import os

#---------------------------------------------------------------------------------------------------------------------------------------

load_dotenv()
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=1.0)

#---------------------------------------------------------------------------------------------------------------------------------------

# Tools
search_tool = DuckDuckGoSearchRun()

@tool
def calculator(a : float, b: float, operation: str) -> float:

    """it performs basic arithmetic operations like addition, subtraction, multiplication, and division."""
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        if b != 0:
            return a / b
        else:
            return "Error: Division by zero"
    else:
        return "Error: Invalid operation"
    
@tool
def get_stock_price(symbol : str) -> dict:
    """it fetches the current stock price for a given stock symbol using the Alpha Vantage API."""

    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={os.getenv('ALPHA_VANTAGE_API_KEY')}"
    response = requests.get(url)
    return response.json()

tools = [search_tool , calculator ,  get_stock_price]

llm_with_tools = llm.bind_tools(tools)

#---------------------------------------------------------------------------------------------------------------------------------------

class ChatState(TypedDict):

    messages : Annotated[list[BaseMessage],add_messages]

#---------------------------------------------------------------------------------------------------------------------------------------


def chat_node(state : ChatState) -> ChatState:

    message = state['messages']
    response = llm_with_tools.invoke(message)

    return {
        'messages': [response]
    }

tool_node = ToolNode(tools)
#---------------------------------------------------------------------------------------------------------------------------------------

conn = sqlite3.connect(database = 'chatbot.db' , check_same_thread = False)
checkpointer = SqliteSaver(conn=conn)

#---------------------------------------------------------------------------------------------------------------------------------------

graph = StateGraph(ChatState)
graph.add_node('chat_node',chat_node)
graph.add_node('tools',tool_node)

graph.add_edge(START,'chat_node')
graph.add_conditional_edges('chat_node',tools_condition)
graph.add_edge('tools','chat_node')

workflow = graph.compile(checkpointer=checkpointer)



#---------------------------------------------------------------------------------------------------------------------------------------
def retrive_threads():
    all_thread = set()
    for checkpoint in checkpointer.list(None):
        all_thread.add(checkpoint.config['configurable']['thread_id'])
    return list(all_thread)

#----------------------------------------------------------------------------------------------------------------------------------------
output = workflow.invoke(
    {
        'messages': [HumanMessage(content="What is the current stock price of apple? ")]
    },
    config={
        "configurable": {
            "thread_id": "thread-1"   # 👈 any string is fine
        }
    }
)

print(output['messages'][-1].content)