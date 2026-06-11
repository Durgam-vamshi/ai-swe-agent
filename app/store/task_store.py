





import json
import os
import uuid

# Set path relative to this file
TASK_FILE = os.path.join(
    os.path.dirname(__file__),
    "task_store.json"
)

tasks = {}

# =========================
# 💾 PERSISTENCE (FIXED)
# =========================
def save_tasks():
    with open(
        TASK_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            tasks,
            f,
            indent=2
        )


def load_tasks():
    global tasks

    if not os.path.exists(TASK_FILE):
        tasks = {}
        return

    try:
        with open(TASK_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()

            if not content:
                tasks = {}
                return

            tasks = json.loads(content)

    except Exception:
        tasks = {}


# =========================
# 🆕 CREATE TASK
# =========================
def create_task():
    task_id = str(uuid.uuid4())

    tasks[task_id] = {
        "id": task_id,  # 🔥 important for frontend
        "status": "running",
        "logs": [],
        "attempt": 0,
        "issue": "",
        "result": {
            "final_status": None,
            "fixed_code": "",
            "explanation": "",
            "attempts": 0,
            "logs": []
        }
    }
    
    save_tasks()
    return task_id


# =========================
# 🔄 UPDATE TASK
# =========================
def update_task(task_id, data=None, **kwargs):
    if task_id not in tasks:
        return

    # 🔥 Case 1: dictionary passed
    if isinstance(data, dict):
        tasks[task_id].update(data)

    # 🔥 Case 2: keyword args passed
    if kwargs:
        tasks[task_id].update(kwargs)
        
    save_tasks()


# =========================
# 🔼 INCREMENT ATTEMPT
# =========================
def increment_attempt(task_id):
    if task_id in tasks:
        tasks[task_id]["attempt"] += 1
        save_tasks()


# =========================
# 📦 GET TASK
# =========================
def get_task(task_id):
    return tasks.get(task_id)


# =========================
# 📜 LOGGING
# =========================
def add_log(task_id, message):
    if task_id in tasks:
        tasks[task_id]["logs"].append(str(message))
        save_tasks()


def get_logs(task_id):
    task = tasks.get(task_id)
    if not task:
        return []
    return task.get("logs", [])


# =========================
# 📊 DASHBOARD SUPPORT
# =========================
def get_all_tasks():
    return list(tasks.values())


# =========================
# 🚀 INITIALIZATION
# =========================
# Load existing data safely on startup
load_tasks()



















