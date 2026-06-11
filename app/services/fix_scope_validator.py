

# import ast
# import re


# def parse_multi_file(code: str):
#     """
#     Parses code blocks containing:

#     # FILE: path/to/file.py

#     markers into:

#     {
#         filename: content
#     }
#     """
#     files = {}

#     parts = re.split(
#         r"^# FILE:\s*",
#         code,
#         flags=re.MULTILINE,
#     )

#     for part in parts:
#         if not part.strip():
#             continue

#         lines = part.splitlines()

#         if not lines:
#             continue

#         filename = lines[0].strip()
#         content = "\n".join(lines[1:])

#         files[filename] = content

#     return files


# def get_function_signatures(tree):
#     signatures = {}

#     for node in ast.walk(tree):
#         if isinstance(
#             node,
#             (
#                 ast.FunctionDef,
#                 ast.AsyncFunctionDef,
#             ),
#         ):
#             signatures[node.name] = {
#                 "args": [
#                     arg.arg
#                     for arg in node.args.args
#                 ],
#                 "kwonlyargs": [
#                     arg.arg
#                     for arg in node.args.kwonlyargs
#                 ],
#                 "vararg": (
#                     node.args.vararg.arg
#                     if node.args.vararg
#                     else None
#                 ),
#                 "kwarg": (
#                     node.args.kwarg.arg
#                     if node.args.kwarg
#                     else None
#                 ),
#             }

#     return signatures


# def get_class_names(tree):
#     return {
#         node.name
#         for node in ast.walk(tree)
#         if isinstance(node, ast.ClassDef)
#     }


# def get_imports(tree):
#     imports = set()

#     for node in ast.walk(tree):
#         if isinstance(node, ast.Import):
#             for alias in node.names:
#                 imports.add(alias.name)

#         elif isinstance(node, ast.ImportFrom):
#             module = node.module or ""
#             for alias in node.names:
#                 imports.add(
#                     f"{module}.{alias.name}"
#                 )

#     return imports


# def validate_fix_scope(
#     original_code,
#     fixed_code,
# ):
#     """
#     Validate generated patches to prevent
#     destructive or hallucinated edits.
#     """

#     # Allow initialization when original code is empty
#     if (
#         not original_code
#         or not str(original_code).strip()
#     ):
#         return {
#             "valid": True,
#             "reason": (
#                 "Initial codebase is empty; "
#                 "allowing initialization."
#             ),
#         }

#     # ----------------------
#     # A. Reject Massive Rewrites
#     # ----------------------
#     original_len = len(str(original_code))
#     fixed_len = len(str(fixed_code))

#     if fixed_len < original_len * 0.5:
#         return {
#             "valid": False,
#             "reason": "Patch removed too much code"
#         }

#     # Prevent extra print statements
#     original_prints = original_code.count(
#         "print("
#     )

#     fixed_prints = fixed_code.count(
#         "print("
#     )

#     if fixed_prints > original_prints:
#         return {
#             "valid": False,
#             "reason": (
#                 "Added new print statements."
#             ),
#         }

#     # Prevent changing existing print content
#     original_print_calls = re.findall(
#         r"print\s*\((.*?)\)",
#         original_code,
#         re.DOTALL,
#     )

#     fixed_print_calls = re.findall(
#         r"print\s*\((.*?)\)",
#         fixed_code,
#         re.DOTALL,
#     )

#     if original_print_calls != fixed_print_calls:
#         return {
#             "valid": False,
#             "reason": (
#                 "Modified print statements."
#             ),
#         }

#     try:
#         original_files = parse_multi_file(
#             original_code
#         )

#         fixed_files = parse_multi_file(
#             fixed_code
#         )

#         if not original_files:
#             original_files = {
#                 "default": original_code
#             }

#         if not fixed_files:
#             fixed_files = {
#                 "default": fixed_code
#             }

#         # ----------------------
#         # B. Reject New Files
#         # ----------------------
#         for filename in fixed_files:
#             if filename not in original_files:
#                 return {
#                     "valid": False,
#                     "reason": f"New file introduced: {filename}"
#                 }

#         for filename, fixed_content in fixed_files.items():

