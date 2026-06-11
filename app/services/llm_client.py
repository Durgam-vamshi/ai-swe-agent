

# import os
# import re
# import time
# from app.utils.logger import log
# import requests
# from dotenv import load_dotenv

# from app.services.context_builder import build_repository_context

# load_dotenv()
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# STRICT_PROMPT = """
# You are an expert software engineer working in an advanced Multi-File Workspace Engine environment.
# You MUST follow this STRICT output format EXACTLY. Do not deviate under any circumstance.

# TARGET_FILE:
# <file path or list of active paths>

# EXPLANATION:
# <brief explanation>

# FIXED_CODE:
# <complete fixed code content block>

# RULES FOR MULTI-FILE EDITING:
# - If modifying multiple files, you MUST partition each file inside the FIXED_CODE section using the exact syntax:
#   # FILE: filename.py
#   <source code here>
#   # FILE: second_file.py
#   <source code here>
# - Do NOT add extra conversation or chit-chat text.
# - Do NOT explain outside sections.
# - Do NOT use markdown code blocks like ``` or ```python inside FIXED_CODE.
# - ONLY return raw code.
# - FIXED_CODE must be MULTI-LINE with each line on a new line.
# """

# def build_prompt(
#     issue: str,
#     code: str,
#     file_name: str,
#     error: str = "",
#     context: dict = None,
# ) -> str:

#     context_text = ""

#     if context:

#         context_blocks = []

#         if not any(
#             isinstance(v, dict)
#             for v in context.values()
#         ):
#             context = {file_name: context}

#         for fname, ctx in context.items():

#             imports_str = ", ".join(
#                 ctx.get("imports", [])[:10]
#             ) or "None"

#             related_str = ", ".join(
#                 ctx.get("related_files", [])[:5]
#             ) or "None"

#             callers_str = ", ".join(
#                 ctx.get("callers", [])[:5]
#             ) or "None"

#             usages_str = ", ".join(
#                 ctx.get("usages", [])[:5]
#             ) or "None"

#             context_blocks.append(
#                 f"""
# REPOSITORY PROFILE: {fname}

# IMPORTS:
# {imports_str}

# RELATED FILES:
# {related_str}

# CALLERS:
# {callers_str}

# USAGES:
# {usages_str}
# """
#             )

#         context_text = "\n===\n".join(
#             context_blocks
#         )

#     return f"""
# {context_text}

# You are an expert Python software engineer.

# TARGET FILES:
# {file_name}

# ISSUE:
# {issue}

# CURRENT CODE:
# {code}

# RUNTIME ERROR:
# {error}

# Rules:
# - Fix only the bug.
# - Keep changes minimal.
# - Do not create files.
# - Do not remove existing functions.
# - Return only the required format.

# TARGET_FILE:
# {file_name}

# EXPLANATION:
# <brief explanation>

# FIXED_CODE:
# """


# def clean_response(text: str) -> str:
#     if not text:
#         return ""

#     text = text.replace("```python", "")
#     text = text.replace("```", "")
#     text = text.replace("\\n", "\n")

#     return text.strip()


# def normalize_response(response: str, file_name: str) -> str:
#     if not response:
#         return response

#     if "TARGET_FILE:" not in response:
#         return (
#             f"TARGET_FILE: {file_name}\n"
#             f"EXPLANATION:\nGenerated fix\n\n"
#             f"FIXED_CODE:\n{response}"
#         )

#     if "FIXED_CODE:" not in response:
#         return (
#             f"{response}\n\n"
#             f"FIXED_CODE:\n"
#         )

#     return response


# def call_llm(
#     prompt: str,
#     model="llama-3.1-8b-instant",
#     system_prompt=None,
#     task_id=None
# ) -> str:

#     headers = {
#         "Authorization": f"Bearer {GROQ_API_KEY}",
#         "Content-Type": "application/json"
#     }

#     payload = {
#         "model": model,
#         "messages": [
#             {
#                 "role": "system",
#                 "content": system_prompt or STRICT_PROMPT
#             },
#             {
#                 "role": "user",
#                 "content": prompt
#             }
#         ],
#         "temperature": 0.2,
#         "max_tokens": 2500,
#         "stream": False
#     }

#     for attempt in range(3):

#         response = requests.post(
#             "https://api.groq.com/openai/v1/chat/completions",
#             json=payload,
#             headers=headers,
#             timeout=60
#         )

#         if response.status_code == 429:

#             log(
#                 task_id,
#                 f"RATE_LIMIT model={model} attempt={attempt + 1}"
#             )

#             time.sleep(15)

#             continue

#         if response.status_code != 200:

#             raise Exception(
#                 f"HTTP_{response.status_code}: {response.text}"
#             )

#         data = response.json()

#         return clean_response(
#             data["choices"][0]["message"]["content"]
#         )

#     raise Exception("RATE_LIMIT")



