

# import os
# from app.store.task_store import update_task, add_log
# from app.agent.retry_loop import run_agent
# from app.utils.diff_utils import generate_diff

# BASE_DIR = r"C:\Users\user\Desktop\githubaiagent\workspace"

# def run_agent_async(task_id, request):
#     try:
#         update_task(task_id, {
#             "current_step": "INITIALIZING",
#             "status": "running",
#             "logs": [],
#             "attempts": [],
#             "execution_steps": []
#         })

#         add_log(task_id, "🚀 Starting agent...")
#         add_log(task_id, f"DEBUG CWD: {os.getcwd()}")
#         add_log(task_id, f"DEBUG BASE_DIR: {BASE_DIR}")

#         # Corrected Indentation Block
#         if request.code:
#             mode = "snippet"
#             file_name = "snippet.py"
#         elif request.repo_url:
#             mode = "repo"
#             file_name = "repo_target.py"
#         else:
#             raise Exception("No valid input supplied")
        
#         file_path = os.path.join(BASE_DIR, file_name)

#         # SNIPPET MODE
#         if mode == "snippet":
#             original_code = request.code
#             with open(file_path, "w", encoding="utf-8") as f:
#                 f.write(request.code)
#             add_log(task_id, f"📝 Snippet mode file created: {file_path}")

#         # REPO MODE
#         else:
#             try:
#                 with open(file_path, "r", encoding="utf-8") as f:
#                     original_code = f.read()
#                 add_log(task_id, f"📂 Loaded file: {file_path}")
#             except FileNotFoundError:
#                 original_code = ""
#                 add_log(task_id, f"⚠️ File not found: {file_path}")

#         update_task(task_id, {"current_step": "AGENT_LOOP"})

#         result = run_agent(
#             base_dir=BASE_DIR,
#             file_name=file_name,
#             issue=request.issue,
#             code=request.code,
#             task_id=task_id
#         )

#         if not result:
#             add_log(task_id, "❌ Agent returned no result")
#             update_task(task_id, {"status": "failed", "current_step": "NO_RESULT", "result": None})
#             return

#         add_log(task_id, f"DEBUG final_status={result.get('final_status')}")

#         if result.get("final_status") not in ["success", "no_change"]:
#             add_log(task_id, "🔥 FAILED_BRANCH_REACHED")
#             update_task(task_id, {"status": "failed", "current_step": "FAILED", "result": result})
#             add_log(task_id, "❌ Agent failed after retries")
#             return

#         fixed_code = result.get("fixed_code")
#         if not fixed_code:
#             add_log(task_id, "❌ No fixed_code returned from agent")
#             update_task(task_id, {"status": "failed", "current_step": "NO_FIX_GENERATED", "result": result})
#             return

#         # 🔥 STRICT EXECUTION VALIDATION
#         execution_output = result.get("execution_output", {})
#         return_code = execution_output.get("return_code")
#         stdout = execution_output.get("stdout", "")
#         stderr = execution_output.get("stderr", "")

#         if result.get("final_status") == "no_change":
#             update_task(task_id, {"status": "no_change", "current_step": "NO_CHANGE", "result": result})
#             add_log(task_id, "ℹ️ No fix needed")
#             return

#         if return_code is None:
#             add_log(task_id, "⚠️ Missing execution return code, rejecting fix")
#             update_task(task_id, {"status": "failed", "current_step": "INVALID_EXECUTION_DATA", "result": result})
#             return

#         stderr_lower = stderr.lower()
#         runtime_error_keywords = [
#             "traceback", "syntaxerror", "typeerror", "valueerror",
#             "zerodivisionerror", "nameerror", "indexerror", "keyerror",
#             "attributeerror", "modulenotfounderror", "importerror",
#             "assertionerror", "runtimeerror", "memoryerror",
#             "recursionerror", "filenotfounderror", "permissionerror",
#         ]

#         has_runtime_error = any(k in stderr_lower for k in runtime_error_keywords)

#         if return_code != 0 and has_runtime_error:
#             add_log(task_id, f"❌ Rejecting invalid fix | return_code={return_code}")
#             update_task(task_id, {"status": "failed", "current_step": "INVALID_FIX_REJECTED", "result": result})
#             return

#         # ✅ SUCCESS FLOW
#         if result.get("final_status") == "success":
#             add_log(task_id, "🧩 Generating diff...")
#             try:
#                 diff_source = result.get("localized_original_code", original_code)
#                 diff_str = generate_diff(diff_source, fixed_code)
#             except Exception as e:
#                 diff_str = ""
#                 add_log(task_id, f"⚠️ Diff generation failed: {str(e)}")

#             update_task(task_id, {
#                 "original_code": original_code,
#                 "fixed_code": fixed_code,
#                 "diff": diff_str,
#                 "result": result
#             })
#             update_task(task_id, {"status": "success", "current_step": "COMPLETED"})
#             add_log(task_id, "✅ Completed successfully")
#         else:
#             update_task(task_id, {"status": "failed", "current_step": "FAILED", "result": result})
#             add_log(task_id, "❌ Agent failed after retries")

