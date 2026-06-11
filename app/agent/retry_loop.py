
# import os
# import re
# import time
# from app.services.ast_validator import validate_no_regression
# from app.agent.nodes.apply_fix import apply_fix
# from app.services.bug_locator import locate_bug_files
# from app.agent.nodes.output_parser import parse_llm_response
# from app.agent.nodes.multi_file_parser import parse_multi_file
# from app.services.context_builder import build_repository_context
# from app.services.docker_runner import run_python_file
# from app.services.llm_client import generate_fix
# from app.services.fix_scope_validator import validate_fix_scope
# from app.store.task_store import increment_attempt
# from app.utils.logger import log
# from app.services.code_search import get_python_files


# def run_agent(base_path=None, file_name=None, issue=None, max_retries=3, task_id=None, **kwargs):
#     MAX_FILE_CHARS = 2500 
#     MAX_FILES = 3
    
#     if base_path is None:
#         base_path = kwargs.get("base_dir")
#     if not base_path:
#         return {"final_status": "failed", "error": "Missing base path"}

#     # Discovery
#     if kwargs.get("code") and file_name:
#         target_files = [file_name]
#         with open(os.path.join(base_path, file_name), "w", encoding="utf-8") as f:
#             f.write(kwargs.get("code"))
#     else:
#         target_files = locate_bug_files(issue=issue, target_file=file_name or "", base_path=base_path) or get_python_files(base_path)[:MAX_FILES]
    
#     target_files = target_files[:MAX_FILES]

#     # Investigation Detection
#     INVESTIGATION_WORDS = ["investigate", "identify", "locate", "analyze"]
#     if any(word in issue.lower() for word in INVESTIGATION_WORDS):
#         log(task_id, f"🔍 Investigation task detected: {target_files}")
#         return {"final_status": "investigation_complete", "target_files": target_files}

#     # Execution Loop
#     attempt = 1
#     last_fixed_code = None
#     while attempt <= max_retries:
#         try:
#             if task_id: increment_attempt(task_id)
            
#             # Prepare context
#             combined_code, context = [], {}
#             for target in target_files:
#                 path = os.path.join(base_path, target)
#                 with open(path, "r", encoding="utf-8") as f:
#                     content = f.read()[:MAX_FILE_CHARS]
#                 combined_code.append(f"# FILE: {target}\n{content}")
#                 context[target] = build_repository_context(target_file=path, base_path=base_path)

#             # Generate and Parse Fix
#             response = generate_fix(issue=issue, code="\n\n".join(combined_code), file_name=", ".join(target_files), context=context, task_id=task_id)
#             parsed = parse_llm_response(normalize_response(response, file_name))
#             parsed_files = parse_multi_file(parsed.get("fixed_code", ""))

#             # Apply Full Overwrite
#             for filename, full_code in parsed_files.items():
#                 target_path = os.path.join(base_path, filename)
#                 with open(target_path, "w", encoding="utf-8") as f:
#                     f.write(full_code) # Full replacement
#                 log(task_id, f"✅ Fully overwritten: {filename}")

#             # Verify (Run test)
#             test_file = list(parsed_files.keys())[0]
#             result = run_python_file(base_path, test_file, extract_args(response), task_id)
            
#             if result.get("return_code") == 0:
#                 return {"final_status": "success", "files_updated": list(parsed_files.keys())}
            
#             attempt += 1
#         except Exception as e:
#             log(task_id, f"💥 CRASH: {str(e)}")
#             attempt += 1

#     return {"final_status": "failed"}



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


def run_agent(base_path=None, file_name=None, issue=None, max_retries=3, task_id=None, **kwargs):
    MAX_FILE_CHARS = 2500 
    MAX_FILES = 3
    
    if base_path is None:
        base_path = kwargs.get("base_dir")
    if not base_path:
        return {"final_status": "failed", "error": "Missing base path"}

    # Discovery
    if kwargs.get("code") and file_name:
        target_files = [file_name]
        with open(os.path.join(base_path, file_name), "w", encoding="utf-8") as f:
            f.write(kwargs.get("code"))
    else:
        target_files = locate_bug_files(issue=issue, target_file=file_name or "", base_path=base_path) or get_python_files(base_path)[:MAX_FILES]
    
    target_files = target_files[:MAX_FILES]

    # Investigation Detection
    INVESTIGATION_WORDS = ["investigate", "identify", "locate", "analyze"]
    if any(word in issue.lower() for word in INVESTIGATION_WORDS):
        log(
            task_id, 
            f"🔍 Investigation complete. Target files identified: {target_files}"
        )
        return {
            "final_status": "investigation_complete", 
            "target_files": target_files
        }

    # Execution Loop
    attempt = 1
    while attempt <= max_retries:
        try:
            if task_id: increment_attempt(task_id)
            
            # Prepare context
            combined_code, context = [], {}
            for target in target_files:
                path = os.path.join(base_path, target)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()[:MAX_FILE_CHARS]
                combined_code.append(f"# FILE: {target}\n{content}")
                context[target] = build_repository_context(target_file=path, base_path=base_path)

            # Generate and Parse Fix
            response = generate_fix(issue=issue, code="\n\n".join(combined_code), file_name=", ".join(target_files), context=context, task_id=task_id)
            parsed = parse_llm_response(normalize_response(response, file_name))
            parsed_files = parse_multi_file(parsed.get("fixed_code", ""))

            # Apply Full Overwrite
            for filename, full_code in parsed_files.items():
                target_path = os.path.join(base_path, filename)
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(full_code) # Full replacement
                log(task_id, f"✅ Fully overwritten: {filename}")

            # Verify (Run test)
            test_file = list(parsed_files.keys())[0]
            result = run_python_file(base_path, test_file, extract_args(response), task_id)
            
            if result.get("return_code") == 0:
                return {"final_status": "success", "files_updated": list(parsed_files.keys())}
            
            attempt += 1
        except Exception as e:
            log(task_id, f"💥 CRASH: {str(e)}")
            attempt += 1

    return {"final_status": "failed"}



































