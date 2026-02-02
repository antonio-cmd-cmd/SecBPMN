"""
Dual LLM BPMN Generator Module

This module implements a dual-LLM system for generating mitigated BPMN:
- Generator LLM: Creates the mitigated BPMN XML
- Validator LLM: Validates the generated BPMN and provides feedback
- Iterative refinement: The two LLMs interact until validation passes or max iterations reached
- Petri Net validation: After LLM iterations, validates BPMN soundness using Petri Net analysis
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple
import re
from app.llm.llm_factory import create_generator_llm, create_validator_llm, invoke_llm
from app.llm.query_builder import clean_up_bpmn_xml
from app.llm.petri_net_refinement import (
    validate_with_petri_net,
    create_petri_net_fix_prompt,
    format_petri_net_result,
    should_enable_petri_net_validation,
    get_max_petri_net_iterations,
    is_strict_mode
)
from app.config import MAX_LLM_ITERATIONS, USE_DUAL_LLM
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


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


def create_generator_prompt(
    original_bpmn_xml: str,
    threat_analysis: str,
    context: dict,
    principles: list,
    validation_feedback: str = None,
    iteration: int = 1,
    iteration_history: list = None
) -> str:
    """
    Create a prompt for the Generator LLM to generate/refine a mitigated BPMN.
    
    Args:
        original_bpmn_xml: Original BPMN XML string
        threat_analysis: The threat analysis result from LLM
        context: Context information about the process
        principles: Security principles to consider
        validation_feedback: Feedback from validator LLM (for refinement iterations)
        iteration: Current iteration number
        iteration_history: List of previous iteration results for context
        
    Returns:
        Formatted prompt for Generator LLM
    """
    context_str = f"""
- Process Goal: {context.get('processQuestion', 'N/A')}
- Technologies: {context.get('systemQuestion', 'N/A')}
- Roles: {context.get('roleQuestion', 'N/A')}
- Other notes: {context.get('otherQuestion', 'N/A')}"""

    principles_str = ", ".join(principles) if principles else "N/A"
    
    # Extract only mitigations from the complete threat analysis
    mitigations_only = extract_mitigations_only(threat_analysis)
    
    # Clean the BPMN XML to remove diagram elements before sending to LLM
    clean_bpmn_xml = clean_up_bpmn_xml(original_bpmn_xml)
    
    # Extract namespace from original BPMN to ensure consistency
    namespace_match = re.search(r'xmlns:bpmn="([^"]+)"', original_bpmn_xml)
    correct_namespace = namespace_match.group(1) if namespace_match else "http://www.omg.org/spec/BPMN/20100524/MODEL"
    
    if iteration == 1:
        # First iteration - generate new BPMN
        prompt = f"""You are a security expert specializing in insider threat mitigation. Your task: START with the existing BPMN below and add ONLY essential security controls to mitigate the identified INSIDER THREATS.

## Process Context
{context_str}

## Security Focus (Insider Threat Principles)
{principles_str}

## EXISTING BPMN TO MODIFY (Keep this structure!)
```xml
{clean_bpmn_xml}
```

## Insider Threat Mitigations (Address ONLY these specific insider threats)
The following mitigations are designed to address INSIDER THREATS identified in this business process.
These are NOT generic security threats - focus on internal actors who may abuse their authorized access.

{mitigations_only}

## YOUR TASK: Modify the Existing BPMN to Mitigate Insider Threats

### Step 1: Copy the Existing BPMN
START with the exact XML provided above. Do NOT create a new BPMN from scratch.

### Step 2: Identify 1-3 Critical Insider Threat Points
Look at the existing process and identify ONLY the most critical points where insider threats could occur.
Focus on points where authorized internal users could abuse their access, manipulate data, or bypass controls.

### Step 3: Add ONLY Essential Insider Threat Mitigations
Add ONLY realistic security controls from the INSIDER THREAT mitigation strategies above.
These controls should address internal actor risks, not external attackers.

### Step 4: Insert Security Tasks into Existing Flow
For each security task you add:
1. Find where it should go in the EXISTING flow
2. Create the new task element with ID format: Activity_[7 random chars] (e.g., Activity_9k3m2x1)
3. Update the sequenceFlow elements to include the new task
4. Give each new flow ID format: Flow_[7 random chars] (e.g., Flow_7p2n5t8)
5. If you add a lane, add flowNodeRef ONLY ONCE for each element

