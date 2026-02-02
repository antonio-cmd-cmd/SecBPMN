"""
BPMN Mitigation Generator Module

This module generates a mitigated BPMN XML by applying security mitigations
identified during threat modeling using an LLM.
"""

import xml.etree.ElementTree as ET
from typing import Dict, List
import re
from app.llm.query_builder import clean_up_bpmn_xml


def extract_mitigations_only(threat_analysis: str) -> str:
    """
    Extract only the mitigation strategies from the complete threat analysis.
    This reduces the prompt size and focuses the LLM on what to implement.
    
    Args:
        threat_analysis: Complete threat analysis markdown from LLM
        
    Returns:
        Formatted string containing only mitigations organized by element
    """
    lines = threat_analysis.split('\n')
    mitigations = []
    current_element = None
    current_element_id = None
    in_mitigation_section = False
    mitigation_bullets = []
    
    for line in lines:
        # Check if it's an element heading (## Element Name)
        if line.startswith('## ') and not line.startswith('###'):
            # Save previous element's mitigations if any
            if current_element and mitigation_bullets:
                mitigations.append(f"## {current_element}")
                if current_element_id:
                    mitigations.append(f"- **BPMN Element ID**: {current_element_id}")
                mitigations.append("- **Mitigation Strategies**:")
                mitigations.extend(mitigation_bullets)
                mitigations.append("")  # Empty line for readability
            
            # Start new element
            current_element = line[3:].strip()
            current_element_id = None
            in_mitigation_section = False
            mitigation_bullets = []
        
        # Check for BPMN Element ID
        elif '**BPMN Element ID**:' in line:
            # Extract the ID
            current_element_id = line.split('**BPMN Element ID**:')[1].strip()
        
        # Check if we're entering the mitigation section
        elif '**Mitigation Strategies**:' in line:
            in_mitigation_section = True
        
        # Check if we're leaving the mitigation section (new field starts)
        elif in_mitigation_section and line.strip().startswith('- **') and 'Mitigation' not in line:
            in_mitigation_section = False
        
        # Collect mitigation bullets
        elif in_mitigation_section and line.strip().startswith('-') and '**Mitigation' not in line:
            # This is a mitigation bullet point
            mitigation_bullets.append(line)
    
    # Don't forget the last element
    if current_element and mitigation_bullets:
        mitigations.append(f"## {current_element}")
        if current_element_id:
            mitigations.append(f"- **BPMN Element ID**: {current_element_id}")
        mitigations.append("- **Mitigation Strategies**:")
        mitigations.extend(mitigation_bullets)
    
    return '\n'.join(mitigations)


