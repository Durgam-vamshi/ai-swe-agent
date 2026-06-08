from app.services.context_builder import (
    build_repository_context
)

context = build_repository_context(
    "app/services/test_validator.py",
    "app",
    "validate_with_tests"
)

print(context)