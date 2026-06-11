# import os
# from app.services.repo_cloner import clone_repo
# from app.store.task_store import update_task, add_log
# from app.agent.retry_loop import run_agent
# from app.utils.diff_utils import generate_diff

# BASE_DIR = r"C:\Users\user\Desktop\githubaiagent\workspace"

# def run_agent_async(task_id, request):
#     try:
#         # ================================
#         # 🚀 INIT
#         # ================================
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

#         # ================================
#         # INPUT MODE DETECTION
#         # ================================
#         working_dir = BASE_DIR
#         file_name = None
#         repo_path = None

#         if request.code:
#             mode = "snippet"
#             file_name = "snippet.py"
#         elif request.repo_url:
#             mode = "repo"
#             repo_path = clone_repo(request.repo_url)
#             add_log(task_id, f"📦 Repo cloned: {repo_path}")
#             file_name = None
#         elif request.file_name:
#             mode = "workspace"
#             file_name = request.file_name
#         else:
#             raise Exception("No valid input supplied")

#         add_log(task_id, f"🎯 MODE: {mode}")
        
#         # Determine the directory the agent should operate in
#         agent_base_dir = BASE_DIR
#         if mode == "repo":
#             agent_base_dir = repo_path
        
#         working_dir = agent_base_dir
#         file_path = os.path.join(working_dir, file_name) if file_name else None

#         # ================================
#         # 📖 STEP 2: Read original code
#         # ================================
#         original_code = ""
#         if file_path and os.path.exists(file_path):
#             try:
#                 with open(file_path, "r", encoding="utf-8") as f:
#                     original_code = f.read()
#                 add_log(task_id, f"📂 Loaded file: {file_path}")
#             except Exception as e:
#                 add_log(task_id, f"⚠️ Could not read file: {e}")
#         else:
#             original_code = request.code or ""
#             if not request.code:
#                 add_log(task_id, "⚠️ No local file found, no snippet provided")

#         # ================================
#         # 🤖 STEP 3: Run agent
#         # ================================
#         update_task(task_id, {"current_step": "AGENT_LOOP"})

#         result = run_agent(
#             base_dir=agent_base_dir,
#             file_name=file_name,
#             issue=request.issue,
#             code=request.code,
#             task_id=task_id
#         )

#         # ================================
#         # ❌ STEP 4: VALIDATION
#         # ================================
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
#         if not fixed_code and result.get("final_status") == "success":
#             add_log(task_id, "❌ No fixed_code returned from agent")
#             update_task(task_id, {"status": "failed", "current_step": "NO_FIX_GENERATED", "result": result})
#             return

#         # 🔥 STRICT EXECUTION VALIDATION
#         execution_output = result.get("execution_output", {})
#         return_code = execution_output.get("return_code")
#         stderr = execution_output.get("stderr", "")

#         if result.get("final_status") == "no_change":
#             update_task(task_id, {"status": "no_change", "current_step": "NO_CHANGE", "result": result})
#             add_log(task_id, "ℹ️ No fix needed")
#             return

#         if return_code is None:
#             add_log(task_id, "⚠️ Missing execution return code, rejecting fix")
#             update_task(task_id, {"status": "failed", "current_step": "INVALID_EXECUTION_DATA", "result": result})
#             return

#         runtime_error_keywords = ["traceback", "syntaxerror", "typeerror", "valueerror", "zerodivisionerror", "nameerror", "indexerror", "keyerror", "attributeerror", "modulenotfounderror", "importerror", "assertionerror", "runtimeerror", "memoryerror", "recursionerror", "filenotfounderror", "permissionerror"]
#         has_runtime_error = any(kw in stderr.lower() for kw in runtime_error_keywords)

#         if return_code != 0 and has_runtime_error:
#             add_log(task_id, f"❌ Rejecting invalid fix | return_code={return_code} | has_runtime_error={has_runtime_error}")
#             update_task(task_id, {"status": "failed", "current_step": "INVALID_FIX_REJECTED", "result": result})
#             return

#         # ================================
#         # ✅ STEP 5: SUCCESS FLOW
#         # ================================
#         if result.get("final_status") == "success":
#             add_log(task_id, "🧩 Generating diff...")
#             try:
#                 diff_str = generate_diff(original_code, fixed_code)
#             except Exception as e:
#                 diff_str = ""
#                 add_log(task_id, f"⚠️ Diff generation failed: {str(e)}")

#             update_task(task_id, {
#                 "original_code": original_code,
#                 "fixed_code": fixed_code,
#                 "diff": diff_str,
#                 "result": result,
#                 "status": "success",
#                 "current_step": "COMPLETED"
#             })
#             add_log(task_id, "✅ Completed successfully")

#     except Exception as e:
#         update_task(task_id, {"status": "failed", "current_step": "CRITICAL_ERROR", "result": None})
#         add_log(task_id, f"💥 Critical error: {str(e)}")




