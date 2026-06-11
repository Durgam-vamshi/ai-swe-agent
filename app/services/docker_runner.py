import subprocess
import os
import re
from app.utils.logger import log

# =========================
# 🔍 EXTRACT MISSING MODULE
# =========================
def extract_missing_module(stderr: str):
    match = re.search(r"No module named '(.+?)'", stderr)
    if match:
        return match.group(1)
    return None

# =========================
# 💻 LOCAL EXECUTION
# =========================
def run_python_local(base_path: str, file_name: str, args=None, task_id=None):
    try:
        file_path = os.path.join(base_path, file_name)
        if args is None:
            args = []

        log(task_id, f"⚙️ Running local file: {file_name}")

        process = subprocess.run(
            ["python", file_path, *args],
            capture_output=True,
            text=True,
            timeout=5
        )

        return {
            "success": process.returncode == 0,
            "stdout": process.stdout.strip() if process.stdout else "",
            "stderr": process.stderr.strip() if process.stderr else "",
            "return_code": process.returncode
        }
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "return_code": 1}

# =========================
# 🐳 DOCKER EXECUTION (FIXED)
# =========================
def run_python_docker(base_path: str, file_name: str, args=None, task_id=None, is_repository=False):
    if args is None:
        args = []

    file_path = os.path.abspath(os.path.join(base_path, file_name))

    if is_repository:
        log(task_id, "📦 Repository mode validation")
        # Validate syntax and imports using py_compile
        process = subprocess.run(
            [
                "docker", "run", "--rm", "--memory=256m", "--cpus=1",
                "-v", f"{base_path}:/app",
                "python:3.12-slim",
                "python", "-m", "py_compile", f"/app/{file_name}"
            ],
            capture_output=True,
            text=True,
            timeout=10
        )
    else:
        log(task_id, "🧪 Snippet mode execution")
        # Standard execution for standalone snippets
        process = subprocess.run(
            [
                "docker", "run", "--rm", "--memory=256m", "--cpus=1",
                "-v", f"{os.path.dirname(file_path)}:/app",
                "python:3.12-slim",
                "python", f"/app/{file_name}",
                *args
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

    return {
        "success": process.returncode == 0,
        "stdout": process.stdout.strip(),
        "stderr": process.stderr.strip(),
        "return_code": process.returncode
    }

# =========================
# 🔁 MAIN EXECUTION FLOW
# =========================
def run_python_file(base_path: str, file_name: str, args=None, task_id=None, is_repository=False):
    """
    Executes Python files via Docker.
    Uses 'py_compile' for repository modules to prevent ImportErrors.
    """
    log(task_id, f"🐳 Using Docker sandbox for: {file_name}")

    result = run_python_docker(base_path, file_name, args, task_id, is_repository)

    if result.get("return_code") == 0:
        log(task_id, "✅ Validation passed")
    else:
        log(task_id, "❌ Validation failed")

    return {
        "used": "docker",
        "success": result.get("success"),
        "stdout": result.get("stdout"),
        "stderr": result.get("stderr"),
        "return_code": result.get("return_code")
    }