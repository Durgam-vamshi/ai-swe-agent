# def classify_error(stderr: str):
#     if not stderr:
#         return "NO_ERROR"

#     stderr_lower = stderr.lower()

#     if "modulenotfounderror" in stderr_lower:
#         return "MISSING_DEPENDENCY"

#     if "syntaxerror" in stderr_lower:
#         return "SYNTAX_ERROR"

#     if "nameerror" in stderr_lower:
#         return "NAME_ERROR"

#     if "typeerror" in stderr_lower:
#         return "TYPE_ERROR"

#     return "UNKNOWN_ERROR"




def classify_error(stderr: str, stdout: str = ""):
    text = f"{stderr}\n{stdout}".lower()

    if "zerodivisionerror" in text:
        return "ZeroDivisionError"

    if "modulenotfounderror" in text:
        return "ModuleNotFoundError"

    if "importerror" in text:
        return "ImportError"

    if "syntaxerror" in text:
        return "SyntaxError"

    if "typeerror" in text:
        return "TypeError"

    if "valueerror" in text:
        return "ValueError"

    if "keyerror" in text:
        return "KeyError"

    if "indexerror" in text:
        return "IndexError"

    if "attributeerror" in text:
        return "AttributeError"

    if "nameerror" in text:
        return "NameError"

    if "assertionerror" in text:
        return "AssertionError"

    if "cannot divide by zero" in text:
        return "ZeroDivisionError"

    return "UNKNOWN_ERROR"