


import os
import re
import time
import traceback
from app.services.ast_validator import validate_no_regression
from app.agent.nodes.apply_fix import apply_fix
from app.services.bug_locator import locate_bug_files
from app.agent.nodes.error_classifier import classify_error
from app.agent.nodes.output_parser import parse_llm_response
from app.agent.nodes.multi_file_parser import parse_multi_file
from app.services.context_builder import build_repository_context
from app.services.docker_runner import run_python_file
from app.services.llm_client import generate_fix
from app.services.fix_scope_validator import validate_fix_scope
from app.store.task_store import increment_attempt
from app.utils.logger import log
from app.services.code_search import get_python_files


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

        if (
            stripped.startswith("# FILE:")
            or stripped.startswith("FILE:")
            or stripped.startswith("```")
        ):
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


def run_agent(
    base_path=None,
    file_name=None,
    issue=None,
    max_retries=3,
    task_id=None,
    **kwargs,
):
    MAX_FILE_CHARS = 2500

    if base_path is None:
        base_path = kwargs.get("base_dir")

    if not base_path:
        return {
            "final_status": "failed",
            "error": "Missing base path or base directory",
        }

    incoming_code = kwargs.get("code")

    if incoming_code and file_name:
        initial_path = os.path.join(base_path, file_name)
        os.makedirs(os.path.dirname(initial_path), exist_ok=True)
        with open(initial_path, "w", encoding="utf-8") as f:
            f.write(incoming_code)
        log(task_id, f"✅ Created snippet file: {initial_path}")

    try:
        max_retries = int(max_retries)
    except Exception:
        max_retries = 3

    logs = []
    last_fixed_code = None
    last_explanation = None
    original_codes = {}
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

            # 1. DISCOVERY LOGIC
            if incoming_code:
                target_files = [file_name]
            elif file_name is None:
                target_files = locate_bug_files(issue=issue, target_file="", base_path=base_path)
                if not target_files:
                    target_files = get_python_files(base_path)[:2]
            else:
                target_files = locate_bug_files(issue=issue, target_file=os.path.join(base_path, file_name), base_path=base_path)
                if not target_files:
                    target_files = [file_name]

            if not target_files:
                attempt += 1
                continue

            combined_current_code_blocks = []
            context = {}

            for target in target_files:
                target_path = os.path.join(base_path, target)

                if os.path.exists(target_path) and target not in original_codes:
                    with open(target_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    if len(content) > MAX_FILE_CHARS:
                        content = content[:MAX_FILE_CHARS]

                    original_codes[target] = content
                    log(task_id, f"FILE_CONTEXT_LEN {target}={len(content)}")
                    log(task_id, f"FILE_CONTEXT_END {target}={content[-120:]}")

                file_code = (
                    last_fixed_code
                    if (len(target_files) == 1 and last_fixed_code)
                    else original_codes.get(target, "")
                )

                combined_current_code_blocks.append(f"# FILE: {target}\n{file_code}")

                file_context = build_repository_context(
                    target_file=target_path,
                    base_path=base_path,
                    function_name=target_function,
                )
                if file_context:
                    context[target] = file_context

            current_code = "\n\n".join(combined_current_code_blocks)

            log(task_id, "DEBUG BEFORE_LLM")
            response = generate_fix(
                issue=issue,
                code=current_code,
                file_name=", ".join(target_files),
                context=context,
                task_id=task_id,
            )
            log(task_id, f"DEBUG AFTER_LLM len={len(response) if response else 0}")

            if not response:
                raise Exception("Empty response from LLM")

            response = normalize_response(response, file_name)
            
            log(task_id, "DEBUG BEFORE_PARSE")
            parsed = parse_llm_response(response)
            log(
                task_id,
                f"RAW_FIXED_CODE_PREVIEW={parsed.get('fixed_code','')[:500]}"
            )
            log(task_id, "DEBUG AFTER_PARSE")
            
            fixed_code = clean_code(parsed.get("fixed_code", ""))
            log(task_id, f"DEBUG fixed_code_len={len(fixed_code)}")
            
            import ast
            try:
                ast.parse(fixed_code)
            except Exception as e:
                log(task_id, f"AST_PARSE_FAILED={e}")
                attempt += 1
                continue
            parsed_files = parse_multi_file(parsed.get("fixed_code", ""))
            
            explanation = parsed.get("explanation", "")

            if "BUG_NOT_VERIFIED" in explanation or fixed_code.strip() == current_code.strip():
                return {"final_status": "no_change", "reason": "LLM returned unchanged code or could not verify bug"}

            parsed_files = parse_multi_file(parsed.get("fixed_code", ""))
            log(task_id, f"DEBUG parsed_files_count={len(parsed_files)}")
            log(task_id, f"DEBUG parsed_files={list(parsed_files.keys())}")
            
            allowed_files = set(target_files)
            parsed_files = {file: code for file, code in parsed_files.items() if file in allowed_files}

            if not fixed_code or not parsed_files:
                attempt += 1
                continue

            # SCOPE VALIDATION
            log(task_id, "DEBUG BEFORE_SCOPE")
            scope_passed = True
            for filename, code in parsed_files.items():
                scope_result = validate_fix_scope("", code)
                if not scope_result.get("valid", True):
                    scope_passed = False
                    attempt += 1
                    break
            log(task_id, "DEBUG AFTER_SCOPE")
            if not scope_passed:
                continue

            # REGRESSION VALIDATION
            log(task_id, "DEBUG BEFORE_REGRESSION")
            regression_result = validate_no_regression(current_code, fixed_code)
            log(task_id, f"DEBUG regression_result={regression_result}")
            
            if not regression_result.get("valid", True):
                attempt += 1
                continue

            last_fixed_code = fixed_code
            last_explanation = parsed.get("explanation")

            # APPLY AND EXECUTE
            log(task_id, "DEBUG BEFORE_APPLY")
            for filename, code in parsed_files.items():
                apply_fix(base_path, filename, code)

            test_file = list(parsed_files.keys())[0]
            safe_name = os.path.basename(test_file)
            temp_file = os.path.join(base_path, f"temp_{safe_name}")
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(parsed_files[test_file])

            log(task_id, "DEBUG BEFORE_EXECUTION")
            result = run_python_file(
                base_path=base_path,
                file_name=f"temp_{safe_name}",
                args=extract_args(response),
                task_id=task_id,
                is_repository=True,
            )

            if result.get("return_code") == 0:
                return {
                    "final_status": "success",
                    "files_updated": list(parsed_files.keys()),
                    "execution_output": result,
                    "explanation": last_explanation,
                    "logs": logs,
                }
            attempt += 1

        except Exception as e:
            import traceback
            log(task_id, f"FULL_EXCEPTION={repr(e)}")
            log(task_id, traceback.format_exc())
            
            if "RATE_LIMIT" in str(e):
                time.sleep(15)
                continue
            
            log(task_id, f"💥 CRASH: {str(e)}")
            attempt += 1

    return {"final_status": "failed", "logs": logs}

















































