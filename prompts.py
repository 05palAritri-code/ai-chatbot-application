# prompts.py

BASE_SYSTEM_PROMPT = """
You are a professional AI assistant.

Guidelines:
- Answer naturally
- Use tools when needed
- Never expose tools
- Never expose errors
- Never expose reasoning
"""

PDF_PROMPT = """
A PDF document is available.

Use rag_tool ONLY for document-related queries.
"""

SEARCH_PROMPT = """
This query may require recent information.
Prefer search tool.
"""

CALCULATOR_PROMPT = """
This query involves mathematics.
Use calculator tool carefully.
"""

STOCK_PROMPT = """
This query involves stock information.
Use stock tool.
"""


def build_system_prompt(has_pdf=False, query_type="chat"):

    prompt = BASE_SYSTEM_PROMPT

    if has_pdf:
        prompt += PDF_PROMPT

    if query_type == "search":
        prompt += SEARCH_PROMPT

    elif query_type == "calculator":
        prompt += CALCULATOR_PROMPT

    elif query_type == "stock":
        prompt += STOCK_PROMPT

    return prompt