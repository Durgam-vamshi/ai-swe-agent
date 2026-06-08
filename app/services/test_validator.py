import os
import ast
import tempfile

from app.utils.logger import log
from app.services.test_generator import generate_tests
from app.services.test_runner import run_pytest


def is_valid_test_code(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except Exception:
        return False


def validate_with_tests(
    code: str,
    issue: str,
    file_name: str,
    repo_path: str,
    task_id: str = None,
    temp_module_name: str = None
) -> dict:

    tests = generate_tests(code, issue, file_name)

    if "import pytest" not in tests:
        tests = "import pytest\n\n" + tests

    module_name = (
        temp_module_name
        if temp_module_name
        else file_name.replace(".py", "").replace("\\", "/").split("/")[-1]
    )

    target_import_statement = f"from {module_name} import *"

    lines = tests.splitlines()

    cleaned_lines = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("from ") and " import " in stripped:
            continue

        cleaned_lines.append(line)

    tests = "\n".join(cleaned_lines)

    tests = f"{target_import_statement}\n\n{tests}"

    log(task_id, f"MODULE NAME = {module_name}")
    log(task_id, f"REPO PATH = {repo_path}")
    log(task_id, f"TARGET FILE = {file_name}")
    log(task_id, f"TEMP MODULE = {temp_module_name}")
    log(task_id, f"GENERATED TESTS WITH INJECTED IMPORTS:\n{tests}")

    if not is_valid_test_code(tests):
        return {
            "success": False,
            "stdout": "",
            "stderr": "Generated invalid test syntax after running validation rules",
            "return_code": 1,
        }

    test_file_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix="_test.py",
            delete=False
        ) as f:
            f.write(tests)
            test_file_path = f.name

        log(task_id, f"TEMP TEST FILE = {test_file_path}")

        result = run_pytest(
            test_file=test_file_path,
            repo_path=repo_path
        )

        return result

    finally:
        if test_file_path and os.path.exists(test_file_path):
            try:
                os.unlink(test_file_path)
            except Exception:
                pass