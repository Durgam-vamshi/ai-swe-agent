

import os
import shutil
import subprocess
import stat

def remove_readonly(func, path, _):
    """
    Clear the readonly bit and reattempt the removal.
    Necessary for Windows to delete .git/objects.
    """
    os.chmod(path, stat.S_IWRITE)
    func(path)

def clone_repo(repo_url: str, base_dir="repos"):
    """
    Clones a repository with a forced cleanup of existing directories.
    Uses a shallow clone for speed.
    """
    os.makedirs(base_dir, exist_ok=True)

    # Extract repository name and strip .git if present
    repo_name = repo_url.split("/")[-1].replace(".git", "")
    repo_path = os.path.join(base_dir, repo_name)

    # 🔥 FORCE DELETE (Windows-safe using onerror handler)
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path, onerror=remove_readonly)

    # 🔥 DOUBLE CHECK DELETE
    if os.path.exists(repo_path):
        raise Exception(
            f"Failed to delete existing repo at {repo_path}. "
            "Please close VS Code or any other process using this folder."
        )

    # 🔥 Clone fresh using high-efficiency flags
    result = subprocess.run(
        [
            "git", "clone",
            "--depth", "1",
            "--single-branch",
            repo_url,
            repo_path
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise Exception(f"Git clone failed: {result.stderr}")

    return repo_path
