"""
Mitigation Loader Utility

This module loads mitigation best practices from a JSON file and prepares them
for storage in a vector database.
"""
import json
from typing import List, Dict
from langchain_core.documents import Document


def load_mitigation_practices(json_path: str) -> List[Document]:
    """
    Load mitigation best practices from a JSON file and convert them to LangChain Documents.
    
    Args:
        json_path: Path to the mitigation.json file
        
    Returns:
        List of Document objects suitable for vectorstore
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        documents = []
        
        # Handle both old and new JSON structure
        best_practices = data if isinstance(data, list) else data.get('best_practices', [])
        
        for practice in best_practices:
            # Get fields from new structure
            practice_id = practice.get('id', 'N/A')
            best_practice_name = practice.get('best_practice', practice.get('title', 'N/A'))
            mitigated_threats = practice.get('mitigated_threats', [])
            mitigation_strategies = practice.get('mitigation_strategies', [])
            
            # Format mitigated threats for better searchability
            threats_text = ", ".join(mitigated_threats) if mitigated_threats else "N/A"
            
            # Format mitigation strategies
            strategies_text = "\n".join([f"  - {strat}" for strat in mitigation_strategies]) if mitigation_strategies else "N/A"
            
            # Create rich text content combining all fields with emphasis on mitigated_threats
            content = f"""
Best Practice: {best_practice_name}

Mitigated Threats: {threats_text}

Mitigation Strategies:
{strategies_text}
"""
            
            # Create metadata with mitigated_threats for filtering
            metadata = {
                'id': practice_id,
                'best_practice': best_practice_name,
                'mitigated_threats': threats_text,
                'type': 'mitigation'
            }
            
            # Create Document
            doc = Document(
                page_content=content.strip(),
                metadata=metadata
            )
            documents.append(doc)
        
        print(f"Loaded {len(documents)} mitigation practices from {json_path}")
        return documents
        
    except Exception as e:
        print(f"Error loading mitigation practices: {e}")
        raise
