import os
import re
import time
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

CRITICAL BUG VERIFICATION RULES:
1. FIRST inspect the provided source code blocks.
2. Verify the reported bug actually exists across the file layout context.
3. Trust the source code over the issue description.
4. Never invent bugs, imports, functions, files, or exceptions.
5. Fix ONLY bugs that are observable in the provided file tracks.
6. If the issue cannot be reproduced or localized, return the original code tracking layout unchanged.

CODE CHANGE RULES:
- Fix ONLY the real bug.
- Keep changes clean, direct, and minimal.
- Do NOT introduction new bugs or regressions.
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


# ==============================
# 🔥 GROQ CALL (WITH 429 DETECTION)
# ==============================
MODEL_PRICING = {
    "llama-3.1-8b-instant": {"input_1k": 0.00005, "output_1k": 0.00008},
    "llama-3.3-70b-versatile": {"input_1k": 0.00059, "output_1k": 0.00079},
}

def call_llm(prompt: str, model="llama-3.1-8b-instant", system_prompt=None, task_id=None) -> str:
    try:
        print(f"🔥 Calling Groq model: {model}")

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt or STRICT_PROMPT,
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 2048,  # Increased to prevent truncation during multi-file content generations
            "stream": False,
        }

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=30,
        )

        if response.status_code == 429:
            raise Exception("RATE_LIMIT")

        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")

        data = response.json()

        if "choices" not in data or len(data["choices"]) == 0:
            raise Exception(f"Invalid Groq response structure: {data}")

        # Usage and telemetry tracking layers
        if "usage" in data and task_id:
            try:
                usage = data["usage"]
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", 0)

                pricing = MODEL_PRICING.get(model, {"input_1k": 0.0, "output_1k": 0.0})
                input_cost = (prompt_tokens / 1000) * pricing["input_1k"]
                output_cost = (completion_tokens / 1000) * pricing["output_1k"]
                total_cost = input_cost + output_cost

                from app.store.task_store import get_task, update_task
                task = get_task(task_id) or {}
                
                current_metrics = task.get("metrics", {"prompt_tokens": 0, "completion_tokens": 0, "total_cost": 0.0})
                
                update_task(task_id, {
                    "metrics": {
                        "prompt_tokens": current_metrics.get("prompt_tokens", 0) + prompt_tokens,
                        "completion_tokens": current_metrics.get("completion_tokens", 0) + completion_tokens,
                        "total_cost": round(current_metrics.get("total_cost", 0.0) + total_cost, 6)
                    }
                })
                
                print(f"💰 [OBSERVABILITY] Task {task_id} | Model: {model} | Run Cost: ${total_cost:.6f} | Total Tokens: {total_tokens}")
            except Exception as metric_err:
                print(f"⚠️ Failed to process tracking telemetry: {metric_err}")

        raw_content = data["choices"][0]["message"]["content"]
        cleaned = clean_response(raw_content)

        print("🧠 RAW LLM RESPONSE:", cleaned)
        print("✅ LLM RESPONSE RECEIVED")

        return cleaned

    except Exception as e:
        print(f"❌ LLM ERROR ({model}): {e}")
        raise

def call_with_fallback(prompt: str, file_name: str, task_id=None) -> str:
    models = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]
    last_error = None

    for model in models:
        try:
            print(f"🧠 Trying model: {model}")
            response = call_llm(prompt, model, task_id=task_id)

            if is_valid_response(response):
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