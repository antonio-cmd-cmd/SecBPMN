import json5

# --- Load JSON-ish JS File ---
def load_knowledge_base(js_path: str):
    with open(js_path, "r") as f:
        js_content = f.read()
    js_content = js_content.strip().rstrip(";")
    return json5.loads(js_content)