def create_mitigation_prompt(original_bpmn_xml: str, threat_analysis: str, context: dict, principles: list) -> str:
    """
    Create a prompt for the LLM to generate a mitigated BPMN.
    
    Args:
        original_bpmn_xml: Original BPMN XML string
        threat_analysis: The threat analysis result from LLM
        context: Context information about the process
        principles: Security principles to consider
        
    Returns:
        Formatted prompt for LLM
    """
    
    context_str = f"""
- Process Goal: {context.get('processQuestion', 'N/A')}
- Technologies: {context.get('systemQuestion', 'N/A')}
- Roles: {context.get('roleQuestion', 'N/A')}
- Other notes: {context.get('otherQuestion', 'N/A')}"""

    principles_str = ", ".join(principles) if principles else "N/A"
    
    # Extract only mitigations from the complete threat analysis
    print("Extracting mitigations from threat analysis...")
    mitigations_only = extract_mitigations_only(threat_analysis)
    print(f"Original threat analysis length: {len(threat_analysis)}, Mitigations only length: {len(mitigations_only)}")
    
    # Clean the BPMN XML to remove diagram elements before sending to LLM
    print("Cleaning BPMN XML (removing diagram elements)...")
    clean_bpmn_xml = clean_up_bpmn_xml(original_bpmn_xml)
    print(f"Original BPMN length: {len(original_bpmn_xml)}, Clean BPMN length: {len(clean_bpmn_xml)}")
    
    # Extract namespace from original BPMN to ensure consistency
    namespace_match = re.search(r'xmlns:bpmn="([^"]+)"', original_bpmn_xml)
    correct_namespace = namespace_match.group(1) if namespace_match else "http://www.omg.org/spec/BPMN/20100524/MODEL"
    
    prompt = f"""You are a security expert. Your task: START with the existing BPMN below and add ONLY essential security controls.

## Process Context
{context_str}

## Security Focus
{principles_str}

## EXISTING BPMN TO MODIFY (Keep this structure!)
```xml
{clean_bpmn_xml}
```

## Security Mitigations (Add only the most critical ones)
{mitigations_only}

## YOUR TASK: Modify the Existing BPMN with security controls

### Step 1: Copy the Existing BPMN
START with the exact XML provided above. Do NOT create a new BPMN from scratch.

### Step 2: Identify Critical Security Points
Look at the existing process and identify ONLY the most critical mitigation from {mitigations_only}

### Step 3: Add ONLY Essential Security Tasks
Add ONLY from realistic security controls

### Step 4: Insert Security Tasks into Existing Flow
For each security task you add:
1. Find where it should go in the EXISTING flow
2. Create the new task element with ID format: Activity_[7 random chars] (e.g., Activity_9k3m2x1)
3. Update the sequenceFlow elements to include the new task
4. Give each new flow ID format: Flow_[7 random chars] (e.g., Flow_7p2n5t8)
5. If you add a lane, add flowNodeRef ONLY ONCE for each element

## CRITICAL RULES FOR VALID BPMN:

### Basic Rules:
2. **DO NOT change original element IDs** - keep all existing IDs exactly as they are
3. **Use correct namespace**: xmlns:bpmn="{correct_namespace}"
4. **Every new element needs a "name" attribute**
5. **NO bpmndi:BPMNDiagram sections** (no visual layout)
6. don't add security everywhere

### Structural Rules (MUST FOLLOW for executable BPMN):

**1. Lane Rules:**
- Each task/event can be in ONLY ONE lane
- Never duplicate flowNodeRef in multiple lanes
- If you add a security task, put it in the appropriate lane (one lane only)

**2. Gateway Rules (CRITICAL - Most Common Error):**
- **Exclusive Gateway** (XOR): MUST have at least 2 outgoing flows
  - Example: "Access Granted?" → YES flow + NO flow
  - If you add a security check gateway, ALWAYS add both paths
  - The NO path should go to an end event or error handler
- **Parallel Gateway**: Use ONLY if you have real parallel work
  - Opening: Must have multiple outgoing flows
  - Closing (Join): Must have same number of incoming flows
  - Don't use parallel gateways for simple sequential security checks

**3. Flow Rules:**
- Every task MUST have at least one incoming and one outgoing flow
- No "orphan" tasks without connections
- If you add a security task, connect it properly: incoming flow → security task → outgoing flow

**4. Process Execution Rules:**
- Process must have ONE clear start event
- Process must have at least ONE end event
- Every element must be reachable from start
- No deadlocks: every path must lead to an end event

### Example of CORRECT Security Gateway:

```xml
<!-- CORRECT: Exclusive gateway with BOTH paths -->
<bpmn:exclusiveGateway id="Gateway_Security" name="Access Granted?"/>
<bpmn:sequenceFlow id="Flow_yes" sourceRef="Gateway_Security" targetRef="Task_Next" name="Yes"/>
<bpmn:sequenceFlow id="Flow_no" sourceRef="Gateway_Security" targetRef="Event_AccessDenied" name="No"/>
<bpmn:endEvent id="Event_AccessDenied" name="Access Denied"/>
```

## What NOT to Do:
✗ Don't create a new BPMN from scratch
✗ Don't add gateway with only ONE outgoing flow
✗ Don't duplicate task references in multiple lanes
✗ Don't create orphan tasks without connections
✗ Don't add parallel gateways unless you have real parallel work
✗ Don't create deadlocks (paths that don't reach an end event)
✗ Don't add unrealistic security measures
✗ Don't modify or remove existing tasks

## Output Format:
Return the COMPLETE modified BPMN XML in ```xml``` blocks.
NO explanations. NO comments outside the XML.
Start with the existing BPMN and add ONLY minimal essential security modifications.

Begin now - copy the existing BPMN above and modify it:
"""
    
    return prompt


def extract_xml_from_llm_response(llm_response: str) -> str:
    """
    Extract XML content from LLM response.
    
    Args:
        llm_response: Raw response from LLM
        
    Returns:
        Extracted XML string
        
    Raises:
        ValueError: If no valid XML found
    """
    # Try to find XML in code blocks
    xml_pattern = r"```xml\s*(.*?)\s*```"
    matches = re.findall(xml_pattern, llm_response, re.DOTALL)
    
    if matches:
        return matches[0].strip()
    
    # Try to find XML without code blocks
    xml_pattern = r"(<\?xml.*?</bpmn:definitions>)"
    matches = re.findall(xml_pattern, llm_response, re.DOTALL)
    
    if matches:
        return matches[0].strip()
    
    # If no patterns match, assume the entire response is XML
    if llm_response.strip().startswith("<?xml") or llm_response.strip().startswith("<bpmn"):
        return llm_response.strip()
    
    raise ValueError("No valid XML found in LLM response")


