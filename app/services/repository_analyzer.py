import os
import ast
import re 


def discover_python_files(base_path):
    files = []
    for root, _, filenames in os.walk(base_path):
        # 1. Skip the entire directory if it's a __pycache__ folder
        if "__pycache__" in root:
            continue

        for file in filenames:
            # 2. Skip temporary files
            if file.startswith("temp_"):
                continue

            # 3. Only append if it's a valid python file
            if file.endswith(".py"):
                files.append(os.path.join(root, file))
                
    return files


def build_dependency_graph(base_path):
    graph = {}
    files = discover_python_files(base_path)
    for file in files:
        graph[file] = extract_imports(file)
    return graph


def find_related_files(target_file, graph):
    related = []
    target_name = target_file.replace(".py", "")

    for file, imports in graph.items():
        if target_file in file:
            continue
        for imp in imports:
            if target_name in imp:
                related.append(file)
                break
    return related


def extract_imports(file_path):
    imports = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.append(name.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

    except Exception as e:
        print("FAILED FILE DURING IMPORT EXTRACT:", file_path)
        print("ERROR:", e)

    return imports


def find_callers(function_name, base_path):
    callers = []
    
    # Leverages discover_python_files which handles __pycache__, temp_, and .py matching
    files = discover_python_files(base_path)

    for path in files:
        # Since 'path' comes from discover_python_files, it is already a full path.
        # We extract the file name to run your requested 'temp_' rule safely here too.
        file = os.path.basename(path)
        if file.startswith("temp_"):
            continue

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            call_pattern = rf"\b{function_name}\s*\("
            definition_pattern = rf"def\s+{function_name}\s*\("

            has_call = re.search(call_pattern, content)
            defines_function = re.search(definition_pattern, content)

            if has_call and not defines_function:
                callers.append(path)

        except Exception as e:
            print("FAILED FILE DURING CALLER SEARCH:", path)
            print("ERROR:", e)

    return callers






