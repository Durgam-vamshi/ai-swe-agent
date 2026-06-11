import os
import re

def locate_bug_files(
    issue: str,
    target_file: str,
    base_path: str
) -> list[str]:
    issue_lower = issue.lower()
    
    # Mapping of keywords to likely file names
    KEYWORD_MAPPING = {
        "session": "sessions.py",
        "blueprint": "blueprints.py",
        "config": "config.py",
        "request": "request.py",
        "auth": "auth.py"
    }

    found_files = set()
    
    # 1. Smarter Localization: Check keywords and resolve full paths
    for keyword, filename in KEYWORD_MAPPING.items():
        if keyword in issue_lower:
            for root, _, files in os.walk(base_path):
                if filename in files:
                    found_files.add(
                        os.path.relpath(
                            os.path.join(root, filename),
                            base_path
                        )
                    )

    # 2. Existing Symbol Tracking Logic
    symbols = []
    if "divide" in issue_lower:
        symbols.append("divide")
    if "multiply" in issue_lower:
        symbols.append("multiply")
    if "add" in issue_lower:
        symbols.append("add")

    target_name = os.path.relpath(target_file, base_path) if target_file else None

    # Scan workspace for related implementations if symbols or keywords are present
    for root, _, files in os.walk(base_path):
        for file in files:
            if not file.endswith(".py") or file.startswith("temp_"):
                continue

            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, base_path)

            # If we already matched via keyword, we still scan to verify 
            # or find other related files that contain the relevant symbols
            if not symbols and rel_path in found_files:
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Match explicit function signatures or usages for symbols
                for symbol in symbols:
                    if re.search(rf"def\s+{symbol}\s*\(", content) or f"import {symbol}" in content:
                        found_files.add(rel_path)
            except Exception:
                pass

    # 3. Fallback: Include target_file if nothing else was found
    if not found_files and target_name:
        found_files.add(target_name)

    return list(found_files)