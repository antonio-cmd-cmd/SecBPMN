"""
Test script to verify mitigation RAG integration

This script tests the mitigation loading and retrieval functionality.
"""
import os
import sys

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.mitigation_loader import load_mitigation_practices
from app.llm.vectorstore import setup_mitigation_vectorstore
from app.llm.qa_chain import build_mitigation_qa_chain
from app.utils.threat_extractor import (
    extract_threat_keywords,
    build_targeted_mitigation_query,
    format_mitigation_results
)


def test_mitigation_loading():
    """Test loading mitigation practices from JSON"""
    print("=" * 80)
    print("TEST 1: Loading Mitigation Practices")
    print("=" * 80)
    
    mitigation_path = os.path.join("resources", "mitigation.json")
    
    if not os.path.exists(mitigation_path):
        print(f"❌ Error: {mitigation_path} not found!")
        return False
    
    try:
        docs = load_mitigation_practices(mitigation_path)
        print(f"✅ Successfully loaded {len(docs)} mitigation practices")
        
        # Show sample
        if docs:
            print("\nSample mitigation practice:")
            print(f"Title: {docs[0].metadata.get('title')}")
            print(f"Category: {docs[0].metadata.get('category')}")
            print(f"Content: {docs[0].page_content[:200]}...")
        
        return True, docs
    except Exception as e:
        print(f"❌ Error loading mitigations: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_vectorstore_setup(docs):
    """Test setting up the mitigation vectorstore"""
    print("\n" + "=" * 80)
    print("TEST 2: Setting up Mitigation Vectorstore")
    print("=" * 80)
    
    try:
        vectorstore = setup_mitigation_vectorstore(docs)
        print("✅ Successfully created mitigation vectorstore")
        return True, vectorstore
    except Exception as e:
        print(f"❌ Error setting up vectorstore: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_mitigation_retrieval(vectorstore):
    """Test retrieving mitigations"""
    print("\n" + "=" * 80)
    print("TEST 3: Testing Mitigation Retrieval")
    print("=" * 80)
    
    try:
        # Build QA chain
        qa_chain = build_mitigation_qa_chain(vectorstore)
        print("✅ Successfully built mitigation QA chain")
        
        # Test 1: General query
        print("\n--- Test 3.1: General Query ---")
        test_query = "What are the best practices for access control and monitoring privileged users?"
        print(f"Query: {test_query}")
        
        result = qa_chain.invoke({"query": test_query})
        print(f"✅ Retrieved {len(result.get('source_documents', []))} relevant documents")
        
        # Show top results
        print("\nTop 3 relevant mitigation practices:")
        for i, doc in enumerate(result.get('source_documents', [])[:3], 1):
            print(f"\n{i}. {doc.metadata.get('best_practice', 'N/A')}")
            print(f"   Mitigated Threats: {doc.metadata.get('mitigated_threats', 'N/A')}")
        
        # Test 2: Threat-specific query using threat extraction
        print("\n--- Test 3.2: Threat-Specific Query ---")
        test_principles = ["Confidentiality", "Integrity"]
        test_context = {
            'processQuestion': 'Customer data verification process',
            'systemQuestion': 'Database management system',
            'roleQuestion': 'Data analysts and administrators'
        }
        
        # Extract threat keywords
        threat_keywords = extract_threat_keywords(test_principles, test_context)
        print(f"Extracted threat keywords: {threat_keywords[:5]}...")
        
        # Build targeted query
        targeted_query = build_targeted_mitigation_query(
            threat_keywords=threat_keywords,
            context=test_context,
            principles=test_principles
        )
        print(f"\nTargeted query:\n{targeted_query[:300]}...")
        
        # Execute query
        targeted_result = qa_chain.invoke({"query": targeted_query})
        print(f"\n✅ Retrieved {len(targeted_result.get('source_documents', []))} threat-specific documents")
        
        # Format and display results
        formatted_mitigations = format_mitigation_results(
            targeted_result.get('source_documents', []),
            max_results=5
        )
        print("\nFormatted mitigation practices (first 500 chars):")
        print(formatted_mitigations[:500] + "...")
        
        return True
    except Exception as e:
        print(f"❌ Error during retrieval test: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n🔍 Testing Mitigation RAG Integration\n")
    
    # Test 1: Load mitigations
    success, docs = test_mitigation_loading()
    if not success or not docs:
        print("\n❌ Tests failed at loading stage")
        return
    
    # Test 2: Setup vectorstore
    success, vectorstore = test_vectorstore_setup(docs)
    if not success or not vectorstore:
        print("\n❌ Tests failed at vectorstore setup stage")
        return
    
    # Test 3: Test retrieval
    success = test_mitigation_retrieval(vectorstore)
    if not success:
        print("\n❌ Tests failed at retrieval stage")
        return
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print("\nMitigation RAG integration is working correctly.")
    print("The system will now retrieve mitigation best practices from the JSON file")
    print("and include them in the threat analysis process.\n")


if __name__ == "__main__":
    main()
