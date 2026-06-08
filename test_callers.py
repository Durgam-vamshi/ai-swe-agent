from app.services.repository_analyzer import find_callers

callers = find_callers(
    "validate_with_tests",
    "app"
)

print("\nCALLERS:\n")

for caller in callers:
    print(caller)