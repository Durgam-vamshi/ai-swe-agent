import ast
import re

def validate_fix_scope(original_code, fixed_code):
    # 🚨 GUARD: Safely allow full initialization if the original codebase is empty or just whitespace
    if not original_code or not str(original_code).strip():
        return {
            "valid": True,
            "reason": "Initial codebase is empty; allowing complete initialization structure."
        }

    # Existing print check
    original_prints = original_code.count("print(")
    fixed_prints = fixed_code.count("print(")

    if fixed_prints > original_prints:
        return {
            "valid": False,
            "reason": "Added new print statements"
        }

    # Validate exact print statement content strings
    original_print_calls = re.findall(
        r"print\s*\((.*?)\)",
        original_code,
        re.DOTALL
    )

    fixed_print_calls = re.findall(
        r"print\s*\((.*?)\)",
        fixed_code,
        re.DOTALL
    )

    if original_print_calls != fixed_print_calls:
        return {
            "valid": False,
            "reason": "Modified print statements"
        }

    # Function signature validation via AST parsing
    try:
        original_tree = ast.parse(original_code)
        fixed_tree = ast.parse(fixed_code)

        original_functions = {
            node.name: len(node.args.args)
            for node in ast.walk(original_tree)
            if isinstance(node, ast.FunctionDef)
        }

        fixed_functions = {
            node.name: len(node.args.args)
            for node in ast.walk(fixed_tree)
            if isinstance(node, ast.FunctionDef)
        }

        for func_name, arg_count in original_functions.items():

            if func_name not in fixed_functions:
                return {
                    "valid": False,
                    "reason": f"Function removed: {func_name}"
                }

            if fixed_functions[func_name] != arg_count:
                return {
                    "valid": False,
                    "reason": f"Function signature changed: {func_name}"
                }

    except Exception as e:
        return {
            "valid": False,
            "reason": str(e)
        }

    return {
        "valid": True
    }