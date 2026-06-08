import os
# Import the central filtering logic from your analyzer file
from app.services.repository_analyzer import discover_python_files

def find_usages(symbol: str, base_path: str):
    usages = []

    # Reuses discover_python_files for absolute consistency across scripts
    files = discover_python_files(base_path)

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line_no, line in enumerate(lines, start=1):
                if symbol in line:
                    usages.append(
                        {
                            # Extracts just the filename out of the full path for output consistency
                            "file": os.path.basename(file_path),
                            "line": line_no,
                            "code": line.strip()
                        }
                    )

        except Exception:
            pass

    return usages