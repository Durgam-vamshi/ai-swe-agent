import os
import re
import time
from app.services.ast_validator import validate_no_regression
from app.agent.nodes.apply_fix import apply_fix
from app.services.bug_locator import locate_bug_files
from app.agent.nodes.output_parser import parse_llm_response
from app.agent.nodes.multi_file_parser import parse_multi_file
from app.services.context_builder import build_repository_context
from app.services.docker_runner import run_python_file
from app.services.llm_client import generate_fix
from app.services.fix_scope_validator import validate_fix_scope
from app.store.task_store import increment_attempt
from app.utils.logger import log
from app.services.code_search import get_python_files

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
        # Preserve file boundaries for multi-file parsing
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






# def run_agent(base_path=None, file_name=None, issue=None, max_retries=3, task_id=None, **kwargs):
#     MAX_FILE_CHARS = 10000 
    
#     if base_path is None:
#         base_path = kwargs.get("base_dir")
    
#     if not base_path:
#         return {"final_status": "failed", "error": "Missing base path or base directory"}
    
#     incoming_code = kwargs.get("code")

#     if incoming_code and file_name:
#         initial_path = os.path.join(base_path, file_name)
#         os.makedirs(os.path.dirname(initial_path), exist_ok=True)
#         with open(initial_path, "w", encoding="utf-8") as f:
#             f.write(incoming_code)
#         log(task_id, f"✅ Created snippet file: {initial_path}")

#     try:
#         max_retries = int(max_retries)
#     except Exception:
#         max_retries = 3

#     logs = []
#     last_fixed_code = None
#     last_explanation = None
#     original_codes = {}
#     target_function = None
#     func_match = re.search(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\)", issue)
#     if func_match:
#         target_function = func_match.group(1)

#     attempt = 1
#     while attempt <= max_retries:
#         try:
#             if task_id:
#                 increment_attempt(task_id)
#             log(task_id, f"🚀 ATTEMPT {attempt}")

#             # 1. DISCOVERY LOGIC
#             if incoming_code:
#                 target_files = [file_name]
#             elif file_name is None:
#                 target_files = locate_bug_files(issue=issue, target_file="", base_path=base_path)
#                 if not target_files:
#                     target_files = get_python_files(base_path)[:2]
#             else:
#                 target_files = locate_bug_files(issue=issue, target_file=os.path.join(base_path, file_name), base_path=base_path)
#                 if not target_files:
#                     target_files = [file_name]

#             if not target_files:
#                 attempt += 1
#                 continue

#             combined_current_code_blocks = []
#             context = {}

#             for target in target_files:
#                 log(task_id, f"DEBUG file={target} length={len(file_code)}")
#                 target_path = os.path.join(base_path, target)
#                 if os.path.exists(target_path) and target not in original_codes:
#                     with open(target_path, "r", encoding="utf-8") as f:
#                         original_codes[target] = f.read()[:MAX_FILE_CHARS]
#                         log(
#                             task_id,
#                             f"DEBUG FILE {target} LEN={len(original_codes[target])}"
#                         )
                
#                 file_code = last_fixed_code if (len(target_files) == 1 and last_fixed_code) else original_codes.get(target, "")
#                 combined_current_code_blocks.append(f"# FILE: {target}\n{file_code}")
#                 file_context = build_repository_context(target_file=target_path, base_path=base_path, function_name=target_function)
#                 if file_context:
#                     context[target] = file_context

#             current_code = "\n\n".join(combined_current_code_blocks)
#             log(task_id, f"DEBUG current_code_length={len(current_code)}")
#             log(task_id, f"DEBUG target_files={target_files}")
#             log(task_id, f"DEBUG current_code_length={len(current_code)}")
#             response = generate_fix(issue=issue, code=current_code, file_name=", ".join(target_files), context=context, task_id=task_id)
            
#             if not response:
#                 raise Exception("Empty response from LLM")

#             response = normalize_response(response, file_name)
#             parsed = parse_llm_response(response)
#             fixed_code = clean_code(parsed.get("fixed_code", ""))
            
#             if fixed_code.strip() == current_code.strip():
#                 log(task_id, "NO_CHANGE_DETECTED")
#                 return {
#                    "final_status": "no_change",
#                    "reason": "LLM returned identical code"
#                 }
            
#             # --- Multi-file parsing ---
#             parsed_files = parse_multi_file(parsed.get("fixed_code", ""))
#             log(task_id, f"DEBUG parsed_files={list(parsed_files.keys())}")
            
#             # Change #1: Added logging for parsed files
#             log(task_id, f"PARSED FILE COUNT: {len(parsed_files)}")
#             for filename, code in parsed_files.items():
#                 log(task_id, f"FILE: {filename}")
#                 log(task_id, f"CODE LENGTH: {len(code)}")
#                 log(task_id, code[:1000])
            
#             log(task_id, "===== FIXED CODE START =====")
#             log(task_id, fixed_code[:3000])
#             log(task_id, "===== FIXED CODE END =====")

#             # --- Multi-file Scope Validation ---
#             scope_passed = True
#             for filename, code in parsed_files.items():
#                 result = validate_fix_scope("", code)
                
#                 # Change #2: Added logging for scope validation
#                 log(task_id, f"SCOPE RESULT FOR {filename}")
#                 log(task_id, str(result))
                
#                 if not result.get("valid", True):
#                     log(task_id, f"SCOPE FAIL: {filename}")
#                     scope_passed = False
#                     break
            
