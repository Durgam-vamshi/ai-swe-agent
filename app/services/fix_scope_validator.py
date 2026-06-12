import ast
import re


def parse_multi_file(code: str):
    """
    Parses code blocks containing:
    # FILE: path/to/file.py
    markers into:
    {
        filename: content
    }
    """
    files = {}
    parts = re.split(r"^# FILE:\s*", code, flags=re.MULTILINE)

    for part in parts:
        if not part.strip():
            continue
        lines = part.splitlines()
        if not lines:
            continue
        filename = lines[0].strip()
        content = "\n".join(lines[1:])
        files[filename] = content
    return files


def get_function_signatures(tree):
    signatures = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            signatures[node.name] = {
                "args": [arg.arg for arg in node.args.args],
                "kwonlyargs": [arg.arg for arg in node.args.kwonlyargs],
                "vararg": node.args.vararg.arg if node.args.vararg else None,
                "kwarg": node.args.kwarg.arg if node.args.kwarg else None,
            }
    return signatures


def get_class_names(tree):
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}


def get_imports(tree):
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.add(f"{module}.{alias.name}")
    return imports


def validate_fix_scope(original_code, fixed_code):
    """
    Validate generated patches to prevent destructive, hallucinated, 
    or incomplete edits.
    """
    # 0. Reject Incomplete/Lazy AI Patterns (Artifacts)
    BAD_PATTERNS = [
        "... rest of",
        "unchanged code",
        "rest of function remains same",
        "omitted code",
        "..."
    ]
    
    fixed_code_str = str(fixed_code)
    for pattern in BAD_PATTERNS:
        if pattern.lower() in fixed_code_str.lower():
            return {
                "valid": False,
                "reason": f"Incomplete generated patch detected: {pattern}"
            }

    # Allow initialization when original code is empty
    if not original_code or not str(original_code).strip():
        return {"valid": True, "reason": "Initial codebase is empty; allowing initialization."}

    # 1. Reject Massive Rewrites (Length/Line Delta)
    original_len = len(str(original_code))
    fixed_len = len(fixed_code_str)

    if fixed_len < original_len * 0.5:
        return {"valid": False, "reason": "Patch removed too much code"}

    original_lines = len(str(original_code).splitlines())
    fixed_lines = len(fixed_code_str.splitlines())

    if abs(fixed_lines - original_lines) > 200:
        return {"valid": False, "reason": "Patch changed too many lines"}

    # 2. Prevent Printing Changes
    if fixed_code_str.count("print(") > str(original_code).count("print("):
        return {"valid": False, "reason": "Added new print statements."}

    original_print_calls = re.findall(r"print\s*\((.*?)\)", str(original_code), re.DOTALL)
    fixed_print_calls = re.findall(r"print\s*\((.*?)\)", fixed_code_str, re.DOTALL)

    if original_print_calls != fixed_print_calls:
        return {"valid": False, "reason": "Modified print statements."}

    # 3. AST Validation
    try:
        original_files = parse_multi_file(original_code)
        fixed_files = parse_multi_file(fixed_code_str)

        if not original_files:
            original_files = {"default": original_code}
        if not fixed_files:
            fixed_files = {"default": fixed_code_str}

        for filename in fixed_files:
            if filename not in original_files:
                return {"valid": False, "reason": f"New file introduced: {filename}"}

        for filename, fixed_content in fixed_files.items():
            original_content = original_files.get(filename)
            if original_content is None:
                continue

            try:
                original_tree = ast.parse(original_content)
                fixed_tree = ast.parse(fixed_content)
            except SyntaxError as e:
                return {"valid": False, "reason": f"Syntax error in {filename}: {e}"}

            if get_function_signatures(original_tree) != get_function_signatures(fixed_tree):
                return {"valid": False, "reason": f"Function signature changed in {filename}"}

            if get_class_names(original_tree) != get_class_names(fixed_tree):
                return {"valid": False, "reason": f"Classes modified or removed in {filename}"}

            original_imports = get_imports(original_tree)
            fixed_imports = get_imports(fixed_tree)
            if len(fixed_imports - original_imports) > 5:
                return {"valid": False, "reason": "Too many imports added"}

    except Exception as e:
        return {"valid": False, "reason": f"AST Validation Error: {str(e)}"}

    return {"valid": True, "reason": "Validation passed."}