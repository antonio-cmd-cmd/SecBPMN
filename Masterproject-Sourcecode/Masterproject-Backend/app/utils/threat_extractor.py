"""
Threat Extraction Utility

This module provides functions to extract threat information from BPMN analysis
and context to enable targeted mitigation retrieval.
"""
from typing import List, Set, Dict
import re


def extract_threat_keywords(
    principles: List[str],
    context: Dict = None
) -> List[str]:
    """
    Extract threat-related keywords from security principles and context.
    
    Args:
        principles: List of security principles (e.g., ["Integrity", "Confidentiality"])
        context: Optional process context dictionary
        
    Returns:
        List of threat keywords for targeted RAG queries
    """
    threat_keywords = []
    
    # Map principles to common insider threats
    principle_threat_mapping = {
        "integrity": [
            "Data Corruption",
            "Unauthorized Data Modification",
            "Data Falsification",
            "Sabotage"
        ],
        "confidentiality": [
            "Data Leakage",
            "Unauthorized Access",
            "Information Disclosure",
            "Theft of Intellectual Property",
            "Corporate Espionage"
        ],
        "availability": [
            "Denial of Service",
            "Sabotage of critical infrastructure",
            "System Disruption",
            "Service Interruption"
        ],
        "accountability": [
            "Privilege Abuse",
            "Circumventing Security Controls",
            "Unauthorized Activity",
            "Non-repudiation Violations"
        ],
        "authenticity": [
            "Identity Theft",
            "Credential Misuse",
            "Impersonation",
            "Unauthorized Access"
        ],
        "authorization": [
            "Privilege Escalation",
            "Unauthorized Access",
            "Access Control Violations",
            "Privilege Abuse"
        ],
        "non-repudiation": [
            "Activity Denial",
            "Log Manipulation",
            "Audit Trail Tampering"
        ]
    }
    
    # Extract threats based on selected principles
    for principle in principles:
        principle_lower = principle.lower()
        if principle_lower in principle_threat_mapping:
            threat_keywords.extend(principle_threat_mapping[principle_lower])
    
    # Add context-specific threats if available
    if context:
        # Check for sensitive operations in context
        context_text = " ".join([
            str(context.get('processQuestion', '')),
            str(context.get('systemQuestion', '')),
            str(context.get('roleQuestion', '')),
            str(context.get('otherQuestion', ''))
        ]).lower()
        
        # Add threats based on keywords in context
        if any(word in context_text for word in ['financial', 'payment', 'transaction', 'money']):
            threat_keywords.extend(["Fraud", "Financial Manipulation"])
        
        if any(word in context_text for word in ['data', 'information', 'database', 'record']):
            threat_keywords.extend(["Data Breach", "Unintentional data loss"])
        
        if any(word in context_text for word in ['customer', 'client', 'personal']):
            threat_keywords.extend(["Privacy violations", "PII Exposure"])
        
        if any(word in context_text for word in ['privileged', 'admin', 'administrator', 'root']):
            threat_keywords.extend(["Privilege Abuse", "Misuse of privileged access"])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_threats = []
    for threat in threat_keywords:
        if threat not in seen:
            seen.add(threat)
            unique_threats.append(threat)
    
    return unique_threats


def build_targeted_mitigation_query(
    threat_keywords: List[str],
    context: Dict = None,
    principles: List[str] = None
) -> str:
    """
    Build a targeted query for the mitigation vectorstore based on specific threats.
    
    Args:
        threat_keywords: List of threat keywords to search for
        context: Optional process context
        principles: Optional security principles
        
    Returns:
        Formatted query string optimized for RAG retrieval
    """
    # Start with threat-focused query
    query_parts = [
        "Find mitigation strategies and best practices for the following insider threats:"
    ]
    
    # Add specific threats
    if threat_keywords:
        threats_list = ", ".join(threat_keywords[:10])  # Limit to top 10 threats
        query_parts.append(f"Threats: {threats_list}")
    
    # Add context if available
    if context:
        process_goal = context.get('processQuestion', '')
        if process_goal:
            query_parts.append(f"Process context: {process_goal}")
        
        technologies = context.get('systemQuestion', '')
        if technologies:
            query_parts.append(f"Technologies involved: {technologies}")
    
    # Add principles
    if principles:
        principles_str = ", ".join(principles)
        query_parts.append(f"Security principles: {principles_str}")
    
    # Emphasize focus areas
    query_parts.append(
        "Focus on practical mitigation strategies including: "
        "access control, monitoring, separation of duties, administrative controls, "
        "and technical safeguards."
    )
    
    return "\n".join(query_parts)


def format_mitigation_results(
    source_documents: List,
    max_results: int = 15
) -> str:
    """
    Format retrieved mitigation documents for inclusion in the LLM prompt.
    
    Args:
        source_documents: List of retrieved documents from vectorstore
        max_results: Maximum number of results to include
        
    Returns:
        Formatted string with mitigation best practices
    """
    if not source_documents:
        return ""
    
    mitigation_context = "\n## RETRIEVED MITIGATION BEST PRACTICES:\n"
    mitigation_context += "Use these best practices as mitigation strategies when applicable:\n\n"
    
    seen_practices = set()
    count = 0
    
    for doc in source_documents:
        if count >= max_results:
            break
        
        # Extract information from document
        best_practice = doc.metadata.get('best_practice', 'N/A')
        
        # Skip duplicates
        if best_practice in seen_practices:
            continue
        
        seen_practices.add(best_practice)
        count += 1
        
        # Get mitigated threats from metadata
        mitigated_threats = doc.metadata.get('mitigated_threats', '')
        
        # Extract mitigation strategies from content
        content = doc.page_content
        
        # Format the output
        mitigation_context += f"### {count}. {best_practice}\n"
        if mitigated_threats:
            mitigation_context += f"**Addresses threats:** {mitigated_threats}\n\n"
        
        # Include the strategies from the document
        if "Mitigation Strategies:" in content:
            strategies = content.split("Mitigation Strategies:")[1].strip()
            mitigation_context += f"{strategies}\n\n"
        else:
            mitigation_context += f"{content}\n\n"
        
        mitigation_context += "---\n\n"
    
    return mitigation_context
