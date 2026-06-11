from app.services.repository_analyzer import (
    extract_imports,
    build_dependency_graph,
    find_related_files,
    find_callers,
)

from app.services.usage_search import find_usages


def build_repository_context(
    target_file,
    base_path,
    function_name=None
):
    MAX_CONTEXT_CHARS = 2000

    graph = build_dependency_graph(base_path)
    imports = extract_imports(target_file)
    related_files = find_related_files(
        target_file.split("\\")[-1],
        graph
    )

    callers = []
    if function_name:
        callers = find_callers(function_name, base_path)

    usages = []
    if function_name:
        usages = find_usages(function_name, base_path)

    # Prepare context dictionary
    context_data = {
        "imports": imports,
        "related_files": related_files,
        "callers": callers,
        "usages": usages,
    }

    # Convert to string to enforce character limit
    context_text = str(context_data)
    
    # Apply hard cap
    if len(context_text) > MAX_CONTEXT_CHARS:
        context_text = context_text[:MAX_CONTEXT_CHARS] + "...[TRUNCATED]"

    # Optional: Log the size for debugging
    # print(f"DEBUG: Context size = {len(context_text)} chars")

    return context_data