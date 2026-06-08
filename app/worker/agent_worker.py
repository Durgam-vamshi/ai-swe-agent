import os
from app.store.task_store import update_task, add_log
from app.agent.retry_loop import run_agent
from app.utils.diff_utils import generate_diff

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../sandbox")
)


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

        # ✅ FIXED: Dynamically capture file name from request
        file_name = request.file_name
        file_path = os.path.join(BASE_DIR, file_name)

        # ================================
        # 📖 STEP 2: Read original code
        # ================================
        try:
            with open(file_path, "r") as f:
                original_code = f.read()

            add_log(task_id, f"📂 Loaded file: {file_path}")

        except FileNotFoundError:
            original_code = request.code or ""
            add_log(task_id, f"⚠️ File not found at {file_path}, using fallback code")

        # ================================
        # 🤖 STEP 3: Run agent
        # ================================
        update_task(task_id, {"current_step": "AGENT_LOOP"})

        # ✅ FIXED: Explicitly pass file_name down to your agent retry loop core
        result = run_agent(
            base_dir=BASE_DIR,
            file_name=file_name,
            issue=request.issue,
            task_id=task_id
        )

        # ================================
        # ❌ STEP 4: VALIDATION (FULL FIX)
        # ================================
        if not result:
            add_log(task_id, "❌ Agent returned no result")

            update_task(task_id, {
                "status": "failed",
                "current_step": "NO_RESULT",
                "result": None
            })
            return

        # 🔍 STRICT PROCESS VERIFICATION LOGS
        add_log(
            task_id,
            f"DEBUG final_status={result.get('final_status')}"
        )

        # Catch exhausted retry agent loops immediately before checking execution payloads
        if result.get("final_status") != "success" and result.get("final_status") != "no_change":
            add_log(task_id, "🔥 FAILED_BRANCH_REACHED")

            update_task(task_id, {
                "status": "failed",
                "current_step": "FAILED",
                "result": result
            })

            add_log(task_id, "❌ Agent failed after retries")
            return

        fixed_code = result.get("fixed_code")

        if not fixed_code:
            add_log(task_id, "❌ No fixed_code returned from agent")

            update_task(task_id, {
                "status": "failed",
                "current_step": "NO_FIX_GENERATED",
                "result": result
            })
            return

        # 🔥 STRICT EXECUTION VALIDATION
        execution_output = result.get("execution_output", {})

        return_code = execution_output.get("return_code")
        stdout = execution_output.get("stdout", "")
        stderr = execution_output.get("stderr", "")

        if result.get("final_status") == "no_change":
            update_task(task_id, {
                "status": "no_change",
                "current_step": "NO_CHANGE",
                "result": result
            })

            add_log(task_id, "ℹ️ No fix needed")
            return

        if return_code is None:
            add_log(task_id, "⚠️ Missing execution return code, rejecting fix")

            update_task(task_id, {
                "status": "failed",
                "current_step": "INVALID_EXECUTION_DATA",
                "result": result
            })
            return

        stderr_lower = stderr.lower()

        runtime_error_keywords = [
            "traceback", "syntaxerror", "typeerror", "valueerror",
            "zerodivisionerror", "nameerror", "indexerror", "keyerror",
            "attributeerror", "modulenotfounderror", "importerror",
            "assertionerror", "runtimeerror", "memoryerror",
            "recursionerror", "filenotfounderror", "permissionerror",
        ]

        has_runtime_error = any(
            keyword in stderr_lower
            for keyword in runtime_error_keywords
        )

        if return_code != 0 and has_runtime_error:
            add_log(
                task_id,
                (
                    f"❌ Rejecting invalid fix | "
                    f"return_code={return_code} | "
                    f"has_runtime_error={has_runtime_error}"
                ),
            )

            update_task(task_id, {
                "status": "failed",
                "current_step": "INVALID_FIX_REJECTED",
                "result": result
            })
            return

        # ================================
        # ✅ STEP 5: SUCCESS FLOW
        # ================================
        if result.get("final_status") == "success":
            add_log(task_id, "🧩 Generating diff...")

            try:
                diff_source = result.get(
                    "localized_original_code",
                    original_code
                )

                diff_str = generate_diff(
                    diff_source,
                    fixed_code
                )
            except Exception as e:
                diff_str = ""
                add_log(task_id, f"⚠️ Diff generation failed: {str(e)}")

            # 🔥 SAVE EVERYTHING (FRONTEND NEEDS THIS)
            update_task(task_id, {
                "original_code": original_code,
                "fixed_code": fixed_code,
                "diff": diff_str,
                "result": result
            })

            update_task(task_id, {
                "status": "success",
                "current_step": "COMPLETED"
            })

            add_log(task_id, "✅ Completed successfully")

        # ================================
        # ❌ FAILURE FLOW (Fallback safeguarding catch-all)
        # ================================
        else:
            update_task(task_id, {
                "status": "failed",
                "current_step": "FAILED",
                "result": result
            })

            add_log(task_id, "❌ Agent failed after retries")

    # ================================
    # 💥 CRITICAL ERROR HANDLER
    # ================================
    except Exception as e:
        update_task(task_id, {
            "status": "failed",
            "current_step": "CRITICAL_ERROR",
            "result": None
        })

        add_log(task_id, f"💥 Critical error: {str(e)}")