import os
import sys
import subprocess


def run_pytest(test_file, repo_path=None):

    if not repo_path:
        repo_path = os.getcwd()

    env = os.environ.copy()

    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = (
            f"{repo_path}{os.pathsep}{env['PYTHONPATH']}"
        )
    else:
        env["PYTHONPATH"] = repo_path

    print("=" * 50)
    print("DEBUG PYTHONPATH =", env["PYTHONPATH"])
    print("DEBUG CWD =", repo_path)
    print("DEBUG TEST FILE =", test_file)
    print("=" * 50)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            test_file,
            "-q"
        ],
        cwd=repo_path,
        env=env,
        capture_output=True,
        text=True
    )

    return {
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "return_code": result.returncode
    }