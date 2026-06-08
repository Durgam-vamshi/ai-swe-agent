import re

def parse_llm_response(response: str):
    try:
        # 1. Broadly check for the critical FIXED_CODE marker
        if "FIXED_CODE:" not in response:
            raise Exception("FIXED_CODE marker not found in response")

        # 2. Extract Explanation safely from the raw response text
        explanation_match = re.search(
            r"EXPLANATION:\s*(.*?)(?:FIXED_CODE:|$)",
            response,
            re.DOTALL | re.IGNORECASE
        )
        
        explanation = None
        if explanation_match:
            extracted_text = explanation_match.group(1).strip()
            if extracted_text and extracted_text.lower() != "no explanation":
                explanation = extracted_text

        # 3. Extract the entire Fixed Code block
        code_match = re.search(
            r"FIXED_CODE:\s*(.*)$",
            response,
            re.DOTALL
        )

        if not code_match:
            raise Exception("Failed to cleanly isolate code blocks post FIXED_CODE tag")

        code = code_match.group(1).strip()

        # 4. Strip out trailing argument specifications if appended by the LLM
        if "ARGS:" in code:
            code = code.split("ARGS:")[0].strip()

        # 5. Strip markdown triple-backtick wrapping if the model explicitly returned them
        code = re.sub(r"^```[a-zA-Z0-9_+]*\n|```$", "", code, flags=re.DOTALL).strip()

        # 6. Extract Target File metadata if present (fallback gracefully if omitted in multi-file setups)
        target_file = "unknown"
        if "TARGET_FILE:" in response:
            try:
                target_file = response.split("TARGET_FILE:", 1)[1].split("\n")[0].strip()
            except Exception:
                pass

        return {
            "target_file": target_file,
            "explanation": explanation,
            "fixed_code": code
        }

    except Exception as e:
        raise Exception(f"Parsing failed: {str(e)} | Raw: {response}")