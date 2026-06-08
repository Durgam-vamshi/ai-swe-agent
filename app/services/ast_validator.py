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
            old = {"classes": set(), "functions": set()}
            # Simple regex search to catch function definitions from broken original code
            for func_name in re.findall(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", original):
                old["functions"].add(func_name)
            for class_name in re.findall(r"class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[:\(]", original):
                old["classes"].add(class_name)

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