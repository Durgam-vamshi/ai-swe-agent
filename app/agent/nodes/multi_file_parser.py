import re


def parse_multi_file(code: str) -> dict:
    """
    Parses LLM output like:

    # FILE: auth.py
    code...

    # FILE: routes.py
    code...

    Returns:
    {
        "auth.py": "...",
        "routes.py": "..."
    }
    """

    if not code:
        return {}

    pattern = r"# FILE:\s*(.+?)\n"

    matches = list(re.finditer(pattern, code))

    if not matches:
        return {"single_file": code.strip()}

    files = {}

    for i, match in enumerate(matches):
        filename = match.group(1).strip()

        start = match.end()

        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(code)

        file_code = code[start:end].strip()

        files[filename] = file_code

    return files