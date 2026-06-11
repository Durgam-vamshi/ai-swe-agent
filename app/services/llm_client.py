


import os
import re
import time
from app.utils.logger import log
import requests
from dotenv import load_dotenv

# Import the new context builder service
from app.services.context_builder import build_repository_context

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


STRICT_PROMPT = """
You are an expert software engineer working in an advanced Multi-File Workspace Engine environment.

You MUST follow this STRICT output format EXACTLY. Do not deviate under any circumstance.

TARGET_FILE:
<file path or list of active paths>

EXPLANATION:
<brief explanation>

FIXED_CODE:
<complete fixed code content block>

RULES FOR MULTI-FILE EDITING:
- If modifying multiple files, you MUST partition each file inside the FIXED_CODE section using the exact syntax:
  # FILE: filename.py
  <source code here>
  # FILE: second_file.py
  <source code here>
- Do NOT add extra conversation or chit-chat text.
- Do NOT explain outside sections.
- Do NOT use markdown code blocks like ``` or ```python inside FIXED_CODE.
- ONLY return raw code.
- FIXED_CODE must be MULTI-LINE with each line on a new line.
"""


def build_prompt(
    issue: str,
    code: str,
    file_name: str,
    error: str = "",
    context: dict = None,
) -> str:

    context_text = ""

    if context:
        # Build multi-file specific repository overview if contextual mapping exists
        context_blocks = []
        # Support context handling for single or multiple files dynamically
        if not any(isinstance(v, dict) for v in context.values()):
            # Fallback for standard single-file structure dicts
            context = {file_name: context}

        for fname, ctx in context.items():
            imports_str = "\n".join([f"- {imp}" for imp in ctx.get("imports", [])]) or "None"
            callers_str = "\n".join([f"- {caller}" for caller in ctx.get("callers", [])]) or "None"
            related_str = "\n".join([f"- {f}" for f in ctx.get("related_files", [])]) or "None"
            usages_str = "\n".join([f"- {usage}" for usage in ctx.get("usages", [])]) or "None"

            context_blocks.append(f"""
REPOSITORY PROFILE: {fname}
IMPORTS:
{imports_str}
RELATED FILES:
{related_str}
CALLERS:
{callers_str}
USAGES:
{usages_str}""")
        
        context_text = "\n===\n".join(context_blocks)

    return f"""
{context_text}

You are an expert Python multi-file debugger and workspace engine.

IMPORTANT WORKSPACE SCOPE:
TARGET_FILES TO REMEDIATE: {file_name}

ISSUE TO REPAIR:
{issue}

CURRENT ACTIVE SCOPE FILES CONTENT:
{code}

RUNTIME ERROR ENCOUNTERED:
{error}

CRITICAL VERIFICATION RULES:
1. FIRST inspect the provided source code blocks.
2. If the provided code snippet does not contain enough information to verify the bug exists, return the original code unchanged.
3. Never create new files.
4. Never create new classes.
5. Never create new methods.
6. Never modify code outside the supplied snippets.
7. If the bug cannot be proven from the supplied code, return the original code unchanged.

BEFORE WRITING FIXED_CODE:
1. Identify exact buggy line.
2. Explain why it is buggy.
3. If exact buggy line cannot be identified, return the original code unchanged.

CODE CHANGE RULES:
- Fix ONLY the real bug.
- Keep changes clean, direct, and minimal.
- Do NOT introduce new bugs or regressions.
- Ensure all variables/imports scale correctly across definitions.

WHEN PRODUCING CHANGES FOR MULTIPLE FILES:
You must structure the FIXED_CODE segment cleanly by using inline file paths headers like this:
# FILE: first_filename.py
<code>
# FILE: second_filename.py
<code>

OUTPUT FORMAT MANDATE:
TARGET_FILE: {file_name}

EXPLANATION:
<brief explanation>

FIXED_CODE:
<complete fixed code block or partitioned layout blocks>
"""


def clean_response(text: str) -> str:
    if not text:
        return ""

    text = text.replace("```python", "").replace("```", "")
    text = text.replace("\\n", "\n")
    return text.strip()


def is_valid_response(response: str) -> bool:
    if not response or len(response.strip()) < 20:
        return False

    if "FIXED_CODE:" in response:
        return True

    if "def " in response or "import " in response:
        return True

    return False


def normalize_response(response: str, file_name: str) -> str:
    if "TARGET_FILE:" not in response:
        return f"TARGET_FILE: {file_name}\nFIXED_CODE:\n{response}"

    if "FIXED_CODE:" not in response:
        parts = response.split("\n", 1)
        code_part = parts[-1] if len(parts) > 1 else response
        return f"TARGET_FILE: {file_name}\nFIXED_CODE:\n{code_part}"

    return response


def call_llm(
    prompt: str,
    model="llama-3.1-8b-instant",
    system_prompt=None,
    task_id=None
) -> str:

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt or STRICT_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2,
        "max_tokens": 2500,
        "stream": False
    }

    for attempt in range(3):

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=60
        )

        if response.status_code == 429:

            log(
                task_id,
                f"RATE_LIMIT model={model} attempt={attempt+1}"
            )

            time.sleep(15)

            continue

        if response.status_code != 200:

            raise Exception(
                f"HTTP_{response.status_code}: {response.text}"
            )

        data = response.json()

        return clean_response(
            data["choices"][0]["message"]["content"]
        )

    raise Exception("RATE_LIMIT")


def call_with_fallback(prompt: str, file_name: str, task_id=None) -> str:
    models = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]
    last_error = None

    for model in models:
        try:
            print(f"🧠 Trying model: {model}")
            log(task_id, f"DEBUG FINAL PROMPT LEN={len(prompt)}")
            response = call_llm(prompt, model, task_id=task_id)
            
            # Debug logging
            log(task_id, f"MODEL_RESPONSE_LEN={len(response)}")
            log(task_id, f"MODEL_RESPONSE_HEAD={response[:500]}")

            # Temporary fix for validation
            if response and len(response.strip()) > 50:
                final = normalize_response(response, file_name)
                print("🧩 NORMALIZED RESPONSE:", final)
                return final

            print(f"⚠️ Invalid response from {model}, trying next...")

        except Exception as e:
            print(f"❌ {model} failed: {e}")
            last_error = e
            
            if "RATE_LIMIT" in str(e):
                print(f"⚠️ Rate limit (429) hit on {model}. Pausing for 10s before fallback...")
                time.sleep(10)
                continue 

        time.sleep(0.5)

    raise Exception(f"❌ All models failed. Last error: {last_error}")


def generate_fix(
    issue: str, code: str, file_name: str, error: str = "", context: dict = None, task_id=None
) -> str:
    print("=" * 50)
    print("REPOSITORY CONTEXT SYSTEM LOG:")
    if context:
        for k, v in context.items():
            print(f"FILE: {k} -> IMPORTS: {v.get('imports', [])}")
    else:
        print("None")
    print("=" * 50)

    prompt = build_prompt(issue, code, file_name, error, context)
    
    print("=" * 50)
    print("FINAL PROMPT")
    print(prompt)
    print("=" * 50)
    
    return call_with_fallback(prompt, file_name, task_id=task_id)





