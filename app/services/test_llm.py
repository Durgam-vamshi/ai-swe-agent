from app.services.llm_client import generate_fix

response = generate_fix(
    issue="Fix runtime error",
    code="""
def divide(a,b):
    return a/b

print(divide(10,0))
""",
    file_name="calculator.py"
)

print(response)