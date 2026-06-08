from app.services.repository_analyzer import build_dependency_graph

graph = build_dependency_graph("app")

for file, imports in graph.items():

    print("\nFILE:", file)

    for imp in imports:
        print("  ->", imp)