import subprocess
import re

def install_missing_package(stderr: str):
    match = re.search(r"No module named '(.+?)'", stderr)
    
    if not match:
        return "No package found"

    package = match.group(1)

    try:
        subprocess.run(["uv", "pip", "install", package])
        return f"Installed {package}"
    except Exception as e:
        return str(e)