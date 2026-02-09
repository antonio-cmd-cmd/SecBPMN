"""
Mitigation Retriever Utility

This module provides functions to retrieve relevant mitigation strategies
from the mitigation vectorstore based on threats identified in BPMN analysis.
"""
from typing import List, Dict


def retrieve_mitigations_for_threats(
    mitigation_chain,
    threats: List[str],
    context: Dict = None,
    max_mitigations_per_threat: int = 3
) -> str:
    """
    Retrieve relevant mitigation strategies for a list of identified threats.
    
    Args:
        mitigation_chain: QA chain for mitigation vectorstore
        threats: List of threat names/descriptions
        context: Optional context information (process context, element types, etc.)
        max_mitigations_per_threat: Maximum number of mitigation strategies to retrieve per threat
        
    Returns:
        Formatted string containing relevant mitigation strategies
    """
    all_mitigations = []
    
    for threat in threats:
        # Build query for this threat
        query = f"Mitigation strategies and best practices for: {threat}"
        
        if context:
            # Add context to make retrieval more relevant
            context_str = f"Process context: {context.get('processQuestion', '')}"
            query += f". {context_str}"
        
        try:
            # Query the mitigation vectorstore
            result = mitigation_chain.invoke({"query": query})
            
            # Extract mitigation practices from source documents
            if 'source_documents' in result:
                for doc in result['source_documents'][:max_mitigations_per_threat]:
                    mitigation_info = {
                        'threat': threat,
                        'title': doc.metadata.get('title', 'N/A'),
                        'category': doc.metadata.get('category', 'N/A'),
                        'description': doc.page_content.split('Description:')[-1].strip() if 'Description:' in doc.page_content else doc.page_content
                    }
                    all_mitigations.append(mitigation_info)
        except Exception as e:
            print(f"Error retrieving mitigations for threat '{threat}': {e}")
            continue
    
    # Format mitigations for inclusion in prompt
    return format_mitigations(all_mitigations)


def format_mitigations(mitigations: List[Dict]) -> str:
    """
    Format retrieved mitigations into a readable string for the LLM prompt.
    
    Args:
        mitigations: List of mitigation information dictionaries
        
    Returns:
        Formatted string
    """
    if not mitigations:
        return "No specific mitigation strategies found in database."
    
    formatted = "## Retrieved Mitigation Best Practices:\n\n"
    
    # Group by threat
    threats_dict = {}
    for mit in mitigations:
        threat = mit['threat']
        if threat not in threats_dict:
            threats_dict[threat] = []
        threats_dict[threat].append(mit)
    
    for threat, threat_mits in threats_dict.items():
        formatted += f"### For threat: {threat}\n\n"
        for mit in threat_mits:
            formatted += f"- **{mit['title']}** (Category: {mit['category']})\n"
            formatted += f"  {mit['description']}\n\n"
    
    return formatted


def extract_threats_from_analysis(threat_analysis: str) -> List[str]:
    """
    Extract threat names from the threat analysis markdown.
    
    Args:
        threat_analysis: Threat analysis markdown text
        
    Returns:
        List of threat names
    """
    threats = []
    lines = threat_analysis.split('\n')
    
    for line in lines:
        # Look for lines with "Potential Threat:"
        if '**Potential Threat**:' in line:
            # Extract the threat name
            threat = line.split('**Potential Threat**:')[1].strip()
            if threat and threat not in threats:
                threats.append(threat)
    
    return threats
