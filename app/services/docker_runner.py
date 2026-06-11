# import subprocess
# import os
# import re
# from app.utils.logger import log
# import tempfile


# def extract_missing_module(stderr: str):
#     match = re.search(r"No module named '(.+?)'", stderr)
#     if match:
#         return match.group(1)
#     return None


# def run_python_local(base_path: str, file_name: str, args=None, task_id=None):
#     try:
#         file_path = os.path.join(base_path, file_name)

#         if args is None:
#             args = []

#         log(task_id, f"⚙️ Running local file: {file_name}")

#         process = subprocess.run(
#             ["python", file_path, *args],
#             capture_output=True,
#             text=True,
#             timeout=5
#         )

#         stdout = process.stdout.strip() if process.stdout else ""
#         stderr = process.stderr.strip() if process.stderr else ""
#         return_code = process.returncode

#         # ✅ LOGS
#         if stdout:
#             log(task_id, f"💻 STDOUT:\n{stdout}")
#         else:
#             log(task_id, "💻 STDOUT: (empty)")

#         if stderr:
#             log(task_id, f"💻 STDERR:\n{stderr}")
#         else:
#             log(task_id, "💻 STDERR: (empty)")

#         log(task_id, f"💻 RETURN CODE: {return_code}")

#         # ✅ CRITICAL FIX → ALWAYS RETURN return_code
#         return {
#             "success": return_code == 0,
#             "stdout": stdout,
#             "stderr": stderr,
#             "return_code": return_code
#         }

#     except subprocess.TimeoutExpired:
#         log(task_id, "⏱️ Execution timed out")

#         return {
#             "success": False,
#             "stdout": "",
#             "stderr": "Execution timed out",
#             "return_code": 1
#         }

#     except Exception as e:
#         log(task_id, f"💥 Execution error: {str(e)}")

#         return {
#             "success": False,
#             "stdout": "",
#             "stderr": str(e),
#             "return_code": 1
#         }

# def run_python_docker(base_path: str, file_name: str, args=None, task_id=None):
#     try:

#         if args is None:
#             args = []

#         file_path = os.path.abspath(
#             os.path.join(base_path, file_name)
#         )

#         log(task_id, f"🐳 Running in Docker: {file_name}")

#         process = subprocess.run(
#             [
#                 "docker",
#                 "run",
#                 "--rm",
#                 "--memory=256m",
#                 "--cpus=1",
#                 "-v",
#                 f"{os.path.dirname(file_path)}:/app",
#                 "python:3.12-slim",
#                 "python",
#                 f"/app/{file_name}",
#                 *args
#             ],
#             capture_output=True,
#             text=True,
#             timeout=10
#         )

#         stdout = process.stdout.strip()
#         stderr = process.stderr.strip()

#         return {
#             "success": process.returncode == 0,
#             "stdout": stdout,
#             "stderr": stderr,
#             "return_code": process.returncode
#         }

#     except subprocess.TimeoutExpired:
#         return {
#             "success": False,
#             "stdout": "",
#             "stderr": "Execution timed out",
#             "return_code": 1
#         }

#     except Exception as e:
#         return {
#             "success": False,
#             "stdout": "",
#             "stderr": str(e),
#             "return_code": 1
#         }

# def run_repo_tests(base_path: str, task_id=None):
#     """
#     Run repository test suite inside Docker.
#     """

#     try:

#         log(task_id, "🧪 Running repository tests")

#         commands = [
#             ["pytest", "-q"],
#             ["python", "-m", "pytest", "-q"],
#         ]

#         for cmd in commands:

#             try:

#                 process = subprocess.run(
#                     [
#                         "docker",
#                         "run",
#                         "--rm",
#                         "--memory=512m",
#                         "--cpus=1",
#                         "-v",
#                         f"{os.path.abspath(base_path)}:/repo",
#                         "-w",
#                         "/repo",
#                         "python:3.12-slim",
#                         *cmd
#                     ],
#                     capture_output=True,
#                     text=True,
#                     timeout=120
#                 )

#                 stdout = process.stdout.strip()
#                 stderr = process.stderr.strip()

#                 log(
#                     task_id,
#                     f"🧪 TEST RETURN CODE: {process.returncode}"
#                 )

#                 return {
#                     "success": process.returncode == 0,
#                     "stdout": stdout,
#                     "stderr": stderr,
#                     "return_code": process.returncode
#                 }

#             except Exception:
#                 continue

#         return {
#             "success": False,
#             "stdout": "",
#             "stderr": "Unable to execute pytest",
#             "return_code": 1
#         }

#     except Exception as e:

#         return {
#             "success": False,
#             "stdout": "",
#             "stderr": str(e),
#             "return_code": 1
#         }