#             original_content = (
#                 original_files.get(filename)
#             )

#             if original_content is None:
#                 continue

#             try:
#                 original_tree = ast.parse(
#                     original_content
#                 )

#                 fixed_tree = ast.parse(
#                     fixed_content
#                 )

#             except SyntaxError as e:
#                 return {
#                     "valid": False,
#                     "reason": (
#                         f"Syntax error in "
#                         f"{filename}: {e}"
#                     ),
#                 }

#             # ----------------------
#             # Function Validation
#             # ----------------------
#             original_functions = (
#                 get_function_signatures(
#                     original_tree
#                 )
#             )

#             fixed_functions = (
#                 get_function_signatures(
#                     fixed_tree
#                 )
#             )

#             for (
#                 func_name,
#                 original_signature,
#             ) in original_functions.items():

#                 if func_name not in fixed_functions:
#                     return {
#                         "valid": False,
#                         "reason": (
#                             f"Function removed "
#                             f"in {filename}: "
#                             f"{func_name}"
#                         ),
#                     }

#                 fixed_signature = (
#                     fixed_functions[
#                         func_name
#                     ]
#                 )

#                 if (
#                     fixed_signature
#                     != original_signature
#                 ):
#                     return {
#                         "valid": False,
#                         "reason": (
#                             f"Function signature "
#                             f"changed in "
#                             f"{filename}: "
#                             f"{func_name}"
#                         ),
#                     }

#             # ----------------------
#             # C. Class Validation
#             # ----------------------
#             original_classes = (
#                 get_class_names(
#                     original_tree
#                 )
#             )

#             fixed_classes = (
#                 get_class_names(
#                     fixed_tree
#                 )
#             )

#             removed_classes = (
#                 original_classes
#                 - fixed_classes
#             )

#             if removed_classes:
#                 return {
#                     "valid": False,
#                     "reason": (
#                         f"Removed classes in "
#                         f"{filename}: "
#                         f"{', '.join(sorted(removed_classes))}"
#                     ),
#                 }

#             # ----------------------
#             # D. Import Validation
#             # ----------------------
#             original_imports = (
#                 get_imports(
#                     original_tree
#                 )
#             )

#             fixed_imports = (
#                 get_imports(
#                     fixed_tree
#                 )
#             )

#             removed_imports = (
#                 original_imports
#                 - fixed_imports
#             )

#             if removed_imports:
#                 return {
#                     "valid": False,
#                     "reason": (
#                         f"Removed imports in "
#                         f"{filename}: "
#                         f"{', '.join(sorted(removed_imports))}"
#                     ),
#                 }

#     except Exception as e:
#         return {
#             "valid": False,
#             "reason": (
#                 f"AST Validation Error: "
#                 f"{str(e)}"
#             ),
#         }

#     return {
#         "valid": True,
#         "reason": "Validation passed.",
#     }


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

    parts = re.split(
        r"^# FILE:\s*",
        code,
        flags=re.MULTILINE,
    )

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
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            signatures[node.name] = {
                "args": [
                    arg.arg
                    for arg in node.args.args
                ],
                "kwonlyargs": [
                    arg.arg
                    for arg in node.args.kwonlyargs
                ],
                "vararg": (
                    node.args.vararg.arg
                    if node.args.vararg
                    else None
                ),
                "kwarg": (
                    node.args.kwarg.arg
                    if node.args.kwarg
                    else None
                ),
            }

    return signatures


def get_class_names(tree):
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
    }


def get_imports(tree):
    imports = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.add(
                    f"{module}.{alias.name}"
                )

    return imports