## CRITICAL RULES FOR VALID BPMN:

### Basic Rules:
1. **Keep 95% of original BPMN unchanged** - preserve the business logic
2. **DO NOT change original element IDs** - keep all existing IDs exactly as they are
3. **Use correct namespace**: xmlns:bpmn="{correct_namespace}"
4. **Every new element needs a "name" attribute**
5. **NO bpmndi:BPMNDiagram sections** (no visual layout)
6. **Maximum 2-4 security tasks** - don't add security everywhere

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

## Output Format:
Return ONLY the COMPLETE modified BPMN XML in ```xml``` blocks.
NO explanations. NO comments outside the XML.
Start with the existing BPMN above and add ONLY minimal essential security modifications.

Begin now:
"""
    else:
        # Refinement iteration - fix based on validator feedback
        # Build history context from previous iterations
        history_context = ""
        if iteration_history:
            history_context = "\n## 📋 PREVIOUS ATTEMPTS HISTORY (Learn from past mistakes!):\n\n"
            history_context += f"You have already tried {len(iteration_history)} time(s). Here's what happened:\n\n"
            
            for hist in iteration_history:
                if hist.get('iteration') and hist.get('status'):
                    iter_num = hist['iteration']
                    status = hist['status']
                    history_context += f"### 🔄 Iteration {iter_num}: {status.upper()}\n"
                    
                    if status == 'invalid' and hist.get('issues'):
                        history_context += f"**Validation Failed** - {len(hist['issues'])} issue(s) found:\n"
                        for idx, issue in enumerate(hist['issues'][:5], 1):  # Show max 5 issues
                            issue_text = issue[:200] + "..." if len(issue) > 200 else issue
                            history_context += f"  ❌ {idx}. {issue_text}\n"
                        if len(hist['issues']) > 5:
                            history_context += f"  ... and {len(hist['issues']) - 5} more issues\n"
                    elif status == 'syntax_error' and hist.get('error'):
                        history_context += f"**XML Syntax Error**: {hist['error']}\n"
                    elif status == 'failed' and hist.get('error'):
                        history_context += f"**Generation Failed**: {hist['error']}\n"
                    elif status == 'valid':
                        history_context += f"**Success!** ✓\n"
                    
                    history_context += "\n"
            
            history_context += "⚠️ **CRITICAL**: Don't repeat the same mistakes! Fix ALL issues mentioned above.\n\n"
        
        prompt = f"""You are a security expert specializing in insider threat mitigation, refining a mitigated BPMN based on validation feedback.

## ITERATION {iteration} - REFINEMENT REQUIRED
{history_context}
## Current Validator Feedback:
{validation_feedback}

## Original Context
{context_str}

## Security Focus (Insider Threat Principles)
{principles_str}

## Original BPMN (for reference)
```xml
{clean_bpmn_xml}
```

## YOUR TASK: Fix the Issues While Maintaining Insider Threat Mitigations

The validator has identified issues with your previous generation. You must:

