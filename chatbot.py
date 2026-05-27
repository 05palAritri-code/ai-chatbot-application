import tempfile
# from unittest import loader

from langchain_core import messages
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph,START,END
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Any, Dict, Optional, TypedDict, Annotated
from langchain_core.messages import AIMessage, BaseMessage,HumanMessage,SystemMessage
from langgraph.graph.message import add_messages

from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
import wikipedia
from langchain_core.tools import tool

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
import psycopg2
from psycopg2.extras import RealDictCursor
# import sqlite3
# from langgraph.checkpoint.sqlite import SqliteSaver
import math
import requests
import random
import os

import hashlib
import re


#---------------------------------------------------------------------------------------------------------------------------------------
load_dotenv()
#---------------------------------------------------------------------------------------------------------------------------------------

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=1,max_retries=2)
embeddings = HuggingFaceEmbeddings(model_name = "sentence-transformers/all-MiniLM-L6-v2")

#---------------------------------------------------------------------------------------------------------------------------------------
# def hash_password(password):
#     return hashlib.sha256(password.encode()).hexdigest()

# def create_user(email, username, password):
#     try:
#         cursor.execute(
#             "INSERT INTO users (email, username, password) VALUES (%s, %s, %s)",
#             (email, username, hash_password(password))
#         )
#         conn.commit()
#         print("✅ User inserted successfully")
#         return True

#     except Exception as e:
#         print("❌ ERROR:", e)
#         conn.rollback()
#         return False

# def login_user(email, password):
#     try:
#         cursor.execute(
#             "SELECT username FROM users WHERE email=%s AND password=%s",
#             (email, hash_password(password))
#         )
#         return cursor.fetchone()
    
#     except Exception as e:
#         print("LOGIN ERROR:", e)
#         conn.rollback()   # ✅ reset broken transaction
#         return None



def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(email, username, password):

    try:

        cursor = conn.cursor()

        # check email
        cursor.execute(
            "SELECT id FROM users WHERE email=%s",
            (email,)
        )

        if cursor.fetchone():

            return "email_exists"

        # check username
        cursor.execute(
            "SELECT id FROM users WHERE username=%s",
            (username,)
        )

        if cursor.fetchone():

            return "username_exists"

        # create user
        cursor.execute(
            """
            INSERT INTO users
            (email, username, password)
            VALUES (%s, %s, %s)
            """,
            (
                email,
                username,
                hash_password(password)
            )
        )

        conn.commit()
        print("✅ User inserted successfully")
        return "success"

    except Exception as e:

        print("CREATE USER ERROR:", e)

        return "error"

def login_user(email, password):
    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT username FROM users WHERE email=%s AND password=%s",
            (email, hash_password(password))
        )

        return cursor.fetchone()

    except Exception as e:
        print("LOGIN ERROR:", e)
        return None

def save_thread(thread_id, username, title):
    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO threads 
            (thread_id, username, title)
            VALUES (%s, %s, %s)
            ON CONFLICT (thread_id) DO NOTHING
            """,
            (thread_id, username, title)
        )

        conn.commit()

    except Exception as e:
        print("SAVE THREAD ERROR:", e)
def update_thread_title(thread_id, title):

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE threads
            SET title=%s
            WHERE thread_id=%s
            """,
            (title, thread_id)
        )

        conn.commit()

    except Exception as e:

        print("UPDATE TITLE ERROR:", e)