def validate_fix_scope(
    original_code,
    fixed_code,
):
    """
    Validate generated patches to prevent
    destructive or hallucinated edits.
    """

    # Allow initialization when original code is empty
    if (
        not original_code
        or not str(original_code).strip()
    ):
        return {
            "valid": True,
            "reason": (
                "Initial codebase is empty; "
                "allowing initialization."
            ),
        }

    # ----------------------
    # A. Reject Massive Rewrites
    # ----------------------
    original_len = len(str(original_code))
    fixed_len = len(str(fixed_code))

    if fixed_len < original_len * 0.5:
        return {
            "valid": False,
            "reason": "Patch removed too much code"
        }

    # Line Delta Guard (Prevents sprawling hallucinations)
    original_lines = len(
        str(original_code).splitlines()
    )

    fixed_lines = len(
        str(fixed_code).splitlines()
    )

    if abs(fixed_lines - original_lines) > 200:
        return {
            "valid": False,
            "reason": "Patch changed too many lines"
        }

    # Prevent extra print statements
    original_prints = original_code.count(
        "print("
    )

    fixed_prints = fixed_code.count(
        "print("
    )

    if fixed_prints > original_prints:
        return {
            "valid": False,
            "reason": (
                "Added new print statements."
            ),
        }

    # Prevent changing existing print content
    original_print_calls = re.findall(
        r"print\s*\((.*?)\)",
        original_code,
        re.DOTALL,
    )

    fixed_print_calls = re.findall(
        r"print\s*\((.*?)\)",
        fixed_code,
        re.DOTALL,
    )

    if original_print_calls != fixed_print_calls:
        return {
            "valid": False,
            "reason": (
                "Modified print statements."
            ),
        }

    try:
        original_files = parse_multi_file(
            original_code
        )

        fixed_files = parse_multi_file(
            fixed_code
        )

        if not original_files:
            original_files = {
                "default": original_code
            }

        if not fixed_files:
            fixed_files = {
                "default": fixed_code
            }

        # ----------------------
        # B. Reject New Files
        # ----------------------
        for filename in fixed_files:
            if filename not in original_files:
                return {
                    "valid": False,
                    "reason": f"New file introduced: {filename}"
                }

        for filename, fixed_content in fixed_files.items():

            original_content = (
                original_files.get(filename)
            )

            if original_content is None:
                continue

            try:
                original_tree = ast.parse(
                    original_content
                )

                fixed_tree = ast.parse(
                    fixed_content
                )

            except SyntaxError as e:
                return {
                    "valid": False,
                    "reason": (
                        f"Syntax error in "
                        f"{filename}: {e}"
                    ),
                }

            # ----------------------
            # Function Validation
            # ----------------------
            original_functions = (
                get_function_signatures(
                    original_tree
                )
            )

            fixed_functions = (
                get_function_signatures(
                    fixed_tree
                )
            )

            for (
                func_name,
                original_signature,
            ) in original_functions.items():

                if func_name not in fixed_functions:
                    return {
                        "valid": False,
                        "reason": (
                            f"Function removed "
                            f"in {filename}: "
                            f"{func_name}"
                        ),
                    }

                fixed_signature = (
                    fixed_functions[
                        func_name
                    ]
                )

                if (
                    fixed_signature
                    != original_signature
                ):
                    return {
                        "valid": False,
                        "reason": (
                            f"Function signature "
                            f"changed in "
                            f"{filename}: "
                            f"{func_name}"
                        ),
                    }

            # ----------------------
            # C. Class Validation
            # ----------------------
            original_classes = (
                get_class_names(
                    original_tree
                )
            )

            fixed_classes = (
                get_class_names(
                    fixed_tree
                )
            )

            removed_classes = (
                original_classes
                - fixed_classes
            )

            if removed_classes:
                return {
                    "valid": False,
                    "reason": (
                        f"Removed classes in "
                        f"{filename}: "
                        f"{', '.join(sorted(removed_classes))}"
                    ),
                }

            # ----------------------
            # D. Import Validation
            # ----------------------
            original_imports = (
                get_imports(
                    original_tree
                )
            )

            fixed_imports = (
                get_imports(
                    fixed_tree
                )
            )

            removed_imports = (
                original_imports
                - fixed_imports
            )

            if removed_imports:
                return {
                    "valid": False,
                    "reason": (
                        f"Removed imports in "
                        f"{filename}: "
                        f"{', '.join(sorted(removed_imports))}"
                    ),
                }

    except Exception as e:
        return {
            "valid": False,
            "reason": (
                f"AST Validation Error: "
                f"{str(e)}"
            ),
        }

    return {
        "valid": True,
        "reason": "Validation passed.",
    }







