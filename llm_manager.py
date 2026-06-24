from langchain_groq import ChatGroq
from tools import tools
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile", 
    temperature=0.1,
    max_retries=2,
    timeout=30
    )

llm_with_tools = llm.bind_tools(tools)
