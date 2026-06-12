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

    # Ignore noisy words
    STOP_WORDS = {
        "where",
        "does",
        "from",
        "with",
        "that",
        "this",
        "have",
        "will",
        "would",
        "correctly",
        "should",
        "could",
        "into",
        "when"
    }

    # Extract useful keywords only
    keywords = [
        word
        for word in re.findall(
            r"[a-zA-Z_]{4,}",
            issue_lower
        )
        if word not in STOP_WORDS
    ]

    scores = []

    python_files = get_python_files(base_path)

    for file in python_files:

        path = os.path.join(
            base_path,
            file
        )

        try:

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as f:

                content = f.read(5000).lower()

            score = 0

            # Content scoring
            for word in keywords:
                score += content.count(word)

            # Filename scoring (higher priority)
            filename_lower = file.lower()

            for word in keywords:
                if word in filename_lower:
                    score += 50

            # Only keep relevant files
            if score > 0:
                scores.append(
                    (score, file)
                )

        except Exception:
            continue

    # Highest score first
    scores.sort(
        key=lambda x: x[0],
        reverse=True
    )

    # IMPORTANT FIX:
    # Return ONLY top 1 file
    files = [
        f
        for _, f in scores[:1]
    ]

    print(f"🔥 RANKED FILES = {files}")

    if files:
        return files

    # Safe fallback
    fallback = get_python_files(base_path)[:1]

    print(
        f"⚠️ FALLBACK FILES = {fallback}"
    )

    return fallback