import os
from app.services.repo_cloner import clone_repo
from app.store.task_store import update_task, add_log
from app.agent.retry_loop import run_agent
from app.utils.diff_utils import generate_diff

BASE_DIR = r"C:\Users\user\Desktop\githubaiagent\workspace"

def run_agent_async(task_id, request):
    try:
        # ================================
        # 🚀 INIT
        # ================================
        update_task(task_id, {
            "current_step": "INITIALIZING",
            "status": "running",
            "logs": [],
            "attempts": [],
            "execution_steps": []
        })

        add_log(task_id, "🚀 Starting agent...")
        add_log(task_id, f"DEBUG CWD: {os.getcwd()}")
        add_log(task_id, f"DEBUG BASE_DIR: {BASE_DIR}")

        # ================================
        # INPUT MODE DETECTION
        # ================================
        file_name = None
        repo_path = None

        if request.code:
            mode = "snippet"
            file_name = "snippet.py"
        elif request.repo_url:
            mode = "repo"
            repo_path = clone_repo(request.repo_url)
            add_log(task_id, f"📦 Repo cloned: {repo_path}")
            file_name = None
        elif request.file_name:
            mode = "workspace"
            file_name = request.file_name
        else:
            raise Exception("No valid input supplied")

        add_log(task_id, f"🎯 MODE: {mode}")
        
        # Determine the directory the agent should operate in
        agent_base_dir = repo_path if mode == "repo" else BASE_DIR
        
        file_path = os.path.join(agent_base_dir, file_name) if file_name else None

        # ================================
        # 📖 STEP 2: Read original code
        # ================================
        original_code = ""
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    original_code = f.read()
                add_log(task_id, f"📂 Loaded file: {file_path}")
            except Exception as e:
                add_log(task_id, f"⚠️ Could not read file: {e}")
        else:
            original_code = request.code or ""
            if not request.code:
                add_log(task_id, "⚠️ No local file found, no snippet provided")

        # ================================
        # 🤖 STEP 3: Run agent
        # ================================
        update_task(task_id, {"current_step": "AGENT_LOOP"})

        result = run_agent(
            base_dir=agent_base_dir,
            file_name=file_name,
            issue=request.issue,
            code=request.code,
            task_id=task_id
        )

        # ================================
        # ❌ STEP 4: VALIDATION
        # ================================
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
        if not fixed_code and result.get("final_status") == "success":
            add_log(task_id, "❌ No fixed_code returned from agent")
            update_task(task_id, {"status": "failed", "current_step": "NO_FIX_GENERATED", "result": result})
            return

        # 🔥 STRICT EXECUTION VALIDATION
        execution_output = result.get("execution_output", {})
        return_code = execution_output.get("return_code")
        stderr = execution_output.get("stderr", "")

        if result.get("final_status") == "no_change":
            update_task(task_id, {"status": "no_change", "current_step": "NO_CHANGE", "result": result})
            add_log(task_id, "ℹ️ No fix needed")
            return

        if return_code is None:
            add_log(task_id, "⚠️ Missing execution return code, rejecting fix")
            update_task(task_id, {"status": "failed", "current_step": "INVALID_EXECUTION_DATA", "result": result})
            return

        runtime_error_keywords = ["traceback", "syntaxerror", "typeerror", "valueerror", "zerodivisionerror", "nameerror", "indexerror", "keyerror", "attributeerror", "modulenotfounderror", "importerror", "assertionerror", "runtimeerror", "memoryerror", "recursionerror", "filenotfounderror", "permissionerror"]
        has_runtime_error = any(kw in stderr.lower() for kw in runtime_error_keywords)

        if return_code != 0 and has_runtime_error:
            add_log(task_id, f"❌ Rejecting invalid fix | return_code={return_code} | has_runtime_error={has_runtime_error}")
            update_task(task_id, {"status": "failed", "current_step": "INVALID_FIX_REJECTED", "result": result})
            return

        # ================================
        # ✅ STEP 5: SUCCESS FLOW
        # ================================
        if result.get("final_status") == "success":
            add_log(task_id, "🧩 Generating diff...")
            try:
                diff_str = generate_diff(original_code, fixed_code)
            except Exception as e:
                diff_str = ""
                add_log(task_id, f"⚠️ Diff generation failed: {str(e)}")

            update_task(task_id, {
                "original_code": original_code,
                "fixed_code": fixed_code,
                "diff": diff_str,
                "result": result,
                "status": "success",
                "current_step": "COMPLETED"
            })
            add_log(task_id, "✅ Completed successfully")

    except Exception as e:
        update_task(task_id, {"status": "failed", "current_step": "CRITICAL_ERROR", "result": None})
        add_log(task_id, f"💥 Critical error: {str(e)}")