#             if not scope_passed:
#                 attempt += 1
#                 continue
            
#             log(task_id, "DEBUG scope validation passed")

#             # REGRESSION VALIDATION
#             regression_result = validate_no_regression(current_code, fixed_code)
#             if not regression_result.get("valid", True):
#                 attempt += 1
#                 continue
#             log(task_id, "DEBUG regression validation passed")

#             last_fixed_code = fixed_code
#             last_explanation = parsed.get("explanation")

#             # --- Multi-file Apply Fix ---
#             for filename, code in parsed_files.items():
#                 apply_fix(base_path, filename, code)

#             # Execution (Using the first file for testing as before)
#             test_file = list(parsed_files.keys())[0]
#             temp_file = os.path.join(base_path, f"temp_{test_file}")
            
#             # Change #3: Added directory creation for temp file path
#             os.makedirs(os.path.dirname(temp_file), exist_ok=True)
            
#             with open(temp_file, "w", encoding="utf-8") as f:
#                 f.write(parsed_files[test_file])
            
#             result = run_python_file(base_path, f"temp_{test_file}", extract_args(response), task_id)
            
#             if result.get("return_code") == 0:
#                 return {
#                     "final_status": "success",
#                     "files_updated": list(parsed_files.keys()),
#                     "execution_output": result,
#                     "explanation": last_explanation,
#                     "logs": logs
#                 }
            
#             attempt += 1

#         except Exception as e:
#             if "RATE_LIMIT" in str(e):
#                 time.sleep(15)
#                 continue
#             log(task_id, f"💥 CRASH: {str(e)}")
#             attempt += 1

#     return {"final_status": "failed", "logs": logs}








def run_agent(base_path=None, file_name=None, issue=None, max_retries=3, task_id=None, **kwargs):
    MAX_FILE_CHARS = 10000 
    
    if base_path is None:
        base_path = kwargs.get("base_dir")
    
    if not base_path:
        return {"final_status": "failed", "error": "Missing base path or base directory"}
    
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
                file_code = ""
                target_path = os.path.join(base_path, target)
                
                # Debug logging for path resolution
                log(task_id, f"DEBUG BASE_PATH={base_path}")
                log(task_id, f"DEBUG SELECTED_FILE={target}")
                log(task_id, f"DEBUG FULL_PATH={target_path}")
                log(task_id, f"DEBUG PATH_EXISTS={os.path.exists(target_path)}")

                if os.path.exists(target_path):
                    with open(target_path, "r", encoding="utf-8") as f:
                        file_code = f.read()[:MAX_FILE_CHARS]
                
                # Validation: If we aren't using a previous fix, we MUST have code
                if not file_code and not (len(target_files) == 1 and last_fixed_code):
                    log(task_id, f"FILE_NOT_FOUND_OR_EMPTY={target_path}")
                    raise Exception(f"Could not load source file: {target_path}")
                
                log(task_id, f"DEBUG FILE {target} LEN={len(file_code)}")
                
                current_block_code = last_fixed_code if (len(target_files) == 1 and last_fixed_code) else file_code
                combined_current_code_blocks.append(f"# FILE: {target}\n{current_block_code}")
                
                file_context = build_repository_context(target_file=target_path, base_path=base_path, function_name=target_function)
                if file_context:
                    context[target] = file_context

            current_code = "\n\n".join(combined_current_code_blocks)
            log(task_id, f"DEBUG current_code_length={len(current_code)}")
            
            response = generate_fix(issue=issue, code=current_code, file_name=", ".join(target_files), context=context, task_id=task_id)
            
            if not response:
                raise Exception("Empty response from LLM")

            response = normalize_response(response, file_name)
            parsed = parse_llm_response(response)
            fixed_code = clean_code(parsed.get("fixed_code", ""))
            
            if fixed_code.strip() == current_code.strip():
                log(task_id, "NO_CHANGE_DETECTED")
                return {"final_status": "no_change", "reason": "LLM returned identical code"}
            
            # --- Multi-file parsing ---
            parsed_files = parse_multi_file(parsed.get("fixed_code", ""))
            log(task_id, f"PARSED FILE COUNT: {len(parsed_files)}")
            
            # --- Multi-file Scope Validation ---
            scope_passed = True
            for filename, code in parsed_files.items():
                result = validate_fix_scope("", code)
                log(task_id, f"SCOPE RESULT FOR {filename}: {result}")
                if not result.get("valid", True):
                    scope_passed = False
                    break
            
            if not scope_passed:
                attempt += 1
                continue

            # REGRESSION VALIDATION
            regression_result = validate_no_regression(current_code, fixed_code)
            if not regression_result.get("valid", True):
                attempt += 1
                continue

            last_fixed_code = fixed_code
            last_explanation = parsed.get("explanation")

            # --- Multi-file Apply Fix ---
            for filename, code in parsed_files.items():
                apply_fix(base_path, filename, code)

            # Execution
            test_file = list(parsed_files.keys())[0]
            temp_file = os.path.join(base_path, f"temp_{test_file}")
            os.makedirs(os.path.dirname(temp_file), exist_ok=True)
            
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(parsed_files[test_file])
            
            result = run_python_file(base_path, f"temp_{test_file}", extract_args(response), task_id)
            
            if result.get("return_code") == 0:
                return {
                    "final_status": "success",
                    "files_updated": list(parsed_files.keys()),
                    "execution_output": result,
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













