def save_message(thread_id, role, content):

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO messages
            (thread_id, role, content)
            VALUES (%s, %s, %s)
            """,
            (thread_id, role, content)
        )

        conn.commit()

    except Exception as e:

        print("SAVE MESSAGE ERROR:", e)

#---------------------------------------------------------------------------------------------------------------------------------------

_THREAD_RETRIEVERS : Dict[str,Any] ={}
_THREAD_METADATA : Dict[str,dict] ={}

def _get_retriever(thread_id : Optional[str]):
    if thread_id and thread_id in _THREAD_RETRIEVERS:
        return _THREAD_RETRIEVERS[thread_id]
    return None

def ingest_pdf(file_bytes : bytes , thread_id : str , filename : Optional[str] = None) -> dict:
    '''Build a retirever for the uploaded pdf and store it for the thread.
    returns a summary dict that can be surfaced in the UI
    Ingest a PDF file, split it into chunks, create embeddings, and store in vector store'''

    if not file_bytes:
        raise ValueError('No bytes received for ingestion.')
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        temp_file.write(file_bytes)
        temp_path = temp_file.name
    try:
        loader = PyPDFLoader(temp_path)
        docs = loader.load()

        # if not docs:
        #     raise ValueError("PDF has no readable text.")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200, separators=["\n\n", "\n", " ", ""]
            )
        chunks = splitter.split_documents(docs)
        # if not chunks:
        #     raise ValueError("Chunking failed.")

        vector_store = Chroma.from_documents(chunks, embeddings)
        retriever = vector_store.as_retriever(
            search_type = 'mmr',search_kwargs = {'k':2}
        )

        _THREAD_RETRIEVERS[str(thread_id)] = retriever
        _THREAD_METADATA[str(thread_id)] = {
            'filename': filename or os.path.basename(temp_path),
            'documents' : len(docs),
            'chunks' : len(chunks)
        }

        return{
            'filename': filename or os.path.basename(temp_path),
            'documents' : len(docs),
            'chunks' : len(chunks)
        }

    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass

#---------------------------------------------------------------------------------------------------------------------------------------
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
            'error' : "No document  indexed for this chat , Please upload a PDF to use this tool.",
            'query' : query
        }
    result = retriever.invoke(query)
    context = [doc.page_content for doc in result]
    metadata = [doc.metadata for doc in result]
    return {
        'query': query,
        'context': context,
        'metadata': metadata,
        'source_file': _THREAD_METADATA.get(str(thread_id), {}).get('filename')
    }

    
tools = [search ,  calculator  , rag_tool , wiki_search]

llm_with_tools = llm.bind_tools(tools)

#---------------------------------------------------------------------------------------------------------------------------------------

class ChatState(TypedDict):

    messages : Annotated[list[BaseMessage],add_messages]

#---------------------------------------------------------------------------------------------------------------------------------------
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
def build_system_prompt(has_pdf, query_type):

    base_prompt = """
    You are a professional AI assistant.

    Guidelines:
    - Answer naturally
    - Use tools when needed
    - Never expose tools
    - Never expose errors
    - Never expose reasoning
    """

    if has_pdf:
        base_prompt += """
        A PDF document is available.

        Use rag_tool ONLY for document-related queries.
        """

    if query_type == "search":
        base_prompt += """
        This query may require recent information.
        Prefer search tool.
        """

    elif query_type == "calculator":
        base_prompt += """
        This query involves mathematics.
        Use calculator tool carefully.
        """

    elif query_type == "stock":
        base_prompt += """
        This query involves stock information.
        Use stock tool.
        """

    return base_prompt
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
# def chat_node(state: ChatState,config = None) -> ChatState:
#     thread_id = None
#     if config and isinstance(config, dict):
#         thread_id = config.get('configurable',{}).get('thread_id')
#     retriever = _get_retriever(thread_id)
#     has_pdf = retriever is not None
#     system_prompt = build_system_prompt(has_pdf)
#     system_messages = SystemMessage(content=system_prompt)


#     messages = [system_messages,*state["messages"]]
#     response = llm_with_tools.invoke(messages,config =config)
#     response.content = clean_response(response.content)
#     return {"messages": [response]}

# tool_node = ToolNode(tools)
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
    # try:

    #     response = llm_with_tools.invoke(
    #         messages,
    #         config=config
    #     )

    # except Exception:

    #     response = AIMessage(
    #             content="I encountered a temporary issue while processing your request. Please try again."
    #         )

    if isinstance(response.content, str):
        response.content = clean_response(response.content)

    return {
        "messages": [response]
    }
tool_node = ToolNode(tools)

#---------------------------------------------------------------------------------------------------------------------------------------


# conn = sqlite3.connect("chatbot.db", check_same_thread=False)
# cursor = conn.cursor()

DATABASE_URL = os.getenv("DATABASE_URL")
def get_connection():

    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )

# conn = psycopg2.connect(
#     DATABASE_URL,
#     cursor_factory=RealDictCursor
# )
# cursor = conn.cursor()

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE,
    username TEXT UNIQUE,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS threads (
    id SERIAL PRIMARY KEY,
    thread_id TEXT UNIQUE,
    username TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    thread_id TEXT,
    role TEXT,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

checkpointer = None
# checkpointer = SqliteSaver(conn=conn)
# checkpointer = SqliteSaver(conn=conn,configurable_keys=['thread_id'])
#---------------------------------------------------------------------------------------------------------------------------------------
graph = StateGraph(ChatState)
graph.add_node('chat_node',chat_node)
graph.add_node('tools',tool_node)

graph.add_edge(START,'chat_node')
graph.add_conditional_edges('chat_node',tools_condition)
graph.add_edge('tools','chat_node')

# workflow = graph.compile(checkpointer=checkpointer)
workflow = graph.compile()

#---------------------------------------------------------------------------------------------------------------------------------------
# def retrive_threads():
#     all_thread = set()
#     for checkpoint in checkpointer.list(None):
#         all_thread.add(checkpoint.config['configurable']['thread_id'])
#     return list(all_thread)

# def retrive_threads(username):
#     user_threads = set()

#     for checkpoint in checkpointer.list(None):
#         config = checkpoint.config.get("configurable", {})

#         # 👇 check user match
#         if config.get("user") == username:
#             user_threads.add(config.get("thread_id"))

#     return list(user_threads)
# -----------------------------------------------------------------------------------------------------------------------------------------------
# def retrive_threads(username):
#     try:
#         cursor = conn.cursor()

#         cursor.execute(
#             """
#             SELECT thread_id
#             FROM threads
#             WHERE username=%s
#             """,
#             (username,)
#         )