# def call_with_fallback(prompt: str, file_name: str, task_id=None) -> str:
#     # 🔧 Added Prompt Size Guard
#     MAX_PROMPT_LEN = 12000
#     if len(prompt) > MAX_PROMPT_LEN:
#         error_msg = f"PROMPT_TOO_LARGE: Length {len(prompt)} exceeds limit of {MAX_PROMPT_LEN}"
#         log(task_id, f"💥 CRASH: {error_msg}")
#         raise Exception(error_msg)

#     models = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]
#     last_error = None

#     for model in models:
#         try:
#             print(f"🧠 Trying model: {model}")
            
#             # Log only when actively calling LLM for repair
#             log(task_id, f"DEBUG FINAL PROMPT LEN={len(prompt)}")
            
#             response = call_llm(prompt, model, task_id=task_id)
            
#             # Debug logging
#             log(task_id, f"MODEL_RESPONSE_LEN={len(response)}")
#             log(task_id, f"MODEL_RESPONSE_HEAD={response[:500]}")

#             # Temporary fix for validation
#             if response and len(response.strip()) > 50:
#                 final = normalize_response(response, file_name)
#                 print("🧩 NORMALIZED RESPONSE:", final)
#                 return final

#             print(f"⚠️ Invalid response from {model}, trying next...")

#         except Exception as e:
#             print(f"❌ {model} failed: {e}")
#             last_error = e
            
#             if "RATE_LIMIT" in str(e):
#                 print(f"⚠️ Rate limit (429) hit on {model}. Pausing for 10s before fallback...")
#                 time.sleep(10)
#                 continue 

#         time.sleep(0.5)

#     raise Exception(f"❌ All models failed. Last error: {last_error}")




# def generate_fix(
#     issue: str, code: str, file_name: str, error: str = "", context: dict = None, task_id=None
# ) -> str:
#     prompt = build_prompt(issue, code, file_name, error, context)
#     return call_with_fallback(prompt, file_name, task_id=task_id)




import os
import re
import time
import requests
from dotenv import load_dotenv
from app.utils.logger import log
from app.services.context_builder import build_repository_context

# Load environment variables
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

def clean_response(text: str) -> str:
    if not text:
        return ""

    text = text.replace("```python", "")
    text = text.replace("```", "")
    text = text.replace("\\n", "\n")

    return text.strip()


def normalize_response(response: str, file_name: str) -> str:
    if not response:
        return response

    if "TARGET_FILE:" not in response:
        return (
            f"TARGET_FILE: {file_name}\n"
            f"EXPLANATION:\nGenerated fix\n\n"
            f"FIXED_CODE:\n{response}"
        )

    if "FIXED_CODE:" not in response:
        return (
            f"{response}\n\n"
            f"FIXED_CODE:\n"
        )

    return response


def build_prompt(
    issue: str,
    code: str,
    file_name: str,
    error: str = "",
    context: dict = None,
) -> str:

    context_text = ""

    if context:
        context_blocks = []

        if not any(
            isinstance(v, dict)
            for v in context.values()
        ):
            context = {file_name: context}

        for fname, ctx in context.items():
            imports_str = ", ".join(
                ctx.get("imports", [])[:10]
            ) or "None"

            related_str = ", ".join(
                ctx.get("related_files", [])[:5]
            ) or "None"

            callers_str = ", ".join(
                ctx.get("callers", [])[:5]
            ) or "None"

            usages_str = ", ".join(
                ctx.get("usages", [])[:5]
            ) or "None"

            context_blocks.append(
                f"""
REPOSITORY PROFILE: {fname}

IMPORTS:
{imports_str}

RELATED FILES:
{related_str}

CALLERS:
{callers_str}

USAGES:
{usages_str}
"""
            )

        context_text = "\n===\n".join(
            context_blocks
        )

    return f"""
{context_text}

You are an expert Python software engineer.

TARGET FILES:
{file_name}

ISSUE:
{issue}

CURRENT CODE:
{code}

RUNTIME ERROR:
{error}

Rules:
- Fix only the bug.
- Keep changes minimal.
- Do not create files.
- Do not remove existing functions.
- Return only the required format.

TARGET_FILE:
{file_name}

EXPLANATION:
<brief explanation>

FIXED_CODE:
"""


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
                f"RATE_LIMIT model={model} attempt={attempt + 1}"
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
    # 🔧 Added Prompt Size Guard
    MAX_PROMPT_LEN = 12000
    if len(prompt) > MAX_PROMPT_LEN:
        error_msg = f"PROMPT_TOO_LARGE: Length {len(prompt)} exceeds limit of {MAX_PROMPT_LEN}"
        log(task_id, f"💥 CRASH: {error_msg}")
        raise Exception(error_msg)

    models = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]
    last_error = None

    for model in models:
        try:
            print(f"🧠 Trying model: {model}")
            
            # Log only when actively calling LLM for repair
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
    prompt = build_prompt(issue, code, file_name, error, context)
    return call_with_fallback(prompt, file_name, task_id=task_id)












