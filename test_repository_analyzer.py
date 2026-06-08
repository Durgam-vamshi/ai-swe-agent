from app.services.repository_analyzer import extract_imports

imports = extract_imports(
    "app/services/agent.py"
)

print(imports)