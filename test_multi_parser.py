from app.agent.nodes.multi_file_parser import parse_multi_file

sample = """
# FILE: auth.py
def login():
    return True

# FILE: routes.py
def route():
    return "ok"

# FILE: service.py
def process():
    return 123
"""

result = parse_multi_file(sample)

print(result)