def fix_bpmn_namespace(xml_content: str, correct_namespace: str = "http://www.omg.org/spec/BPMN/20100524/MODEL") -> str:
    """
    Fix BPMN namespace if it's incorrect.
    
    Args:
        xml_content: BPMN XML string
        correct_namespace: The correct BPMN namespace
        
    Returns:
        XML with corrected namespace
    """
    # Check if namespace is wrong
    wrong_patterns = [
        r'xmlns:bpmn="http://www\.omg\.org/spec/BPMN"',
        r'xmlns:bpmn="http://www\.omg\.org/spec/BPMN/"',
    ]
    
    for pattern in wrong_patterns:
        if re.search(pattern, xml_content):
            xml_content = re.sub(pattern, f'xmlns:bpmn="{correct_namespace}"', xml_content)
            print(f"Fixed incorrect BPMN namespace")
            break
    
    # Remove bpmndi namespace if present (since we don't include diagrams)
    xml_content = re.sub(r'\s*xmlns:bpmndi="[^"]*"', '', xml_content)
    xml_content = re.sub(r'\s*xmlns:dc="[^"]*"', '', xml_content)
    xml_content = re.sub(r'\s*xmlns:di="[^"]*"', '', xml_content)
    
    return xml_content


def validate_mitigated_bpmn(xml_content: str) -> Dict[str, any]:
    """
    Validate the generated mitigated BPMN XML with structural checks.
    
    Args:
        xml_content: BPMN XML string
        
    Returns:
        Dictionary with validation results
    """
    try:
        # Parse XML to ensure it's valid
        root = ET.fromstring(xml_content)
        
        # Check for required BPMN namespace
        if 'definitions' not in root.tag:
            return {
                'valid': False,
                'message': 'Invalid BPMN XML: missing definitions element'
            }
        
        # Try to find processes with different namespace strategies
        processes = []
        
        # Strategy 1: Try with standard BPMN 2.0 namespace
        namespaces = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}
        processes = root.findall('.//bpmn:process', namespaces)
        
        # Strategy 2: Try with any bpmn namespace (extract from XML)
        if not processes:
            ns_match = re.search(r'xmlns:bpmn="([^"]+)"', xml_content)
            if ns_match:
                actual_namespace = ns_match.group(1)
                namespaces = {'bpmn': actual_namespace}
                processes = root.findall('.//bpmn:process', namespaces)
        
        # Strategy 3: Try without namespace prefix
        if not processes:
            processes = root.findall('.//process')
        
        # Strategy 4: Try with default namespace
        if not processes:
            for child in root:
                if 'process' in child.tag:
                    processes.append(child)
        
        if not processes:
            return {
                'valid': False,
                'message': f'Invalid BPMN XML: no process found. Root tag: {root.tag}'
            }
        
        # Structural validation
        warnings = []
        
        # Check for duplicate flowNodeRef in lanes
        lane_refs = {}
        for lane in root.findall('.//{*}lane'):
            lane_id = lane.get('id', 'unknown')
            for ref in lane.findall('.//{*}flowNodeRef'):
                node_id = ref.text
                if node_id in lane_refs:
                    warnings.append(f"Duplicate flowNodeRef '{node_id}' in lanes: {lane_refs[node_id]} and {lane_id}")
                else:
                    lane_refs[node_id] = lane_id
        
        # Check for exclusive gateways with only one outgoing flow
        for gateway in root.findall('.//{*}exclusiveGateway'):
            gw_id = gateway.get('id', 'unknown')
            outgoing_flows = [flow for flow in root.findall('.//{*}sequenceFlow') if flow.get('sourceRef') == gw_id]
            if len(outgoing_flows) < 2:
                warnings.append(f"Exclusive gateway '{gw_id}' has only {len(outgoing_flows)} outgoing flow(s) - should have at least 2")
        
        # Check for orphan tasks (tasks without incoming or outgoing flows)
        all_tasks = root.findall('.//{*}task')
        for task in all_tasks:
            task_id = task.get('id', 'unknown')
            incoming = [f for f in root.findall('.//{*}sequenceFlow') if f.get('targetRef') == task_id]
            outgoing = [f for f in root.findall('.//{*}sequenceFlow') if f.get('sourceRef') == task_id]
            if not incoming:
                warnings.append(f"Task '{task_id}' has no incoming flows (orphan)")
            if not outgoing:
                warnings.append(f"Task '{task_id}' has no outgoing flows (dead end)")
        
        # Count all elements in the process
        element_count = 0
        for process in processes:
            element_count += len(list(process.iter()))
        
        result = {
            'valid': True,
            'message': 'Mitigated BPMN is valid' if not warnings else 'Mitigated BPMN has structural warnings',
            'element_count': element_count,
            'process_count': len(processes)
        }
        
        if warnings:
            result['warnings'] = warnings
            print("⚠️ BPMN Structural Warnings:")
            for w in warnings:
                print(f"  - {w}")
        
        return result
        
    except ET.ParseError as e:
        return {
            'valid': False,
            'message': f'XML parsing error: {str(e)}'
        }
    except Exception as e:
        return {
            'valid': False,
            'message': f'Validation error: {str(e)}'
        }


