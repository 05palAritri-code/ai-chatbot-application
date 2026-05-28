from typing import Any, Dict, Optional, TypedDict, Annotated
from typing import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import AIMessage, BaseMessage,HumanMessage,SystemMessage

from chatbot import _get_retriever
from prompts import build_system_prompt
from utils import clean_response
from llm_manager import llm_with_tools


class ChatState(TypedDict):

    messages : Annotated[list[BaseMessage],add_messages]


def classify_query(query):

    query = query.lower()

    if any(word in query for word in [
        "latest",
        "today",
        "news",
        "current",
        "update"
    ]):
        return "search"

    if any(word in query for word in [
        "calculate",
        "+",
        "-",
        "*",
        "/",
        "sqrt",
        "log"
    ]):
        return "calculator"

    if any(word in query for word in [
        "stock",
        "share price"
    ]):
        return "stock"

    return "chat"

def chat_node(state: ChatState, config=None) -> ChatState:

    thread_id = None

    if config and isinstance(config, dict):
        thread_id = config.get("configurable", {}).get("thread_id")

    retriever = _get_retriever(thread_id)
    has_pdf = retriever is not None

    user_query = state["messages"][-1].content.lower()

    query_type = classify_query(user_query)

    system_prompt = build_system_prompt(
        has_pdf=has_pdf,
        query_type=query_type
    )

    system_message = SystemMessage(content=system_prompt)

    # messages = [system_message, *state["messages"]]

    messages = state["messages"]

    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [system_message] + messages

    response = llm_with_tools.invoke(
            messages,
            config=config
    )
    

    if isinstance(response.content, str):
        response.content = clean_response(response.content)

    return {
        "messages": [response]
    }
tool_node = ToolNode(tools)