# import os
# import re
# from app.services.code_search import get_python_files

# def locate_bug_files(
#     issue: str,
#     target_file: str,
#     base_path: str
# ) -> list[str]:
#     print("🔥 NEW BUG_LOCATOR VERSION LOADED")
#     print(f"DEBUG ISSUE = {issue}")
    
#     issue_lower = issue.lower()
#     symbols = []

#     if "divide" in issue_lower:
#         symbols.append("divide")
#     if "multiply" in issue_lower:
#         symbols.append("multiply")
#     if "add" in issue_lower:
#         symbols.append("add")

#     print(f"DEBUG SYMBOLS = {symbols}")

#     # Initialize target_name safely using relative path
#     target_name = (
#         os.path.relpath(target_file, base_path)
#         if target_file
#         else ""
#     )

#     # If no explicitly tracked symbols are found, default to scanning files
#     if not symbols:
#         files = get_python_files(base_path)[:5]
#         print(f"🔥 RETURNING FILES = {files}")
#         return files

#     found_files = set()
    
#     # Always include the primary target file if it contains any of the symbols
#     if target_file and os.path.exists(target_file):
#         try:
#             with open(target_file, "r", encoding="utf-8") as f:
#                 target_content = f.read()
#             for symbol in symbols:
#                 if symbol in target_content:
#                     found_files.add(target_name)
#                     break
#         except Exception:
#             pass

#     # Scan the rest of the workspace directory for related implementations
#     for root, _, files in os.walk(base_path):
#         for file in files:
#             if not file.endswith(".py") or file.startswith("temp_"):
#                 continue

#             file_path = os.path.join(root, file)

#             try:
#                 with open(file_path, "r", encoding="utf-8") as f:
#                     content = f.read()

#                 for symbol in symbols:
#                     # Match explicit function signatures or usages
#                     if re.search(rf"def\s+{symbol}\s*\(", content) or f"import {symbol}" in content:
#                         found_files.add(
#                             os.path.relpath(
#                                 file_path,
#                                 base_path
#                             )
#                         )

#             except Exception:
#                 pass

#     # Ensure we return a clean list of files. Fall back to target if everything else is empty.
#     if not found_files and target_name:
#         found_files.add(target_name)

#     return list(found_files)






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
    
    # Extract keywords (words with 4+ characters)
    keywords = re.findall(r"[a-zA-Z_]{4,}", issue_lower)
    
    scores = []
    python_files = get_python_files(base_path)

    for file in python_files:
        path = os.path.join(base_path, file)
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read(5000).lower()
            
            score = 0
            
            # Content scoring
            for word in keywords:
                score += content.count(word)
            
            # Path scoring
            filename_lower = file.lower()
            for word in keywords:
                if word in filename_lower:
                    score += 50
            
            if score > 0:
                scores.append((score, file))
                
        except Exception:
            continue

    scores.sort(key=lambda x: x[0], reverse=True)
    
    # Take top 2 files
    files = [f for _, f in scores[:2]]
    
    # Calculate mock metrics for debugging (assuming helper functions exist)
    # In a real environment, you'd calculate actual lengths
    code_length_mock = sum(len(f) for f in files)
    final_prompt_len_mock = len(issue) + code_length_mock
    
    print(f"🔥 RANKED FILES = {files}")
    print(f"DEBUG current_code_length = {code_length_mock}")
    print(f"DEBUG FINAL PROMPT LEN = {final_prompt_len_mock}")
    
    if files:
        return files

    # Fallback
    fallback = get_python_files(base_path)[:1]
    return fallback











































