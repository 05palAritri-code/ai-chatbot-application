from langchain_groq import ChatGroq
from tools import tools
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile", 
    temperature=1,
    max_retries=2
    )

llm_with_tools = llm.bind_tools(tools)
