import re

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