#     except Exception as e:
#         update_task(task_id, {"status": "failed", "current_step": "CRITICAL_ERROR", "result": None})
#         add_log(task_id, f"💥 Critical error: {str(e)}")



import os
from app.store.task_store import update_task, add_log
from app.agent.retry_loop import run_agent
from app.utils.diff_utils import generate_diff
from app.utils.git_utils import clone_repo  # Assuming this is your helper

BASE_DIR = r"C:\Users\user\Desktop\githubaiagent\workspace"

def run_agent_async(task_id, request):
    try:
        update_task(task_id, {
            "current_step": "INITIALIZING",
            "status": "running",
            "logs": [],
            "attempts": [],
            "execution_steps": []
        })

        add_log(task_id, "🚀 Starting agent...")
        add_log(task_id, f"DEBUG CWD: {os.getcwd()}")

        # INITIALIZATION LOGIC
        mode = None
        file_name = None
        repo_path = None

        if request.code:
            mode = "snippet"
            file_name = "snippet.py"
        elif request.repo_url:
            mode = "repo"
            repo_path = clone_repo(request.repo_url)
            add_log(task_id, f"📂 Repository cloned to: {repo_path}")
        else:
            raise Exception("No valid input supplied")
        
        # PREPARE SNIPPET FILE
        if mode == "snippet":
            file_path = os.path.join(BASE_DIR, file_name)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(request.code)
            add_log(task_id, f"📝 Snippet mode file created: {file_path}")

        update_task(task_id, {"current_step": "AGENT_LOOP"})

        # DYNAMIC AGENT EXECUTION
        if mode == "repo":
            result = run_agent(
                base_dir=repo_path,
                file_name=None,
                issue=request.issue,
                task_id=task_id
            )
        else:
            result = run_agent(
                base_dir=BASE_DIR,
                file_name=file_name,
                issue=request.issue,
                code=request.code,
                task_id=task_id
            )

        if not result:
            add_log(task_id, "❌ Agent returned no result")
            update_task(task_id, {"status": "failed", "current_step": "NO_RESULT", "result": None})
            return

        add_log(task_id, f"DEBUG final_status={result.get('final_status')}")

        if result.get("final_status") not in ["success", "no_change"]:
            add_log(task_id, "🔥 FAILED_BRANCH_REACHED")
            update_task(task_id, {"status": "failed", "current_step": "FAILED", "result": result})
            add_log(task_id, "❌ Agent failed after retries")
            return

        fixed_code = result.get("fixed_code")
        if not fixed_code and mode == "snippet":
            add_log(task_id, "❌ No fixed_code returned from agent")
            update_task(task_id, {"status": "failed", "current_step": "NO_FIX_GENERATED", "result": result})
            return

        # STRICT EXECUTION VALIDATION
        execution_output = result.get("execution_output", {})
        return_code = execution_output.get("return_code")
        stderr = execution_output.get("stderr", "")

        if result.get("final_status") == "no_change":
            update_task(task_id, {"status": "no_change", "current_step": "NO_CHANGE", "result": result})
            add_log(task_id, "ℹ️ No fix needed")
            return

        stderr_lower = stderr.lower()
        runtime_error_keywords = [
            "traceback", "syntaxerror", "typeerror", "valueerror",
            "zerodivisionerror", "nameerror", "indexerror", "keyerror",
            "attributeerror", "modulenotfounderror", "importerror",
            "assertionerror", "runtimeerror", "memoryerror",
            "recursionerror", "filenotfounderror", "permissionerror",
        ]

        has_runtime_error = any(k in stderr_lower for k in runtime_error_keywords)

        if return_code is not None and return_code != 0 and has_runtime_error:
            add_log(task_id, f"❌ Rejecting invalid fix | return_code={return_code}")
            update_task(task_id, {"status": "failed", "current_step": "INVALID_FIX_REJECTED", "result": result})
            return

        # SUCCESS FLOW
        if result.get("final_status") == "success":
            diff_str = ""
            if mode == "snippet":
                add_log(task_id, "🧩 Generating diff...")
                try:
                    original_code = request.code
                    diff_source = result.get("localized_original_code", original_code)
                    diff_str = generate_diff(diff_source, fixed_code)
                except Exception as e:
                    add_log(task_id, f"⚠️ Diff generation failed: {str(e)}")

            update_task(task_id, {
                "fixed_code": fixed_code,
                "diff": diff_str,
                "result": result
            })
            update_task(task_id, {"status": "success", "current_step": "COMPLETED"})
            add_log(task_id, "✅ Completed successfully")
        else:
            update_task(task_id, {"status": "failed", "current_step": "FAILED", "result": result})
            add_log(task_id, "❌ Agent failed after retries")

    except Exception as e:
        update_task(task_id, {"status": "failed", "current_step": "CRITICAL_ERROR", "result": None})
        add_log(task_id, f"💥 Critical error: {str(e)}")