


from fastapi import APIRouter, HTTPException
from app.store.task_store import get_task

router = APIRouter()


@router.get("/runs/{run_id}")
def get_run(run_id: str):
    task = get_task(run_id)

    # ❌ Task not found
    if not task:
        raise HTTPException(status_code=404, detail="Run not found")

    # ✅ Safe extraction
    result = task.get("result") or {}

    original_code = task.get("original_code") or ""
    fixed_code = task.get("fixed_code") or ""
    diff = task.get("diff") or ""

    return {
        "data": {
            "id": run_id,
            "status": task.get("status", "unknown"),

            # 🧠 Safe result fields
            "issue": result.get("issue"),

            # 🔁 Retry info
            "attempts": task.get("attempts") or [],

            # 📜 Logs (ensure always array)
            "logs": task.get("logs") or [],

            # 🧠 Execution steps
            "execution_steps": task.get("execution_steps") or [],

            # 🔥 Diff system (critical)
            "original_code": original_code,
            "fixed_code": fixed_code,
            "diff": diff,

            # 🧪 Debug helpers (optional but powerful)
            "meta": {
                "has_diff": bool(diff),
                "has_fixed_code": bool(fixed_code),
                "has_original_code": bool(original_code),
            }
        }
    }