1. **Address ALL issues mentioned in the validator feedback**
2. **Keep the insider threat mitigations you added (don't remove security controls)**
3. **Fix structural problems** (missing flows, incorrect gateways, etc.)
4. **Ensure BPMN is executable and valid**

### Critical Rules to Follow:

**Gateway Rules:**
- Exclusive Gateway: MUST have at least 2 outgoing flows
- Parallel Gateway: Opening and closing must have matching flow counts
- Every gateway decision must have all paths defined

**Flow Rules:**
- Every task must have incoming AND outgoing flows
- No orphan elements
- All paths must eventually reach an end event

**Lane Rules:**
- Each element can only be in ONE lane
- No duplicate flowNodeRef elements

**Namespace Rules:**
- Use correct namespace: xmlns:bpmn="{correct_namespace}"
- Remove any bpmndi, dc, or di namespaces

## Output Format:
Return ONLY the COMPLETE corrected BPMN XML in ```xml``` blocks.
NO explanations. NO comments outside the XML.
Make sure ALL validator issues are resolved.

Begin now:
"""
    
    return prompt


def create_validator_prompt(generated_bpmn_xml: str, original_bpmn_xml: str, mitigations: str) -> str:
    """
    Create a prompt for the Validator LLM to validate the generated BPMN.
    
    Args:
        generated_bpmn_xml: The BPMN XML generated by the Generator LLM
        original_bpmn_xml: The original BPMN for reference
        mitigations: The security mitigations that should be implemented
        
    Returns:
        Formatted prompt for Validator LLM
    """
    prompt = f"""You are a BPMN validation expert. Your task is to validate a security-enhanced BPMN XML.

## Generated BPMN to Validate:
```xml
{generated_bpmn_xml}
```

## Original BPMN (for comparison):
```xml
{clean_up_bpmn_xml(original_bpmn_xml)}
```

## Expected Security Mitigations:
{mitigations}

## YOUR VALIDATION TASKS:

### 1. XML Syntax Validation
- Check if XML is well-formed
- Check for proper BPMN namespace
- Check for required BPMN elements (definitions, process)

### 2. BPMN Structural Validation
Check for these critical issues:

**Gateway Validation:**
- Exclusive gateways MUST have at least 2 outgoing flows
- Parallel gateways must have matching open/close flow counts
- All gateway paths must be properly defined

**Flow Validation:**
- Every task/event must have proper incoming/outgoing flows
- No orphan elements (elements not connected to the flow)
- All paths must eventually reach an end event
- No dead ends (except end events)

**Lane Validation:**
- Each element should be in only ONE lane
- No duplicate flowNodeRef elements

**Process Flow Validation:**
- Process must have at least one start event
- Process must have at least one end event
- All elements must be reachable from start event
- No circular dependencies or deadlocks

### 3. Security Implementation Validation
- Check if security mitigations were actually implemented
- Verify that new security tasks are properly integrated
- Ensure security doesn't break the business process flow

### 4. Structural Integrity
- Original business logic should be preserved
- Original element IDs should not be changed
- New elements should follow BPMN naming conventions

## OUTPUT FORMAT:

You must respond in this EXACT format:

**VALIDATION_RESULT: [PASS or FAIL]**

**ISSUES_FOUND:**
[If PASS: write "None - BPMN is valid"
 If FAIL: List each issue clearly, one per line, with:
 - Issue type (e.g., "Gateway Error", "Flow Error", "Orphan Element")
 - Element ID if applicable
 - Clear description of the problem
 - Suggestion for how to fix it]

**SECURITY_IMPLEMENTATION:**
[Brief assessment of whether security mitigations were properly added]

**RECOMMENDATIONS:**
[If FAIL: Specific actionable recommendations to fix the issues
 If PASS: Optional suggestions for improvement]

Be precise and specific. Reference element IDs when identifying issues.

Begin validation now:
"""
    
    return prompt


def extract_xml_from_response(response: str) -> str:
    """
    Extract XML content from LLM response.
    
    Args:
        response: Raw response from LLM
        
    Returns:
        Extracted XML string
        
    Raises:
        ValueError: If no valid XML found
    """
    # Try to find XML in code blocks
    xml_pattern = r"```xml\s*(.*?)\s*```"
    matches = re.findall(xml_pattern, response, re.DOTALL)
    
    if matches:
        return matches[0].strip()
    
    # Try to find XML without code blocks
    xml_pattern = r"(<\?xml.*?</bpmn:definitions>)"
    matches = re.findall(xml_pattern, response, re.DOTALL)
    
    if matches:
        return matches[0].strip()
    
    # If no patterns match, assume the entire response is XML
    if response.strip().startswith("<?xml") or response.strip().startswith("<bpmn"):
        return response.strip()
    
    raise ValueError("No valid XML found in LLM response")


def parse_validation_result(validation_response: str) -> Tuple[bool, str, List[str]]:
    """
    Parse the validation result from the Validator LLM response.
    
    Args:
        validation_response: Raw response from Validator LLM
        
    Returns:
        Tuple of (is_valid, feedback_text, issues_list)
    """
    print("\n" + "="*60)
    print("DEBUG: PARSING VALIDATOR RESPONSE")
    print("="*60)
    
    # Extract validation result
    result_match = re.search(r'\*\*VALIDATION_RESULT:\s*(PASS|FAIL)\*\*', validation_response, re.IGNORECASE)
    is_valid = result_match and result_match.group(1).upper() == "PASS" if result_match else False
    
    print(f"Validation Result Match: {result_match.group(0) if result_match else 'NOT FOUND'}")
    print(f"Is Valid: {is_valid}")
    
    # Extract issues section
    issues_match = re.search(r'\*\*ISSUES_FOUND:\*\*\s*(.*?)\s*\*\*', validation_response, re.DOTALL)
    issues_text = issues_match.group(1).strip() if issues_match else ""
    
    print(f"\nIssues Section Match: {'FOUND' if issues_match else 'NOT FOUND'}")
    if issues_match:
        print(f"Issues Text Length: {len(issues_text)}")
        print(f"Issues Text Preview:\n{issues_text[:500]}")
    
    # Parse individual issues
    issues_list = []
    if issues_text and "None" not in issues_text:
        # Split by lines and filter out empty lines
        print("\nParsing individual issues:")
        for idx, line in enumerate(issues_text.split('\n')):
            line = line.strip()
            print(f"  Line {idx}: '{line[:100]}...' (starts with '-': {line.startswith('-')})")
            if line and line.startswith('-'):
                issue = line[1:].strip()
                issues_list.append(issue)
                print(f"    ✓ Added issue: '{issue[:100]}...'")
    
    print(f"\nTotal Issues Parsed: {len(issues_list)}")
    print("="*60 + "\n")
    
    return is_valid, validation_response, issues_list


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


def validate_xml_syntax(xml_content: str) -> Dict[str, any]:
    """
    Validate XML syntax and basic BPMN structure.
    
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
        
        # Try to find processes
        processes = root.findall('.//{*}process')
        
        if not processes:
            return {
                'valid': False,
                'message': 'Invalid BPMN XML: no process found'
            }
        
        return {
            'valid': True,
            'message': 'XML syntax is valid',
            'process_count': len(processes)
        }
        
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


def generate_mitigated_bpmn_dual_llm(
    original_bpmn_xml: str,
    threat_analysis: str,
    context: dict,
    principles: list
) -> Dict[str, any]:
    """
    Generate a mitigated BPMN using a dual-LLM system (Generator + Validator).
    
    Args:
        original_bpmn_xml: Original BPMN XML
        threat_analysis: Threat analysis from LLM
        context: Process context
        principles: Security principles
        
    Returns:
        Dictionary with generation results including iteration history
    """
    try:
        print("=== STARTING DUAL-LLM MITIGATED BPMN GENERATION ===")
        print(f"Max iterations configured: {MAX_LLM_ITERATIONS}")
        
        # Create LLM instances
        generator_llm = create_generator_llm()
        validator_llm = create_validator_llm()
        
        # Extract mitigations for validator
        mitigations_text = extract_mitigations_only(threat_analysis)
        
        # Variables for iteration loop
        current_bpmn = None
        validation_feedback = None
        iteration_history = []
        
        # Iterative refinement loop
        for iteration in range(1, MAX_LLM_ITERATIONS + 1):
            print(f"\n=== ITERATION {iteration}/{MAX_LLM_ITERATIONS} ===")
            
            # Step 1: Generate/Refine BPMN with Generator LLM
            print(f"[Iteration {iteration}] Generator LLM: Creating BPMN...")
            
            # DEBUG: Log iteration history being passed
            if iteration > 1 and iteration_history:
                print(f"[Iteration {iteration}] 🧠 Providing context from {len(iteration_history)} previous iteration(s)")
                print(f"[Iteration {iteration}] Context includes:")
                for hist in iteration_history:
                    status_emoji = "✓" if hist.get('status') == 'valid' else "✗"
                    print(f"   {status_emoji} Iteration {hist.get('iteration')}: {hist.get('status')} ({hist.get('issues_count', 0)} issues)")
            
            generator_prompt = create_generator_prompt(
                original_bpmn_xml,
                threat_analysis,
                context,
                principles,
                validation_feedback,
                iteration,
                iteration_history  # Pass the history for context
            )
            
            # DEBUG: Log if history was included in prompt
            if iteration > 1 and iteration_history:
                if "PREVIOUS ATTEMPTS HISTORY" in generator_prompt:
                    print(f"[Iteration {iteration}] ✓ History successfully injected into Generator prompt")
                else:
                    print(f"[Iteration {iteration}] ⚠️ WARNING: History NOT found in Generator prompt!")
            
            generator_response = invoke_llm(generator_llm, generator_prompt)
            print(f"[Iteration {iteration}] Generator response length: {len(generator_response)}")
            
            # DEBUG: Log generator response preview
            print(f"\n{'='*60}")
            print(f"DEBUG: GENERATOR RESPONSE PREVIEW (Iteration {iteration})")
            print(f"{'='*60}")
            print(f"First 500 chars:\n{generator_response[:500]}")
            print(f"\nLast 500 chars:\n{generator_response[-500:]}")
            print(f"{'='*60}\n")
            
            # Extract XML from generator response
            try:
                print(f"[Iteration {iteration}] Extracting XML from LLM response...")
                current_bpmn = extract_xml_from_response(generator_response)
                print(f"[Iteration {iteration}] XML extracted, length: {len(current_bpmn)}")
                
                # DEBUG: More detailed XML preview
                print(f"\n{'='*60}")
                print(f"DEBUG: EXTRACTED BPMN XML (Iteration {iteration})")
                print(f"{'='*60}")
                print(f"First 800 chars:\n{current_bpmn[:800]}")
                print(f"\n[... middle content omitted ...]\n")
                print(f"Last 800 chars:\n{current_bpmn[-800:]}")
                print(f"{'='*60}\n")
                
                # DEBUG: Save to temporary file for inspection
                try:
                    import os
                    debug_dir = "debug_output"
                    os.makedirs(debug_dir, exist_ok=True)
                    debug_file = f"{debug_dir}/iteration_{iteration}_generated_bpmn.xml"
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(current_bpmn)
                    print(f"[Iteration {iteration}] ✓ Saved generated BPMN to: {debug_file}")
                except Exception as e:
                    print(f"[Iteration {iteration}] ⚠ Could not save debug file: {e}")
                
                # Fix namespace
                current_bpmn = fix_bpmn_namespace(current_bpmn)
                print(f"[Iteration {iteration}] Namespace fixed")
            except ValueError as e:
                error_msg = f"Failed to extract XML from generator response: {str(e)}"
                print(f"[Iteration {iteration}] ERROR: {error_msg}")
                iteration_history.append({
                    'iteration': iteration,
                    'phase': 'generation',
                    'status': 'failed',
                    'error': error_msg
                })
                
                # If we have a previous valid BPMN, return it
                if iteration > 1 and len(iteration_history) > 0:
                    for prev_iter in reversed(iteration_history):
                        if prev_iter.get('generated_bpmn'):
                            print(f"Returning BPMN from iteration {prev_iter['iteration']}")
                            return {
                                'success': True,
                                'message': f'Generation failed at iteration {iteration}, returning best result from iteration {prev_iter["iteration"]}',
                                'mitigated_bpmn': prev_iter['generated_bpmn'],
                                'iterations': iteration_history,
                                'final_iteration': prev_iter['iteration']
                            }
                
                return {
                    'success': False,
                    'message': error_msg,
                    'iterations': iteration_history
                }
            
            # Quick XML syntax validation
            syntax_check = validate_xml_syntax(current_bpmn)
            if not syntax_check['valid']:
                print(f"[Iteration {iteration}] XML syntax error: {syntax_check['message']}")
                iteration_history.append({
                    'iteration': iteration,
                    'phase': 'generation',
                    'status': 'syntax_error',
                    'error': syntax_check['message']
                })
                
                validation_feedback = f"XML Syntax Error: {syntax_check['message']}\nPlease generate valid XML."
                continue
            
            # Step 2: Validate with Validator LLM
            print(f"[Iteration {iteration}] Validator LLM: Validating BPMN...")
            validator_prompt = create_validator_prompt(
                current_bpmn,
                original_bpmn_xml,
                mitigations_text
            )
            
            validator_response = invoke_llm(validator_llm, validator_prompt)
            print(f"[Iteration {iteration}] Validator response length: {len(validator_response)}")
            
            # DEBUG: Log full validator response
            print(f"\n{'='*60}")
            print(f"DEBUG: FULL VALIDATOR RESPONSE (Iteration {iteration})")
            print(f"{'='*60}")
            print(validator_response)
            print(f"{'='*60}\n")
            
            # Parse validation result
            is_valid, feedback_text, issues_list = parse_validation_result(validator_response)
            
            print(f"[Iteration {iteration}] Validation result: {'PASS' if is_valid else 'FAIL'}")
            if issues_list:
                print(f"[Iteration {iteration}] Issues found: {len(issues_list)}")
                for idx, issue in enumerate(issues_list, 1):
                    print(f"  {idx}. {issue}")
            else:
                print(f"[Iteration {iteration}] ⚠ No issues parsed from validator response!")
                if not is_valid:
                    print(f"[Iteration {iteration}] ⚠ WARNING: Validation FAILED but no issues were extracted!")
                    print(f"[Iteration {iteration}] This suggests a problem with validator response format.")
            
            # DEBUG: Save validation feedback to file
            try:
                import os
                debug_dir = "debug_output"
                os.makedirs(debug_dir, exist_ok=True)
                debug_file = f"{debug_dir}/iteration_{iteration}_validation_feedback.txt"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(f"Validation Result: {'PASS' if is_valid else 'FAIL'}\n")
                    f.write(f"Issues Count: {len(issues_list)}\n")
                    f.write(f"\n{'='*60}\n")
                    f.write(f"FULL VALIDATOR RESPONSE:\n")
                    f.write(f"{'='*60}\n")
                    f.write(feedback_text)
                print(f"[Iteration {iteration}] ✓ Saved validation feedback to: {debug_file}")
            except Exception as e:
                print(f"[Iteration {iteration}] ⚠ Could not save validation feedback: {e}")
            
            # Store iteration results
            iteration_history.append({
                'iteration': iteration,
                'phase': 'complete',
                'status': 'valid' if is_valid else 'invalid',
                'generated_bpmn': current_bpmn,
                'validation_feedback': feedback_text,
                'issues_count': len(issues_list),
                'issues': issues_list
            })
            
            # DEBUG: Log iteration history summary
            print(f"\n{'='*60}")
            print(f"ITERATION {iteration} SUMMARY")
            print(f"{'='*60}")
            print(f"Status: {'✓ VALID' if is_valid else '✗ INVALID'}")
            print(f"Issues found: {len(issues_list)}")
            print(f"Total iterations in history: {len(iteration_history)}")
            if iteration > 1:
                print(f"Learning from {iteration - 1} previous attempt(s)")
            print(f"{'='*60}\n")
            
            # Check if validation passed
            if is_valid:
                print(f"[Iteration {iteration}] ✓ Validation PASSED - BPMN is valid!")
                break  # Exit iteration loop, proceed to Petri Net validation
            else:
                print(f"[Iteration {iteration}] ✗ Validation FAILED - Preparing feedback for next iteration")
                validation_feedback = feedback_text
        
        # ======================================================================
        # PHASE 2: PETRI NET VALIDATION (After LLM iterations complete)
        # ======================================================================
        
        print(f"\n{'='*80}")
        print("PHASE 2: PETRI NET VALIDATION")
        print(f"{'='*80}")
        
        final_bpmn = current_bpmn
        petri_net_iterations = 0
        max_petri_iterations = get_max_petri_net_iterations()
        
        if should_enable_petri_net_validation():
            logger.info("🔍 Petri Net validation is ENABLED")
            print(f"[Petri Net] Validating BPMN soundness...")
            
            # Initial Petri Net validation
            petri_result = validate_with_petri_net(final_bpmn)
            print(format_petri_net_result(petri_result, 0))
            
            # If not sound, try to fix with additional iterations
            while not petri_result['valid'] and petri_net_iterations < max_petri_iterations:
                petri_net_iterations += 1
                print(f"\n[Petri Net Refinement] Iteration {petri_net_iterations}/{max_petri_iterations}")
                print(f"Asking Generator LLM to fix structural issues...")
                
                # Create fix prompt
                fix_prompt = create_petri_net_fix_prompt(
                    final_bpmn,
                    petri_result,
                    petri_net_iterations
                )
                
                # Get fixed BPMN from Generator LLM
                fix_response = invoke_llm(generator_llm, fix_prompt)
                fixed_bpmn = extract_xml_from_response(fix_response)
                
                if not fixed_bpmn:
                    print(f"[Petri Net Iteration {petri_net_iterations}] ❌ Failed to extract XML")
                    break
                
                # Save debug output
                try:
                    import os
                    debug_dir = "debug_output"
                    os.makedirs(debug_dir, exist_ok=True)
                    debug_file = f"{debug_dir}/petri_iteration_{petri_net_iterations}_bpmn.xml"
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(fixed_bpmn)
                    print(f"[Petri Net Iteration {petri_net_iterations}] ✓ Saved fixed BPMN to: {debug_file}")
                except Exception as e:
                    print(f"[Petri Net Iteration {petri_net_iterations}] ⚠ Could not save BPMN: {e}")
                
                # Validate fixed BPMN
                final_bpmn = fixed_bpmn
                petri_result = validate_with_petri_net(final_bpmn)
                print(format_petri_net_result(petri_result, petri_net_iterations))
                
                if petri_result['valid']:
                    print(f"[Petri Net] ✅ BPMN is now SOUND after {petri_net_iterations} iteration(s)!")
                    break
            
            # Final Petri Net validation result
            if petri_result['valid']:
                logger.info("✅ Petri Net validation PASSED - BPMN is SOUND")
            else:
                logger.warning(f"❌ Petri Net validation FAILED after {petri_net_iterations} attempts")
                
                if is_strict_mode():
                    # Strict mode: reject BPMN if not sound
                    logger.error("🚫 STRICT MODE: Rejecting BPMN due to soundness issues")
                    return {
                        'success': False,
                        'message': 'BPMN failed Petri Net soundness validation (Strict Mode enabled)',
                        'error': petri_result.get('message', 'Unknown soundness error'),
                        'error_type': petri_result.get('error_type', 'soundness_error'),
                        'iterations': iteration_history,
                        'petri_net_iterations': petri_net_iterations,
                        'final_iteration': iteration
                    }
                else:
                    # Warning mode: return BPMN with warning
                    logger.warning("⚠️ WARNING MODE: Returning BPMN with soundness warning")
                    print(f"\n⚠️ WARNING: BPMN has structural issues but will be returned (Warning Mode)")
        else:
            logger.info("ℹ️ Petri Net validation is DISABLED")
            print("[Petri Net] Validation is disabled in configuration")
            petri_result = {'valid': None, 'message': 'Petri Net validation disabled'}
        
        # ======================================================================
        # FINAL RESULT
        # ======================================================================
        
        print(f"\n{'='*80}")
        print("FINAL RESULT")
        print(f"{'='*80}")
        print(f"LLM Iterations: {iteration}/{MAX_LLM_ITERATIONS}")
        print(f"Petri Net Iterations: {petri_net_iterations}/{max_petri_iterations}")
        print(f"LLM Validation: {'✓ PASS' if is_valid else '✗ FAIL'}")
        
        if should_enable_petri_net_validation():
            if petri_result['valid']:
                print(f"Petri Net Validation: ✓ PASS (SOUND)")
            elif petri_result['valid'] is None:
                print(f"Petri Net Validation: - SKIPPED")
            else:
                print(f"Petri Net Validation: ✗ FAIL (NOT SOUND)")
                if is_strict_mode():
                    print(f"Mode: 🚫 STRICT (Rejected)")
                else:
                    print(f"Mode: ⚠️ WARNING (Accepted with warning)")
        print(f"{'='*80}\n")
        
        # Add metadata
        from datetime import datetime
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'principles': principles,
            'llm_iterations': iteration,
            'petri_net_iterations': petri_net_iterations,
            'petri_net_enabled': should_enable_petri_net_validation(),
            'petri_net_valid': petri_result.get('valid'),
            'petri_net_strict_mode': is_strict_mode(),
            'dual_llm': True
        }
        
        # Prepare warnings if any
        warnings = []
        if not is_valid:
            warnings.append('BPMN has LLM validation issues')
        if should_enable_petri_net_validation() and not petri_result.get('valid'):
            warnings.append(f"BPMN is not sound: {petri_result.get('message', 'Unknown error')}")
        
        return {
            'success': True,
            'message': f'Mitigated BPMN generated successfully (LLM: {iteration} iterations, Petri Net: {petri_net_iterations} iterations)',
            'mitigated_bpmn': final_bpmn,
            'iterations': iteration_history,
            'final_iteration': iteration,
            'petri_net_result': petri_result,
            'petri_net_iterations': petri_net_iterations,
            'metadata': metadata,
            'warnings': warnings if warnings else None
        }
        
        
    except Exception as e:
        print(f"=== ERROR IN DUAL-LLM GENERATION ===")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'message': f'Error in dual-LLM generation: {str(e)}',
            'iterations': iteration_history if 'iteration_history' in locals() else []
        }
