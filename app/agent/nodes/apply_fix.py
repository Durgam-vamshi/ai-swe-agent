import os

def apply_fix(base_path: str, target_file: str, fixed_code: str):
    try:
        file_path = os.path.join(base_path, target_file)

        # ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # write file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(fixed_code)

        return {
            "status": "success",
            "file_path": file_path
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }







