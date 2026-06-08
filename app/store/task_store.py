

tasks = {}


# =========================
# 🆕 CREATE TASK
# =========================
def create_task():
    import uuid

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

    return task_id


# =========================
# 🔄 UPDATE TASK (FIXED)
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


# =========================
# 🔼 INCREMENT ATTEMPT
# =========================
def increment_attempt(task_id):
    if task_id in tasks:
        tasks[task_id]["attempt"] += 1


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















