import difflib

def generate_diff(old_text: str, new_text: str):
    if not old_text:
        old_text = ""
    if not new_text:
        new_text = ""
        
    diff = difflib.unified_diff(
        old_text.splitlines(), 
        new_text.splitlines(), 
        fromfile='original', 
        tofile='fixed', 
        lineterm=''
    )
    return "\n".join(list(diff))