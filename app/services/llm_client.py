# import os
# import re
# import time
# from app.utils.logger import log
# import requests
# from dotenv import load_dotenv

# # Import the new context builder service
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

# # ... [build_prompt, clean_response, is_valid_response, normalize_response, call_llm remain unchanged] ...

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
#     # ... [Implementation remains the same, calling the updated call_with_fallback] ...
#     prompt = build_prompt(issue, code, file_name, error, context)
#     return call_with_fallback(prompt, file_name, task_id=task_id)

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
