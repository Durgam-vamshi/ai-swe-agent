import ast
import re


def extract_structure(code: str):
    tree = ast.parse(code)

    classes = set()
    functions = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.add(node.name)
        elif isinstance(node, ast.FunctionDef):
            functions.add(node.name)

    return {
        "classes": classes,
        "functions": functions,
        "function_count": len(functions),
    }


def validate_no_regression(original: str, fixed: str):
    try:
        # Step 1: Parse the fixed code first to make sure it's valid
        try:
            new = extract_structure(fixed)
        except Exception as e:
            return {
                "valid": False,
                "error": f"Generated fixed code has syntax errors: {str(e)}",
            }

        # Step 2: Parse the original code safely
        try:
            old = extract_structure(original)
        except Exception:
            # If the original code was broken/unparseable (e.g., missing ':'),
            # we fallback to a regex match to find structural functions or assume empty baseline
            old_functions = set(re.findall(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", original))
            old_classes = set(re.findall(r"class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[:\(]", original))
            
            old = {
                "classes": old_classes,
                "functions": old_functions,
                "function_count": len(old_functions)
            }

        # Change #1: Detect massive file truncation
        old_lines = len(original.splitlines())
        new_lines = len(fixed.splitlines())

        if old_lines > 50 and new_lines < old_lines * 0.7:
            return {
                "valid": False,
                "error": f"Suspicious file truncation detected. Original={old_lines}, New={new_lines}"
            }

        # Change #2: Track Function Count
        if new["function_count"] < old["function_count"]:
            return {
                "valid": False,
                "error": "Function deletion detected"
            }

        removed_classes = old["classes"] - new["classes"]
        removed_functions = old["functions"] - new["functions"]

        return {
            "valid": not (removed_classes or removed_functions),
            "removed_classes": list(removed_classes),
            "removed_functions": list(removed_functions),
        }

    except Exception as e:
        return {
            "valid": False,
            "error": f"AST validation crash: {str(e)}",
        }