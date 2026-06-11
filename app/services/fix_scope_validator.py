import ast
import re

def parse_multi_file(code: str):
    """Parses code block containing # FILE: markers into a dictionary of {filename: content}."""
    files = {}
    # Split by # FILE:
    parts = re.split(r'^# FILE:\s*', code, flags=re.MULTILINE)
    
    # The first part might be empty or preamble if the code doesn't start with # FILE:
    for part in parts:
        if not part.strip():
            continue
        lines = part.splitlines()
        filename = lines[0].strip()
        content = "\n".join(lines[1:])
        files[filename] = content
    return files

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
    original_print_calls = re.findall(r"print\s*\((.*?)\)", original_code, re.DOTALL)
    fixed_print_calls = re.findall(r"print\s*\((.*?)\)", fixed_code, re.DOTALL)

    if original_print_calls != fixed_print_calls:
        return {
            "valid": False,
            "reason": "Modified print statements"
        }

    # Function signature validation via AST parsing
    try:
        # Parse multi-file structures
        original_files = parse_multi_file(original_code)
        fixed_files = parse_multi_file(fixed_code)

        # Ensure we have at least one file to compare, fallback to treating as single file if no markers
        if not original_files: original_files = {"default": original_code}
        if not fixed_files: fixed_files = {"default": fixed_code}

        for filename, f_code in fixed_files.items():
            if filename not in original_files:
                continue # Allow new files
            
            orig_tree = ast.parse(original_files[filename])
            fixed_tree = ast.parse(f_code)

            original_functions = {
                node.name: len(node.args.args)
                for node in ast.walk(orig_tree)
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
                        "reason": f"Function removed in {filename}: {func_name}"
                    }

                if fixed_functions[func_name] != arg_count:
                    return {
                        "valid": False,
                        "reason": f"Function signature changed in {filename}: {func_name}"
                    }

    except Exception as e:
        return {
            "valid": False,
            "reason": f"AST Validation Error: {str(e)}"
        }

    return {
        "valid": True
    }