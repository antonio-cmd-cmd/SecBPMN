from app.llm.prompts.prompt_threat_analysis import prompt

def clean_up_bpmn_xml(xml_string: str) -> str:
    """
    Removes all <bpmndi:BPMNDiagram> elements (and their nested contents) from the BPMN XML.

    This function was written with the help of ChatGPT.
    """
    import re
    
    cleaned_xml = re.sub(
        r"<bpmndi:BPMNDiagram[^>]*>.*?</bpmndi:BPMNDiagram>", "", xml_string, flags=re.DOTALL
    )

    print("Cleaned BPMN XML for analysis:", cleaned_xml)

    return cleaned_xml

def build_analysis_query(xml_string: str, context: dict, principles: list) -> str:
    # Format inputs
    context_str = f"""
- Process Goal:: {context.get('processQuestion')}
- Technologies: {context.get('systemQuestion')}
- Roles: {context.get('roleQuestion')}
- Other notes: {context.get('otherQuestion')}"""

    principles_str = ", ".join(principles)

    clean_bpmn_xml = clean_up_bpmn_xml(xml_string)

    # Create prompt from template
    formatted_prompt = prompt.format(
        context=context_str,
        principles=principles_str,
        bpmn_xml=clean_bpmn_xml
    )
    
    return formatted_prompt
