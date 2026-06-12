import subprocess
import os
import re
from app.utils.logger import log

def extract_missing_module(stderr: str):
    match = re.search(r"No module named '(.+?)'", stderr)
    if match:
        return match.group(1)
    return None

def run_python_local(base_path: str, file_name: str, args=None, task_id=None):
    try:
        file_path = os.path.join(base_path, file_name)
        args = args or []
        log(task_id, f"⚙️ Running local file: {file_name}")

        process = subprocess.run(
            ["python", file_path, *args],
            capture_output=True,
            text=True,
            timeout=5
        )

        stdout = process.stdout.strip() if process.stdout else "(empty)"
        stderr = process.stderr.strip() if process.stderr else "(empty)"
        
        log(task_id, f"💻 STDOUT: {stdout}")
        log(task_id, f"💻 STDERR: {stderr}")
        log(task_id, f"💻 RETURN CODE: {process.returncode}")

        return {
            "success": process.returncode == 0,
            "stdout": stdout,
            "stderr": stderr,
            "return_code": process.returncode
        }
    except Exception as e:
        log(task_id, f"💥 Execution error: {str(e)}")
        return {"success": False, "stdout": "", "stderr": str(e), "return_code": 1}

def run_python_docker(base_path: str, file_name: str, args=None, task_id=None):
    try:
        args = args or []
        file_path = os.path.abspath(os.path.join(base_path, file_name))
        log(task_id, f"🐳 Running in Docker: {file_name}")

        process = subprocess.run(
            [
                "docker", "run", "--rm", "--memory=256m", "--cpus=1",
                "-v", f"{os.path.dirname(file_path)}:/app",
                "python:3.12-slim", "python", f"/app/{file_name}", *args
            ],
            capture_output=True, text=True, timeout=10
        )

        return {
            "success": process.returncode == 0,
            "stdout": process.stdout.strip(),
            "stderr": process.stderr.strip(),
            "return_code": process.returncode
        }
    except Exception as e:
        log(task_id, f"💥 Docker execution error: {str(e)}")
        return {"success": False, "stdout": "", "stderr": str(e), "return_code": 1}

def run_repo_tests(base_path: str, task_id=None):
    """Run repository test suite inside Docker with detailed diagnostics."""
    log(task_id, "🧪 Running repository tests")
    cmd = ["python", "-m", "pytest", "-q"]

    try:
        process = subprocess.run(
            [
                "docker", "run", "--rm", "--memory=512m", "--cpus=1",
                "-v", f"{os.path.abspath(base_path)}:/repo",
                "-w", "/repo", "python:3.12-slim", *cmd
            ],
            capture_output=True, text=True, timeout=120
        )

        stdout = process.stdout.strip()
        stderr = process.stderr.strip()

        # Log detailed diagnostics
        log(task_id, f"TEST RETURN CODE={process.returncode}")
        
        if stdout:
            log(task_id, f"TEST STDOUT:\n{stdout[:1500]}")
        if stderr:
            log(task_id, f"TEST STDERR:\n{stderr[:1500]}")

        if process.returncode != 0:
            log(task_id, "❌ Repository tests failed")

        return {
            "success": process.returncode == 0,
            "stdout": stdout,
            "stderr": stderr,
            "return_code": process.returncode
        }
    except Exception as e:
        log(task_id, f"💥 Test suite exception: {str(e)}")
        return {"success": False, "stdout": "", "stderr": str(e), "return_code": 1}

def run_python_file(base_path: str, file_name: str, args=None, task_id=None):
    """🐳 Sandbox execution orchestration"""
    log(task_id, "🐳 Using Docker sandbox execution")
    result = run_python_docker(base_path, file_name, args or [], task_id)

    if result["return_code"] == 0:
        log(task_id, "✅ Execution passed")
    else:
        log(task_id, "❌ Code execution failed")

    return {
        "used": "docker",
        **result
    }