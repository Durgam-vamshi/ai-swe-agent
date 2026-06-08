import json
import os
from datetime import datetime


LOG_FILE = "evaluation_logs.json"


def evaluate_run(result: dict):
    entry = {
        "timestamp": str(datetime.now()),
        "status": result.get("final_status"),
        "file": result.get("file"),
        "attempts": result.get("attempts"),
        "success": result.get("final_status") == "success",
        "stdout": "",
        "stderr": "",
    }

    logs = result.get("logs", [])

    if logs:
        last = logs[-1]
        entry["stdout"] = last.get("stdout", "")
        entry["stderr"] = last.get("stderr", "")

    save_log(entry)


def save_log(entry):
    data = []

    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                data = json.load(f)
        except:
            data = []

    data.append(entry)

    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_metrics():
    if not os.path.exists(LOG_FILE):
        return {
            "total_runs": 0,
            "success_rate": 0,
            "avg_attempts": 0
        }

    with open(LOG_FILE, "r") as f:
        data = json.load(f)

    total = len(data)
    success = sum(1 for d in data if d["success"])
    attempts = sum(d.get("attempts", 0) for d in data)

    return {
        "total_runs": total,
        "success_rate": round((success / total) * 100, 2) if total else 0,
        "avg_attempts": round(attempts / total, 2) if total else 0
    }