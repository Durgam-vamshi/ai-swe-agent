

from app.services.llm_client import call_llm

TEST_PROMPT = """
You are an expert Python QA engineer and pytest specialist.

Return ONLY executable pytest code.

CRITICAL RULES:
* Output valid Python code only
* Output valid pytest code only
* No markdown
* No explanations
* No comments
* No TARGET_FILE
* No EXPLANATION
* No FIXED_CODE
* No prose
* No undefined variables
* No placeholder code
* No pseudocode
* Tests must be syntactically valid
* Tests must compile successfully
* Tests must not contain incomplete expressions
* Tests must not contain unfinished function calls
* Tests must be executable
* Import pytest when required

TEST INTEGRITY MANDATE:
* Generate tests ONLY for behavior explicitly present in the provided code.
* Do NOT invent edge cases or assume hidden requirements.
* Do NOT assume exceptions or error handling that are not written in the code.
* Only generate tests that are logically and mathematically correct.
* Do NOT invent or hallucinate expected outputs.
* Trace and calculate outputs directly from the code implementation.
* Source code is the ground truth.

BUG VERIFICATION RULES:
* Before generating regression tests, verify the reported bug can actually occur in the provided source code.
* Never generate regression tests for behavior that does not exist in the implementation.
* Never invent ValueError, ZeroDivisionError, KeyError, IndexError, TypeError, RuntimeError, or custom exceptions.
* Only test exceptions that are explicitly raised in the source code.
* If the reported bug contradicts the source code, trust the source code.
* If the bug cannot be reproduced from the source code, DO NOT generate regression tests.
* Multiplication by zero returns 0 unless the source code explicitly raises an exception.
* Do not modify mathematical behavior based on the issue description.

Generate:
1. Normal test cases
2. Edge case tests based ONLY on actual code logic
3. Regression tests ONLY if the bug is observable in the code

If you are unsure about imports, generate tests that are self-contained and syntactically correct.
"""


def generate_tests(code: str, issue: str, file_name: str) -> str:
    base_module = file_name.replace(".py", "").replace("\\", "/").split("/")[-1]

    prompt = f"""
Generate pytest tests for this Python code.

TARGET FILE:
{file_name}

Requirements:
- Use pytest
- ALWAYS include:
  import pytest
- Import functions from target file
- Test normal behavior
- Test edge cases
- Return ONLY executable Python test code

Example import:
from {base_module} import *

CRITICAL:
* Return ONLY executable pytest code
* Tests must be syntactically valid
* Generate tests ONLY for behavior present in the code.
* Do NOT invent edge cases or assume hidden requirements.
* Do NOT assume exceptions that do not exist in the source code.
* Do NOT invent ValueError, ZeroDivisionError, KeyError, IndexError, TypeError, RuntimeError, or custom exceptions.
* Only test exceptions explicitly present in the code.
* Do NOT invent expected outputs.
* Calculate outputs directly from the implementation.
* No markdown
* No explanations
* No undefined symbols
* No incomplete statements
* No unfinished function calls
* Generate realistic assertions

REGRESSION TEST RULES:
* First determine whether the reported bug can actually occur.
* Generate regression tests ONLY if the bug is observable in the code.
* If the bug cannot be reproduced from the code, skip regression tests completely.
* Trust the source code over the issue description.

ISSUE:
{issue}

CODE:
{code}
"""
    
    response = call_llm(
        prompt,
        system_prompt=TEST_PROMPT
    )

    return response.strip()