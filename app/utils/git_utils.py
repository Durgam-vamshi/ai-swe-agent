import os
import subprocess
import uuid

def clone_repo(repo_url: str) -> str:
    """
    Clones a repository into a temporary directory within the workspace.
    Returns the path to the cloned repository.
    """
    # Define a base path for cloned repos
    base_clone_dir = r"C:\Users\user\Desktop\githubaiagent\workspace\clones"
    os.makedirs(base_clone_dir, exist_ok=True)
    
    # Generate a unique folder name to avoid conflicts
    repo_name = repo_url.split("/")[-1].replace(".git", "")
    clone_path = os.path.join(base_clone_dir, f"{repo_name}_{uuid.uuid4().hex[:8]}")
    
    try:
        # Run git clone command
        subprocess.check_call(["git", "clone", repo_url, clone_path])
        return clone_path
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to clone repository: {str(e)}")