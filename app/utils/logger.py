# app/utils/logger.py

def log(task_id, message):
    from app.store.task_store import add_log
    if task_id:
        add_log(task_id, message)
    else:
        print(message)  # fallback