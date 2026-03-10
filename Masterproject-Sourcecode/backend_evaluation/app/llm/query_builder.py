from app.llm.prompts.prompt_threat_analysis import prompt
from app.utils.threat_extractor import (
    extract_threat_keywords, 
    build_targeted_mitigation_query,
    format_mitigation_results
)

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

def build_analysis_query(
    xml_string: str, 
    context: dict, 
    principles: list,
    mitigation_chain=None
) -> str:
    """
    Build the analysis query with optional mitigation strategies from RAG.
    
    Args:
        xml_string: BPMN XML content
        context: Process context dictionary
        principles: List of security principles
        mitigation_chain: Optional QA chain for retrieving mitigation strategies
        
    Returns:
        Formatted prompt string
    """
    # Format inputs
    context_str = f"""
- Process Goal:: {context.get('processQuestion')}
- Technologies: {context.get('systemQuestion')}
- Roles: {context.get('roleQuestion')}
- Other notes: {context.get('otherQuestion')}"""

    principles_str = ", ".join(principles)

    clean_bpmn_xml = clean_up_bpmn_xml(xml_string)
    
    # Retrieve relevant mitigation strategies if chain is available
    mitigation_context = ""
    if mitigation_chain is not None:
        try:
            # Extract threat keywords based on principles and context
            threat_keywords = extract_threat_keywords(principles, context)
            print(f"Extracted {len(threat_keywords)} threat keywords: {threat_keywords[:5]}...")
            
            # Build a targeted query using the extracted threats
            mitigation_query = build_targeted_mitigation_query(
                threat_keywords=threat_keywords,
                context=context,
                principles=principles
            )
            
            print("Querying mitigation vectorstore with targeted query...")
            print(f"Query: {mitigation_query[:200]}...")
            
            result = mitigation_chain.invoke({"query": mitigation_query})
            
            # Format the retrieved mitigations using the new formatter
            if 'source_documents' in result and result['source_documents']:
                mitigation_context = format_mitigation_results(
                    result['source_documents'],
                    max_results=15
                )
                print(f"Retrieved {len(result['source_documents'])} mitigation practices")
            else:
                print("No mitigation documents retrieved")
                
        except Exception as e:
            print(f"Error retrieving mitigation strategies: {e}")
            import traceback
            traceback.print_exc()
            mitigation_context = ""

    # Create prompt from template, including mitigation context if available
    formatted_prompt = prompt.format(
        context=context_str,
        principles=principles_str,
        bpmn_xml=clean_bpmn_xml,
        mitigation_context=mitigation_context
    )
    
    return formatted_prompt
