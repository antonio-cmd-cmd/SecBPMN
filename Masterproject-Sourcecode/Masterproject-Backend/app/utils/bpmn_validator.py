"""
BPMN Validator Module

This module validates BPMN models by converting them to Petri nets
and checking for structural correctness (soundness).
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple
import pm4py
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.petri_net.utils import petri_utils


class BPMNValidationError(Exception):
    """Custom exception for BPMN validation errors"""
    pass


def parse_bpmn_xml(xml_content: str) -> ET.Element:
    """
    Parse BPMN XML content and return the root element.
    
    Args:
        xml_content: BPMN XML as string
        
    Returns:
        XML root element
        
    Raises:
        BPMNValidationError: If XML parsing fails
    """
    try:
        root = ET.fromstring(xml_content)
        return root
    except ET.ParseError as e:
        raise BPMNValidationError(f"Invalid XML format: {str(e)}")


def extract_bpmn_elements(root: ET.Element) -> Dict[str, List]:
    """
    Extract BPMN elements (tasks, gateways, events, flows) from XML.
    
    Args:
        root: BPMN XML root element
        
    Returns:
        Dictionary with categorized BPMN elements
    """
    # Define BPMN 2.0 namespace
    namespaces = {
        'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
        'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI'
    }
    
    elements = {
        'start_events': [],
        'end_events': [],
        'tasks': [],
        'gateways': [],
        'flows': []
    }
    
    # Find all process elements
    for process in root.findall('.//bpmn:process', namespaces):
        elements['start_events'].extend(process.findall('.//bpmn:startEvent', namespaces))
        elements['end_events'].extend(process.findall('.//bpmn:endEvent', namespaces))
        elements['tasks'].extend(process.findall('.//bpmn:task', namespaces))
        elements['tasks'].extend(process.findall('.//bpmn:userTask', namespaces))
        elements['tasks'].extend(process.findall('.//bpmn:serviceTask', namespaces))
        elements['tasks'].extend(process.findall('.//bpmn:scriptTask', namespaces))
        elements['tasks'].extend(process.findall('.//bpmn:manualTask', namespaces))
        elements['gateways'].extend(process.findall('.//bpmn:exclusiveGateway', namespaces))
        elements['gateways'].extend(process.findall('.//bpmn:parallelGateway', namespaces))
        elements['gateways'].extend(process.findall('.//bpmn:inclusiveGateway', namespaces))
        elements['flows'].extend(process.findall('.//bpmn:sequenceFlow', namespaces))
    
    return elements


def validate_bpmn_structure(elements: Dict[str, List]) -> Tuple[bool, str]:
    """
    Validate basic BPMN structural requirements.
    
    Args:
        elements: Dictionary of BPMN elements
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check for at least one start event
    if len(elements['start_events']) == 0:
        return False, "BPMN must have at least one start event"
    
    # Check for at least one end event
    if len(elements['end_events']) == 0:
        return False, "BPMN must have at least one end event"
    
    # Check for sequence flows
    if len(elements['flows']) == 0:
        return False, "BPMN must have at least one sequence flow"
    
    return True, ""


def convert_bpmn_to_petri_net(xml_content: str) -> Tuple[PetriNet, Marking, Marking]:
    """
    Convert BPMN XML to a Petri net using pm4py.
    
    Args:
        xml_content: BPMN XML as string
        
    Returns:
        Tuple of (petri_net, initial_marking, final_marking)
        
    Raises:
        BPMNValidationError: If conversion fails
    """
    try:
        # Save XML to temporary string-based object for pm4py
        import tempfile
        import os
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bpmn', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(xml_content)
            temp_path = temp_file.name
        
        try:
            # Import BPMN and convert to Petri net
            bpmn_graph = pm4py.read_bpmn(temp_path)
            net, im, fm = pm4py.convert_to_petri_net(bpmn_graph)
            return net, im, fm
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except Exception as e:
        raise BPMNValidationError(f"Failed to convert BPMN to Petri net: {str(e)}")


