import os
import re
from app.services.code_search import get_python_files

def locate_bug_files(
    issue: str,
    target_file: str,
    base_path: str
) -> list[str]:
    print("🔥 NEW BUG_LOCATOR VERSION LOADED")
    print(f"DEBUG ISSUE = {issue}")
    
    issue_lower = issue.lower()
    symbols = []

    if "divide" in issue_lower:
        symbols.append("divide")
    if "multiply" in issue_lower:
        symbols.append("multiply")
    if "add" in issue_lower:
        symbols.append("add")

    print(f"DEBUG SYMBOLS = {symbols}")

    # Initialize target_name safely using relative path
    target_name = (
        os.path.relpath(target_file, base_path)
        if target_file
        else ""
    )

    # If no explicitly tracked symbols are found, default to scanning files
    if not symbols:
        files = get_python_files(base_path)[:5]
        print(f"🔥 RETURNING FILES = {files}")
        return files

    found_files = set()
    
    # Always include the primary target file if it contains any of the symbols
    if target_file and os.path.exists(target_file):
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                target_content = f.read()
            for symbol in symbols:
                if symbol in target_content:
                    found_files.add(target_name)
                    break
        except Exception:
            pass

    # Scan the rest of the workspace directory for related implementations
    for root, _, files in os.walk(base_path):
        for file in files:
            if not file.endswith(".py") or file.startswith("temp_"):
                continue

            file_path = os.path.join(root, file)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                for symbol in symbols:
                    # Match explicit function signatures or usages
                    if re.search(rf"def\s+{symbol}\s*\(", content) or f"import {symbol}" in content:
                        found_files.add(
                            os.path.relpath(
                                file_path,
                                base_path
                            )
                        )

            except Exception:
                pass

    # Ensure we return a clean list of files. Fall back to target if everything else is empty.
    if not found_files and target_name:
        found_files.add(target_name)

    return list(found_files)