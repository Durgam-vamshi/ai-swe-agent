from app.services.test_generator import generate_tests

code = """
def divide(a, b):
    return a / b
"""

issue = "Handle division by zero"

tests = generate_tests(code, issue)

print(tests)