# def run_python_file(base_path: str, file_name: str, args=None, task_id=None):
#     """
#     🚫 Docker disabled
#     ✅ Local execution with full logging
#     """

#     if args is None:
#         args = []

#     log(task_id, "🐳 Using Docker sandbox execution")

#     result = run_python_docker(base_path, file_name, args, task_id)

#     # ✅ LOG SUCCESS/FAILURE
#     if result.get("return_code") == 0:
#         log(task_id, "✅ Syntax validation passed")
#     else:
#         log(task_id, "❌ Code execution failed")

#     # ✅ CRITICAL FIX → RETURN return_code ALSO
#     return {
#         "used": "docker",
#         "success": result.get("success"),
#         "stdout": result.get("stdout"),
#         "stderr": result.get("stderr"),
#         "return_code": result.get("return_code")
#     }







import subprocess
import os
import re
from app.utils.logger import log
import tempfile


def extract_missing_module(stderr: str):
    match = re.search(r"No module named '(.+?)'", stderr)
    if match:
        return match.group(1)
    return None


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

        stdout = process.stdout.strip() if process.stdout else ""
        stderr = process.stderr.strip() if process.stderr else ""
        return_code = process.returncode

        # ✅ LOGS
        if stdout:
            log(task_id, f"💻 STDOUT:\n{stdout}")
        else:
            log(task_id, "💻 STDOUT: (empty)")

        if stderr:
            log(task_id, f"💻 STDERR:\n{stderr}")
        else:
            log(task_id, "💻 STDERR: (empty)")

        log(task_id, f"💻 RETURN CODE: {return_code}")

        # ✅ CRITICAL FIX → ALWAYS RETURN return_code
        return {
            "success": return_code == 0,
            "stdout": stdout,
            "stderr": stderr,
            "return_code": return_code
        }

    except subprocess.TimeoutExpired:
        log(task_id, "⏱️ Execution timed out")

        return {
            "success": False,
            "stdout": "",
            "stderr": "Execution timed out",
            "return_code": 1
        }

    except Exception as e:
        log(task_id, f"💥 Execution error: {str(e)}")

        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "return_code": 1
        }


def run_python_docker(base_path: str, file_name: str, args=None, task_id=None):
    try:
        if args is None:
            args = []

        file_path = os.path.abspath(
            os.path.join(base_path, file_name)
        )

        log(task_id, f"🐳 Running in Docker: {file_name}")

        process = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--memory=256m",
                "--cpus=1",
                "-v",
                f"{os.path.dirname(file_path)}:/app",
                "python:3.12-slim",
                "python",
                f"/app/{file_name}",
                *args
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        stdout = process.stdout.strip()
        stderr = process.stderr.strip()

        return {
            "success": process.returncode == 0,
            "stdout": stdout,
            "stderr": stderr,
            "return_code": process.returncode
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Execution timed out",
            "return_code": 1
        }

    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "return_code": 1
        }


def run_repo_tests(base_path: str, task_id=None):
    """
    Run repository test suite inside Docker using pytest -q.
    """
    try:
        log(task_id, "🧪 Running repository tests")

        commands = [
            ["pytest", "-q"],
            ["python", "-m", "pytest", "-q"],
        ]

        for cmd in commands:
            try:
                process = subprocess.run(
                    [
                        "docker",
                        "run",
                        "--rm",
                        "--memory=512m",
                        "--cpus=1",
                        "-v",
                        f"{os.path.abspath(base_path)}:/repo",
                        "-w",
                        "/repo",
                        "python:3.12-slim",
                        *cmd
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                stdout = process.stdout.strip()
                stderr = process.stderr.strip()

                log(
                    task_id,
                    f"🧪 TEST RETURN CODE: {process.returncode}"
                )

                return {
                    "success": process.returncode == 0,
                    "stdout": stdout,
                    "stderr": stderr,
                    "return_code": process.returncode
                }

            except Exception:
                continue

        return {
            "success": False,
            "stdout": "",
            "stderr": "Unable to execute pytest",
            "return_code": 1
        }

    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "return_code": 1
        }


def run_python_file(base_path: str, file_name: str, args=None, task_id=None):
    """
    🐳 Sandbox execution orchestration
    """
    if args is None:
        args = []

    log(task_id, "🐳 Using Docker sandbox execution")

    result = run_python_docker(base_path, file_name, args, task_id)

    # ✅ LOG SUCCESS/FAILURE
    if result.get("return_code") == 0:
        log(task_id, "✅ Syntax validation passed")
    else:
        log(task_id, "❌ Code execution failed")

    # ✅ CRITICAL FIX → RETURN return_code ALSO
    return {
        "used": "docker",
        "success": result.get("success"),
        "stdout": result.get("stdout"),
        "stderr": result.get("stderr"),
        "return_code": result.get("return_code")
    }









