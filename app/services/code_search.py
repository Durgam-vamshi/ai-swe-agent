

# import os


# print("=" * 50)
# print("CODE_SEARCH.PY CALLED")
# print("repo_path =", repo_path)
# print("=" * 50)




# def get_python_files(repo_path):
#     py_files = []
    
#     # Use a set for O(1) lookup speed
#     exclude_dirs = {"docs", "test", "tests", "examples", "site-packages", "__pycache__", ".git", ".venv"}

#     # Convert repo_path to absolute to avoid relative path issues
#     repo_path = os.path.abspath(repo_path)

#     for root, dirs, files in os.walk(repo_path):
#         # MODIFICATION: Prune directories in-place. 
#         # This prevents os.walk from entering these folders entirely.
#         dirs[:] = [d for d in dirs if d.lower() not in exclude_dirs]

#         for file in files:
#             if file.endswith(".py"):
#                 full_path = os.path.join(root, file)
                
#                 # Double-check: ensure we aren't in a hidden folder (like .github)
#                 if any(part.startswith('.') for part in full_path.split(os.sep)):
#                     continue
                
#                 # Get path relative to the repo root
#                 relative_path = os.path.relpath(full_path, repo_path)
#                 py_files.append(relative_path)
#                 print("FOUND PYTHON FILES:", len(py_files))
#                 print(py_files[:20])
#                 print("FINAL PY FILE COUNT =", len(py_files))

#     return py_files










import os

def get_python_files(repo_path):
    """
    Scans a directory for .py files, excluding standard noise directories.
    """
    py_files = []
    
    # Use a set for O(1) lookup speed
    exclude_dirs = {"docs", "test", "tests", "examples", "site-packages", "__pycache__", ".git", ".venv"}

    # Convert repo_path to absolute to avoid relative path issues
    abs_repo_path = os.path.abspath(repo_path)

    for root, dirs, files in os.walk(abs_repo_path):
        # Prune directories in-place to prevent os.walk from entering them
        dirs[:] = [d for d in dirs if d.lower() not in exclude_dirs]

        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                
                # Ensure we aren't in a hidden folder
                if any(part.startswith('.') for part in full_path.split(os.sep)):
                    continue
                
                # Get path relative to the repo root
                relative_path = os.path.relpath(full_path, abs_repo_path)
                py_files.append(relative_path)

    # Optional: Debugging output moved inside the function scope
    print(f"DEBUG: Found {len(py_files)} python files in {repo_path}")
    return py_files












