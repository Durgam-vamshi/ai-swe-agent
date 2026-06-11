import os
from app.services.llm_client import call_llm


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


def read_file_content(repo_path, file_path, max_chars=1000):
    try:
        full_path = os.path.join(repo_path, file_path)
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()[:max_chars]
    except:
        return ""


def build_multi_file_prompt(issue, file_data):
    formatted = ""

    for file_name, content in file_data:
        formatted += f"\nFILE: {file_name}\nCONTENT:\n{content}\n"

    return f"""
You are an expert software engineer.

Your task is to identify ALL files that need to be fixed.

ISSUE:
{issue}

FILES:
{formatted}

RULES:
- Return ONLY file names separated by commas
- Example: main.py, config.py
- Do NOT explain
- Choose all relevant files
"""


def clean_files(response, files):
    response = response.strip()
    response = response.replace('"', '').replace("'", "").replace("`", "")

    selected = [f.strip() for f in response.split(",")]

    cleaned = []

    for sel in selected:
        sel = os.path.basename(sel)

        for f in files:
            if sel == f or sel in f:
                cleaned.append(f)

    return list(set(cleaned))


def select_files(repo_path, issue):
    files = get_python_files(repo_path)

    if not files:
        raise Exception("No Python files found")

    print("📂 Files available:", files)

    file_data = []
    for f in files:
        content = read_file_content(repo_path, f)
        file_data.append((f, content))

    prompt = build_multi_file_prompt(issue, file_data)


    response = call_llm(prompt, model="phi3:mini")

    print("🧠 RAW MULTI-FILE RESPONSE:", response)

    selected_files = clean_files(response, files)

    if not selected_files:
        print("⚠️ No valid files selected, fallback to first file")
        return [files[0]]

    print(f"🧠 AI Selected Files: {selected_files}")

    return selected_files