import re

def parse_llm_output(response: str):
    try:
        target_file = re.search(r"TARGET_FILE:\s*(.*)", response).group(1)
        explanation = re.search(r"EXPLANATION:\s*(.*)", response).group(1)
        code = re.search(r"```python(.*?)```", response, re.DOTALL).group(1)

        return {
            "target_file": target_file.strip(),
            "explanation": explanation.strip(),
            "code": code.strip()
        }
    except:
        raise Exception("Invalid LLM format")