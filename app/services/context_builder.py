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

    graph = build_dependency_graph(base_path)

    imports = extract_imports(target_file)

    related_files = find_related_files(
        target_file.split("\\")[-1],
        graph
    )

    callers = []

    if function_name:
        callers = find_callers(
            function_name,
            base_path
        )

    usages = []

    if function_name:
        usages = find_usages(
            function_name,
            base_path
        )

    print("=" * 50)
    print("REPOSITORY CONTEXT")
    print("IMPORTS:", imports)
    print("RELATED FILES:", related_files)
    print("CALLERS:", callers)
    print("USAGES:", usages)
    print("=" * 50)

    return {
        "imports": imports,
        "related_files": related_files,
        "callers": callers,
        "usages": usages,
    }