def check_petri_net_soundness(net: PetriNet, im: Marking, fm: Marking) -> Tuple[bool, str]:
    """
    Check if the Petri net is sound (well-formed).
    
    A Petri net is sound if:
    1. It can always reach the final marking from the initial marking
    2. The final marking is the only marking reachable with no tokens in intermediate places
    3. There are no dead transitions (all transitions can fire in some reachable marking)
    
    Args:
        net: Petri net object
        im: Initial marking
        fm: Final marking
        
    Returns:
        Tuple of (is_sound, error_message)
    """
    try:
        # Check if there are places and transitions
        if len(net.places) == 0:
            return False, "Petri net has no places"
        
        if len(net.transitions) == 0:
            return False, "Petri net has no transitions"
        
        # Check if initial marking exists
        if not im:
            return False, "Initial marking is empty"
        
        # Check if final marking exists
        if not fm:
            return False, "Final marking is empty"
        
        # Use pm4py's soundness check (if available in the version)
        try:
            from pm4py.algo.analysis.woflan import algorithm as woflan
            is_sound = woflan.apply(net, im, fm)
            if not is_sound:
                return False, "Petri net is not sound: the process model may have deadlocks, livelocks, or unreachable parts"
        except ImportError:
            # Fallback: basic reachability check
            from pm4py.objects.petri_net.utils.reachability_graph import construct_reachability_graph
            
            try:
                # Check if final marking is reachable from initial marking
                reach_graph = construct_reachability_graph(net, im)
                
                # Check if final marking is in reachable states
                final_state_reachable = False
                for state in reach_graph.states:
                    if state == fm:
                        final_state_reachable = True
                        break
                
                if not final_state_reachable:
                    return False, "Final marking is not reachable from initial marking: the process cannot complete properly"
                    
            except Exception as e:
                # If reachability analysis fails, it might indicate structural problems
                return False, f"Cannot verify reachability: {str(e)}"
        
        return True, ""
        
    except Exception as e:
        return False, f"Error during soundness check: {str(e)}"


def validate_bpmn(xml_content: str) -> Dict[str, any]:
    """
    Main validation function that performs complete BPMN validation.
    
    Args:
        xml_content: BPMN XML as string
        
    Returns:
        Dictionary with validation results:
        {
            'valid': bool,
            'message': str,
            'error_type': str (optional)
        }
    """
    try:
        # Step 1: Parse XML
        root = parse_bpmn_xml(xml_content)
        
        # Step 2: Extract elements
        elements = extract_bpmn_elements(root)
        
        # Step 3: Validate basic structure
        is_valid, error_msg = validate_bpmn_structure(elements)
        if not is_valid:
            return {
                'valid': False,
                'message': error_msg,
                'error_type': 'structure_error'
            }
        
        # Step 4: Convert to Petri net
        try:
            net, im, fm = convert_bpmn_to_petri_net(xml_content)
        except BPMNValidationError as e:
            return {
                'valid': False,
                'message': str(e),
                'error_type': 'conversion_error'
            }
        
        # Step 5: Check Petri net soundness
        is_sound, error_msg = check_petri_net_soundness(net, im, fm)
        if not is_sound:
            return {
                'valid': False,
                'message': error_msg,
                'error_type': 'soundness_error'
            }
        
        # All checks passed
        return {
            'valid': True,
            'message': 'BPMN is valid and sound',
            'petri_net_info': {
                'places': len(net.places),
                'transitions': len(net.transitions),
                'arcs': len(net.arcs)
            }
        }
        
    except BPMNValidationError as e:
        return {
            'valid': False,
            'message': str(e),
            'error_type': 'validation_error'
        }
    except Exception as e:
        return {
            'valid': False,
            'message': f"Unexpected error during validation: {str(e)}",
            'error_type': 'unexpected_error'
        }
