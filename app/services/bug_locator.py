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











































