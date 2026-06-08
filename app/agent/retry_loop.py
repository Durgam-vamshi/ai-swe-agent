from app.services.ast_validator import validate_no_regression
from app.agent.nodes.apply_fix import apply_fix
from app.services.bug_locator import locate_bug_files

import os
import re
import time
from app.agent.nodes.apply_fix import apply_fix
from app.agent.nodes.error_classifier import classify_error
from app.agent.nodes.output_parser import parse_llm_response
from app.services.context_builder import build_repository_context
from app.services.docker_runner import run_python_file
from app.services.llm_client import generate_fix
from app.services.fix_scope_validator import validate_fix_scope
from app.store.task_store import increment_attempt
from app.utils.logger import log


# =========================
# 🔧 HELPERS
# =========================
def extract_args(response_text: str):
    for line in response_text.splitlines():
        if line.startswith("ARGS:"):
            value = line.replace("ARGS:", "").strip()
            if value.upper() == "NONE":
                return []
            return value.split()
    return []


def clean_code(code: str):
    if not code:
        return ""
    code = code.split("ARGS:")[0]
    code = code.split("RULES:")[0]
    code = code.split("IMPORTANT:")[0]

    lines = code.splitlines()
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("# FILE:"):
            continue
        if stripped.startswith("FILE:"):
            continue
        if stripped.startswith("```"):
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def normalize_response(response: str, file_name: str) -> str:
    if not response or "FIXED_CODE:" not in response:
        return response

    parts = response.split("FIXED_CODE:")
    if len(parts) < 2:
        return response

    code_part = parts[1]

    if "ARGS:" in code_part:
        code_part = code_part.split("ARGS:")[0]

    code_part = code_part.replace("\\n", "\n").strip()

    return f"{parts[0]}FIXED_CODE:\n{code_part}"


def is_valid_python_code(code: str):
    if not code or not code.strip():
        return False

    code = code.strip()
    lower_code = code.lower()

    invalid_phrases = [
        "no changes required",
        "no bug",
        "nothing to fix",
        "the provided code",
        "based on the issue",
        "we can conclude",
        "therefore",
        "looking closely at",
    ]

    for phrase in invalid_phrases:
        if phrase in lower_code:
            return False

    if len(code.splitlines()) == 1 and len(code.split()) > 15:
        return False

    if code.startswith("/") or code.endswith(".py"):
        return False

    if not any(k in code for k in ["def ", "return", "=", "print(", "import"]):
        return False

    return True


def generate_fallback_explanation(issue: str, error_type: str = "Unknown"):
    return {
        "root_cause": error_type if error_type else "Unknown/Implicit Error",
        "fix_summary": f"Attempted structural code remediation for: {issue.splitlines()[0]}",
        "confidence": 0.75,
    }


# =========================
# 🚀 MAIN AGENT LOOP
# =========================




def run_agent(base_path=None, file_name=None, issue=None, max_retries=3, task_id=None, **kwargs):
    # FIX: Map 'base_dir' (passed by API) to 'base_path' if needed
    if base_path is None:
        base_path = kwargs.get("base_dir")
    
    if not base_path:
        return {"final_status": "failed", "error": "Missing base path or base directory"}

    try:
        max_retries = int(max_retries)
    except Exception:
        max_retries = 3

    logs = []
    last_fixed_code = None
    last_explanation = None
    cached_test_suite = None 

    original_codes = {}
    localized_original_codes = {}

    log(task_id, f"📂 Initial target working file: {file_name}")

    initial_path = os.path.join(base_path, file_name)
    if os.path.exists(initial_path):
        try:
            with open(initial_path, "r", encoding="utf-8") as f:
                original_codes[file_name] = f.read()
        except Exception as e:
            log(task_id, f"⚠️ Could not read initial file context: {e}")

    target_function = None
    func_match = re.search(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\)", issue)
    if func_match:
        target_function = func_match.group(1)

    attempt = 1
    while attempt <= max_retries:
        try:
            if task_id:
                increment_attempt(task_id)

            log(task_id, f"🚀 ATTEMPT {attempt}")


            current_target_path = os.path.join(base_path, file_name)
            target_files = locate_bug_files(issue=issue, target_file=current_target_path, base_path=base_path)

            if not target_files:
                target_files = [file_name]

            log(task_id, f"🎯 Workspace scope files localized: {target_files}")

            combined_current_code_blocks = []
            context = {}

            for target in target_files:
                target_path = os.path.join(base_path, target)
                if not os.path.exists(target_path):
                    continue

                if target not in original_codes:
                    try:
                        with open(target_path, "r", encoding="utf-8") as f:
                            original_codes[target] = f.read()
                            localized_original_codes[target] = original_codes[target]
                    except Exception:
                        continue

                if attempt == 1:
                    file_code = original_codes[target]
                else:
                    file_code = last_fixed_code if len(target_files) == 1 else original_codes[target]

                combined_current_code_blocks.append(f"# FILE: {target}\n{file_code}")

                file_context = build_repository_context(target_file=target_path, base_path=base_path, function_name=target_function)
                if file_context:
                    context[target] = file_context

            current_code = "\n\n".join(combined_current_code_blocks)

            if target_function and not any(f"def {target_function}" in block for block in combined_current_code_blocks):
                issue += f"\nIMPORTANT: {target_function}() not found in current scope. Do not hallucinate."

            response = generate_fix(issue=issue, code=current_code, file_name=", ".join(target_files), context=context, task_id=task_id)

            if not response:
                raise Exception("Empty response from LLM")

            response = normalize_response(response, file_name)
            parsed = parse_llm_response(response)
            fixed_code = clean_code(parsed.get("fixed_code", ""))

            if not fixed_code:
                attempt += 1
                continue

            if current_code and fixed_code.strip() == current_code.strip():
                return {"final_status": "no_change", "fixed_code": fixed_code}

            scope_result = validate_fix_scope(current_code, fixed_code)
            if not scope_result.get("valid", True):
                attempt += 1
                continue

            ast_result = validate_no_regression(current_code, fixed_code)
            if not ast_result["valid"]:
                attempt += 1
                continue

            last_fixed_code = fixed_code
            last_explanation = parsed.get("explanation")

            # Sandbox testing logic
            temp_file = os.path.join(base_path, f"temp_{target_files[0]}")
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(fixed_code)
            
            result = run_python_file(base_path, f"temp_{target_files[0]}", extract_args(response), task_id)
            
            if result.get("return_code") == 0:
                # SUCCESS: Apply files
                for target in target_files:
                    apply_fix(base_path, target, fixed_code)
                
                return {
                    "final_status": "success",
                    "files_updated": target_files,
                    "explanation": last_explanation,
                    "logs": logs
                }
            
            attempt += 1

        except Exception as e:
            if "RATE_LIMIT" in str(e):
                time.sleep(15)
                continue
            log(task_id, f"💥 CRASH: {str(e)}")
            attempt += 1

    return {"final_status": "failed", "logs": logs}