def add_mitigation_metadata(xml_content: str, metadata: Dict) -> str:
    """
    Add metadata about mitigations to the BPMN XML.
    
    Args:
        xml_content: BPMN XML string
        metadata: Dictionary with mitigation metadata
        
    Returns:
        Modified XML with metadata
    """
    try:
        root = ET.fromstring(xml_content)
        
        # Find or create documentation element
        namespaces = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}
        process = root.find('.//bpmn:process', namespaces)
        
        if process is not None:
            # Create documentation element
            doc_text = f"""
Security Mitigations Applied:
- Generated on: {metadata.get('timestamp', 'N/A')}
- Principles: {', '.join(metadata.get('principles', []))}
- Mitigations: {metadata.get('mitigation_count', 0)} security controls added
"""
            
            # Add as comment (safer than modifying structure)
            comment = ET.Comment(doc_text)
            process.insert(0, comment)
        
        return ET.tostring(root, encoding='unicode')
        
    except Exception as e:
        # If metadata addition fails, return original XML
        print(f"Warning: Could not add metadata: {e}")
        return xml_content


def generate_mitigated_bpmn(
    original_bpmn_xml: str,
    threat_analysis: str,
    context: dict,
    principles: list,
    qa_chain
) -> Dict[str, any]:
    """
    Generate a mitigated BPMN using LLM.
    
    Args:
        original_bpmn_xml: Original BPMN XML
        threat_analysis: Threat analysis from LLM
        context: Process context
        principles: Security principles
        qa_chain: LangChain QA chain for LLM
        
    Returns:
        Dictionary with generation results
    """
    try:
        print("=== STARTING MITIGATED BPMN GENERATION ===")
        # Create prompt
        prompt = create_mitigation_prompt(
            original_bpmn_xml,
            threat_analysis,
            context,
            principles
        )
        
        print(f"Prompt created, length: {len(prompt)}")
        
        # Query LLM
        print("Generating mitigated BPMN with LLM...")
        result = qa_chain.invoke({"query": prompt})
        llm_response = result.get('result', '')
        
        print(f"LLM response received, length: {len(llm_response)}")
        print("=== LLM RESPONSE PREVIEW (first 1000 chars) ===")
        print(llm_response[:1000])
        print("=== LLM RESPONSE PREVIEW (last 1000 chars) ===")
        print(llm_response[-1000:])
        
        if not llm_response:
            return {
                'success': False,
                'message': 'LLM returned empty response'
            }
        
        # Extract XML from response
        try:
            print("Extracting XML from LLM response...")
            mitigated_xml = extract_xml_from_llm_response(llm_response)
            print(f"XML extracted, length: {len(mitigated_xml)}")
            print("=== EXTRACTED XML PREVIEW (first 500 chars) ===")
            print(mitigated_xml[:500])
            print("=== EXTRACTED XML PREVIEW (last 500 chars) ===")
            print(mitigated_xml[-500:])
            
            # Fix namespace if needed
            print("Fixing BPMN namespace if needed...")
            mitigated_xml = fix_bpmn_namespace(mitigated_xml)
            
        except ValueError as e:
            print(f"Failed to extract XML: {e}")
            return {
                'success': False,
                'message': str(e),
                'raw_response': llm_response[:500]  # First 500 chars for debugging
            }
        
        # Validate the generated BPMN
        print("Validating generated BPMN...")
        validation = validate_mitigated_bpmn(mitigated_xml)
        print(f"Validation result: {validation}")
        
        if not validation['valid']:
            return {
                'success': False,
                'message': f"Generated BPMN is invalid: {validation['message']}",
                'raw_xml': mitigated_xml[:500]
            }
        
        # Add metadata
        from datetime import datetime
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'principles': principles,
            'mitigation_count': validation.get('element_count', 0)
        }
        
        final_xml = add_mitigation_metadata(mitigated_xml, metadata)
        
        print("=== MITIGATED BPMN GENERATION COMPLETED SUCCESSFULLY ===")
        
        return {
            'success': True,
            'message': 'Mitigated BPMN generated successfully',
            'mitigated_bpmn': final_xml,
            'element_count': validation.get('element_count', 0)
        }
        
    except Exception as e:
        print(f"=== ERROR IN MITIGATED BPMN GENERATION ===")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'message': f'Error generating mitigated BPMN: {str(e)}'
        }
