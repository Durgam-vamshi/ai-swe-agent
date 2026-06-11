
import os
import re
import time
import requests
from dotenv import load_dotenv
from app.utils.logger import log
from app.services.context_builder import build_repository_context

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


STRICT_PROMPT = """
You are an expert software engineer working in an advanced Multi-File Workspace Engine.

TARGET_FILE:
<file path or list of active paths>

EXPLANATION:
<brief explanation>

FIXED_CODE:
<complete fixed code content block>

IMPORTANT:
- Return the SMALLEST possible fix.
- Prefer function-level patches.
- Never regenerate an entire file when a function-level change is sufficient.

SYNTAX INTEGRITY MANDATE:
- Every string, bracket, and brace MUST be closed.
- Output MUST be valid Python code. 
- NEVER include conversational text outside the defined sections.
- NEVER use markdown code blocks.
- If your generated code causes a SyntaxError, the entire task is considered failed.

RULES FOR MULTI-FILE EDITING:
- Partition each file inside FIXED_CODE using: # FILE: filename.py
- ONLY return raw code.
- FIXED_CODE must be MULTI-LINE.
"""

def build_prompt(issue: str, code: str, file_name: str, error: str = "", context: dict = None) -> str:
    context_text = ""
    if context:
        context_blocks = []
        if not any(isinstance(v, dict) for v in context.values()):
            context = {file_name: context}
        for fname, ctx in context.items():
            imports_str = "\n".join([f"- {imp}" for imp in ctx.get("imports", [])]) or "None"
            callers_str = "\n".join([f"- {caller}" for caller in ctx.get("callers", [])]) or "None"
            related_str = "\n".join([f"- {f}" for f in ctx.get("related_files", [])]) or "None"
            usages_str = "\n".join([f"- {usage}" for usage in ctx.get("usages", [])]) or "None"
            context_blocks.append(
                f"REPOSITORY PROFILE: {fname}\n"
                f"IMPORTS:\n{imports_str}\n"
                f"RELATED FILES:\n{related_str}\n"
                f"CALLERS:\n{callers_str}\n"
                f"USAGES:\n{usages_str}"
            )
        context_text = "\n===\n".join(context_blocks)

    return f"""
{context_text}

ISSUE TO REPAIR:
{issue}

CURRENT ACTIVE SCOPE FILES CONTENT:
{code}

RUNTIME ERROR:
{error}

Follow the rules defined in the system prompt precisely.
"""

def clean_response(text: str) -> str:
    if not text: return ""
    text = text.replace("```python", "").replace("```", "")
    return text.strip()

def is_valid_response(response: str) -> bool:
    return response and len(response.strip()) >= 20 and "FIXED_CODE:" in response

def normalize_response(response: str, file_name: str) -> str:
    if "TARGET_FILE:" not in response:
        return f"TARGET_FILE: {file_name}\nFIXED_CODE:\n{response}"
    return response

def call_llm(prompt: str, model="llama-3.1-8b-instant", system_prompt=None, task_id=None) -> str:
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt or STRICT_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2, "max_tokens": 1000, "stream": False
    }
    response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=60)
    if response.status_code == 429: raise Exception("RATE_LIMIT")
    return clean_response(response.json()["choices"][0]["message"]["content"])

# def call_with_fallback(prompt: str, file_name: str, task_id=None) -> str:
#     for model in ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]:
#         try:
#             response = call_llm(prompt, model, task_id=task_id)
#             if is_valid_response(response):
#                 return normalize_response(response, file_name)
#         except Exception as e:
#             log(task_id, f"MODEL_FAILED {model}: {repr(e)}")
#             continue
#     raise Exception("All models failed")


def call_with_fallback(
    prompt: str,
    file_name: str,
    task_id=None
) -> str:

    models = [
        "llama-3.1-8b-instant",
        "llama-3.3-70b-versatile"
    ]

    last_error = None

    for model in models:

        try:

            log(task_id, f"TRYING_MODEL={model}")

            response = call_llm(
                prompt,
                model,
                task_id=task_id
            )

            log(
                task_id,
                f"MODEL_RESPONSE_LEN={len(response) if response else 0}"
            )

            if is_valid_response(response):

                return normalize_response(
                    response,
                    file_name
                )

        except Exception as e:

            last_error = e

            log(
                task_id,
                f"MODEL_FAILED {model}: {repr(e)}"
            )

            if "RATE_LIMIT" in str(e):
                time.sleep(10)

            continue

    raise Exception(
        f"All models failed. Last error: {repr(last_error)}"
    )


def generate_fix(issue: str, code: str, file_name: str, error: str = "", context: dict = None, task_id=None) -> str:
    prompt = build_prompt(issue, code, file_name, error, context)
    return call_with_fallback(prompt, file_name, task_id=task_id)























