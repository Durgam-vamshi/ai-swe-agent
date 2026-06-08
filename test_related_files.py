from app.services.repository_analyzer import (
    build_dependency_graph,
    find_related_files
)

graph = build_dependency_graph("app")

related = find_related_files(
    "test_validator.py",
    graph
)

print("\nRELATED FILES:\n")

for f in related:
    print(f)