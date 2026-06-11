import os
from app.services.llm_client import call_llm


# ==============================
# 🔥 GET PYTHON FILES
# ==============================
def get_python_files(repo_path):
    py_files = []

    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".py"):

                if any(
                    x in root.lower()
                    for x in ["docs", "example", "__pycache__", "site-packages"]
                ):
                    continue

                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo_path)
                py_files.append(rel_path)

    return py_files


def read_file_content(repo_path, file_path, max_chars=1500):
    try:
        full_path = os.path.join(repo_path, file_path)

        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 🔥 Limit content (important for LLM)
        return content[:max_chars]

    except Exception:
        return ""


# ==============================
# 🔥 BUILD SMART PROMPT
# ==============================
def build_smart_prompt(issue: str, file_data: list):
    formatted = ""

    for file_name, content in file_data:
        formatted += f"\nFILE: {file_name}\nCONTENT:\n{content}\n"

    return f"""
You are an expert software engineer.

Your task is to identify which file is MOST relevant to fix.

ISSUE:
{issue}

FILES:
{formatted}

RULES:
- Return ONLY the file name (example: main.py)
- Do NOT explain
- Choose the file where the bug most likely exists
"""


# ==============================
# 🔥 CLEAN RESPONSE
# ==============================
def clean_selected_file(response: str, files: list) -> str:
    selected = response.strip()

    selected = selected.replace('"', '').replace("'", "").replace("`", "")

    # Extract filename if full path
    selected = os.path.basename(selected)

    # Match with known files
    for f in files:
        if selected == f or selected in f:
            return f

    return selected


# ==============================
# 🔥 MAIN SELECT FUNCTION
# ==============================
def select_file(repo_path: str, issue: str):
    files = get_python_files(repo_path)

    if not files:
        raise Exception("No Python files found")

    print("📂 Files available:", files)

    # 🔥 Read content of each file
    file_data = []
    for f in files:
        content = read_file_content(repo_path, f)
        file_data.append((f, content))

    # 🔥 Build smart prompt
    prompt = build_smart_prompt(issue, file_data)
    
    # 🔥 Call LLM
    response = call_llm(prompt, model="phi3:mini")

    print("🧠 RAW FILE SELECTION RESPONSE:", response)

    selected_file = clean_selected_file(response, files)

    # 🔥 Safety fallback
    if selected_file not in files:
        print("⚠️ Invalid file selected, fallback to first file")
        return files[0]

    print(f"🧠 AI Selected File (SMART): {selected_file}")

    return selected_file
























