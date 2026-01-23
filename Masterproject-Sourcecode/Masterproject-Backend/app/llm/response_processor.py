import re

def extract_bpmn_id_suffixes(llm_response: str) -> list[str]:
    """
    Extracts unique BPMN element ID suffixes from the '**BPMN Element ID**' sections
    in the LLM response (e.g., extracts '1d386ik' from 'Activity_1d386ik').
    Args:
        llm_response (str): Full markdown-style string from LLM.
    Returns:
        list[str]: List of unique ID suffixes.

    This function was written with the help of ChatGPT.
    """
    # Locate '**BPMN Element IDs**' blocks
    pattern = r"- \*\*BPMN Element ID[s]?\*\*:\s*(.+)"
    matches = re.findall(pattern, llm_response, flags=re.IGNORECASE)


    suffixes = []
    for match in matches:
         # Match the ids that after an underscore (e.g., 'Task_123abc' -> '123abc')
        found = re.findall(r"[A-Za-z]+_(\w+)", match)
        suffixes.extend(found)

    # Deduplicate while preserving order
    seen = set()
    unique_suffixes = []
    for s in suffixes:
        if s not in seen:
            seen.add(s)
            unique_suffixes.append(s)

    return unique_suffixes


def strip_bpmn_id_blocks(text: str) -> str:
    """
    Removes '- **BPMN Element IDs**:' and all bullet lines that follow it.

    This function was written with the help of ChatGPT.
    """
    pattern = r"^- \*\*BPMN Element ID[s]?\*\*:[^\n]*\n?"
    cleaned = re.sub(pattern, "", text, flags=re.IGNORECASE | re.MULTILINE)
    return cleaned.strip()