#         rows = cursor.fetchall()

#         return [row["thread_id"] for row in rows]

#     except Exception as e:
#         print("RETRIEVE THREAD ERROR:", e)
#         return []
def retrive_threads(username):

    conn = None
    cursor = None

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT thread_id
            FROM threads
            WHERE username=%s
            ORDER BY created_at DESC
            """,
            (username,)
        )

        rows = cursor.fetchall()

        return [row["thread_id"] for row in rows]

    except Exception as e:

        print("RETRIEVE THREAD ERROR:", e)
        return []

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

def load_messages(thread_id):

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT role, content
            FROM messages
            WHERE thread_id=%s
            ORDER BY id
            """,
            (thread_id,)
        )

        rows = cursor.fetchall()

        return [
            {
                "role": row["role"],
                "content": row["content"]
            }
            for row in rows
        ]

    except Exception as e:

        print("LOAD MESSAGE ERROR:", e)

        return []
    
def thread_has_document(thread_id : str) -> bool:
    return str(thread_id) in _THREAD_RETRIEVERS

def thread_document_metadata(thread_id : str) -> dict:
    return _THREAD_METADATA.get(str(thread_id),{})

def delete_thread(thread_id):

    try:

        cursor = conn.cursor()

        # delete messages first
        cursor.execute(
            """
            DELETE FROM messages
            WHERE thread_id=%s
            """,
            (thread_id,)
        )

        # delete thread
        cursor.execute(
            """
            DELETE FROM threads
            WHERE thread_id=%s
            """,
            (thread_id,)
        )

        conn.commit()

    except Exception as e:

        print("DELETE THREAD ERROR:", e)


def rename_thread(thread_id, new_title):

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE threads
            SET title=%s
            WHERE thread_id=%s
            """,
            (new_title, thread_id)
        )

        conn.commit()

    except Exception as e:

        print("RENAME THREAD ERROR:", e)

def get_thread_title(thread_id):

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT title
            FROM threads
            WHERE thread_id=%s
            """,
            (thread_id,)
        )

        row = cursor.fetchone()

        if row:
            return row["title"]

    except Exception as e:

        print("GET TITLE ERROR:", e)

    return None
# try:
#     cursor.execute("SELECT 1")
#     print("✅ Connected to Supabase")

# except Exception as e:
#     print("❌ DB ERROR:", e)