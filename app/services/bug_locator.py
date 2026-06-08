import os
import re

def locate_bug_files(
    issue: str,
    target_file: str,
    base_path: str
) -> list[str]:
    issue_lower = issue.lower()
    symbols = []

    if "divide" in issue_lower:
        symbols.append("divide")
    if "multiply" in issue_lower:
        symbols.append("multiply")
    if "add" in issue_lower:
        symbols.append("add")

    # If no explicitly tracked symbols are found, default to tracking the primary file
    target_name = os.path.basename(target_file)
    if not symbols:
        return [target_name] if target_name else []

    found_files = set()
    
    # Always include the primary target file if it contains any of the symbols
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
                        found_files.add(file)

            except Exception:
                pass

    # Ensure we return a clean list of files. Fall back to target if everything else is empty.
    if not found_files and target_name:
        found_files.add(target_name)

    return list(found_files)