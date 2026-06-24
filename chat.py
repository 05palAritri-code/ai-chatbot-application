from typing import  TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import AIMessage, BaseMessage,HumanMessage,SystemMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import StateGraph,START,END
import re
from prompts import build_system_prompt
from llm_manager import llm_with_tools
from tools import tools
from ingest import _get_retriever

def clean_response(text: str) -> str:

    patterns = [
        r"</function>",
        r"function=.*?>",
        r"groq\.APIError.*",
        r"failed_generation.*"
    ]

    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    return text.strip()


def classify_query(query):

    query = query.lower()
    if any(word in query for word in ["stock", "share price", "price of"]):
        return "stock"

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


class ChatState(TypedDict):

    messages : Annotated[list[BaseMessage],add_messages]


def chat_node(state: ChatState, config=None) -> ChatState:


    if config and isinstance(config, dict):
        thread_id = config.get("configurable", {}).get("thread_id")

    # print("CHAT NODE THREAD:", thread_id)


    retriever = _get_retriever(thread_id)
    has_pdf = retriever is not None

    user_query = state["messages"][-1].content.lower()

    query_type = classify_query(user_query)

    system_prompt = build_system_prompt(
        has_pdf=has_pdf,
        query_type=query_type
    )

    system_message = SystemMessage(content=system_prompt)


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

graph = StateGraph(ChatState)

graph.add_node('chat_node',chat_node)
graph.add_node('tools',tool_node)

graph.add_edge(START,'chat_node')
graph.add_conditional_edges('chat_node',tools_condition)
graph.add_edge('tools','chat_node')

workflow = graph.compile()