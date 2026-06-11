

from fastapi import APIRouter
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

import os
import time
import threading

from app.agent.retry_loop import run_agent
from app.services.repo_cloner import clone_repo
from app.services.code_search import get_python_files
from app.store.task_store import create_task, get_task, get_all_tasks, update_task
from app.worker.agent_worker import run_agent_async
import json

from fastapi.responses import StreamingResponse
import time

# ✅ ADD THIS IMPORT (THIS IS YOUR BUG)
from app.store.task_store import get_logs, get_task
from typing import Optional


router = APIRouter()


# class AgentRequest(BaseModel):
#     code: str
#     issue: str
#     file_name: str = "test.py"

class AgentRequest(BaseModel):
    issue: str
    code: Optional[str] = None
    repo_url: Optional[str] = None


class RepoRequest(BaseModel):
    repo_url: str
    issue: str


@router.get("/")
def root():
    return {"message": "AI SWE Agent Running 🚀"}


@router.post("/run-agent")
def run_ai_agent(request: AgentRequest):
    task_id = create_task()

    thread = threading.Thread(
        target=run_agent_async,
        args=(task_id, request),
        daemon=True
    )
    thread.start()

    return {"task_id": task_id, "status": "started"}



@router.get("/task/{task_id}")
def get_task_full(task_id: str):
    task = get_task(task_id)
    if not task:
        return {"error": "Task not found"}
    
    # This now includes 'diff', 'original_code', and 'fixed_code'
    return task


@router.get("/runs")
def get_runs():
    return {"runs": get_all_tasks()}


@router.get("/metrics")
def get_metrics():
    tasks = get_all_tasks()
    total = len(tasks)
    success = len([t for t in tasks if t["status"] == "success"])
    failed = len([t for t in tasks if t["status"] == "failed"])

    return {
        "total": total,
        "success": success,
        "failed": failed,
        "success_rate": (success / total * 100) if total else 0
    }



@router.get("/logs-stream/{task_id}")
def stream_logs(task_id: str):

    def event_generator():
        last_len = 0

        while True:
            logs = get_logs(task_id)
            task = get_task(task_id)

            # ✅ Send new logs
            if logs and len(logs) > last_len:
                new_logs = logs[last_len:]

                yield f"event: log\ndata: {json.dumps(new_logs, ensure_ascii=False)}\n\n"

                last_len = len(logs)

            # ✅ End condition
            if task and task.get("status") in ["success", "failed"]:
                yield f"event: end\ndata: {json.dumps({'status': task.get('status')})}\n\n"
                break

            time.sleep(0.05)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )