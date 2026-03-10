"""
Petri Net Refinement Module

This module handles Petri Net validation after dual-LLM iterations
and performs additional refinement iterations if structural issues are found.
"""

import logging
from typing import Dict, List, Optional, Tuple
from ..utils.bpmn_validator import validate_bpmn
from ..config import (
    ENABLE_PETRI_NET_VALIDATION,
    MAX_PETRI_NET_FIX_ITERATIONS,
    PETRI_NET_STRICT_MODE
)

logger = logging.getLogger(__name__)


def validate_with_petri_net(bpmn_xml: str) -> Dict[str, any]:
    """
    Validate BPMN using Petri Net analysis.
    
    Args:
        bpmn_xml: BPMN XML content as string
        
    Returns:
        Dictionary with validation results:
        {
            'valid': bool,
            'message': str,
            'error_type': str (optional),
            'petri_net_info': dict (optional)
        }
    """
    logger.info("🔍 Starting Petri Net validation...")
    
    try:
        result = validate_bpmn(bpmn_xml)
        
        if result['valid']:
            logger.info("✅ Petri Net validation PASSED")
            logger.info(f"   Places: {result.get('petri_net_info', {}).get('places', 'N/A')}")
            logger.info(f"   Transitions: {result.get('petri_net_info', {}).get('transitions', 'N/A')}")
            logger.info(f"   Arcs: {result.get('petri_net_info', {}).get('arcs', 'N/A')}")
        else:
            logger.warning(f"❌ Petri Net validation FAILED: {result['message']}")
            logger.warning(f"   Error type: {result.get('error_type', 'unknown')}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error during Petri Net validation: {str(e)}")
        return {
            'valid': False,
            'message': f"Petri Net validation error: {str(e)}",
            'error_type': 'validation_exception'
        }


def create_petri_net_fix_prompt(
    bpmn_xml: str,
    petri_net_issues: Dict[str, any],
    attempt_number: int
) -> str:
    """
    Create a prompt for the Generator LLM to fix Petri Net issues.
    
    Args:
        bpmn_xml: Current BPMN XML
        petri_net_issues: Validation result from Petri Net check
        attempt_number: Current attempt number
        
    Returns:
        Prompt string for LLM
    """
    error_type = petri_net_issues.get('error_type', 'unknown')
    error_message = petri_net_issues.get('message', 'Unknown error')
    
    # Detailed explanation based on error type
    error_explanations = {
        'structure_error': """
This is a basic structural error. The BPMN model is missing essential elements like start/end events or sequence flows.
Ensure that:
- At least one Start Event exists
- At least one End Event exists
- All elements are properly connected with sequence flows
""",
        'conversion_error': """
The BPMN model could not be converted to a Petri Net. This usually indicates:
- Invalid BPMN XML syntax or structure
- Unsupported BPMN elements
- Malformed element definitions
Check that all BPMN elements follow the BPMN 2.0 specification.
""",
        'soundness_error': """
The Petri Net derived from this BPMN is not sound. This means the process has structural flaws:
- **Deadlocks**: The process can get stuck with no way to proceed
- **Unreachable states**: Parts of the process can never be executed
- **Improper completion**: The process cannot reach the end state properly

Common causes:
- Missing sequence flows between gateways and activities
- Gateways with incorrect numbers of incoming/outgoing flows
- Parallel gateways not properly paired (split without corresponding join)
- Exclusive gateways with missing branches or conditions
- Activities that have no path to the end event
""",
        'validation_error': """
General validation error occurred. Check the BPMN structure carefully.
""",
        'unexpected_error': """
An unexpected error occurred during validation. Review the entire BPMN structure.
"""
    }
    
    explanation = error_explanations.get(error_type, error_explanations['unexpected_error'])
    
    prompt = f"""# 🔧 PETRI NET VALIDATION FAILURE - FIX REQUIRED (Attempt {attempt_number}/{MAX_PETRI_NET_FIX_ITERATIONS})

## ⚠️ Problem Detected
The BPMN model has passed semantic validation but **FAILED Petri Net soundness verification**.

### Error Type: {error_type}
### Error Message: {error_message}

{explanation}

## 📋 Current BPMN XML (with structural issues)
```xml
{bpmn_xml}
```

## 🎯 Your Task
**Fix the structural issues** in this BPMN model to make it **sound** from a Petri Net perspective.

### Requirements:
1. **Maintain all security mitigations** - do NOT remove any security controls
2. **Fix only structural/flow issues** - focus on proper connections and gateway logic
3. **Ensure soundness**:
   - All paths from Start to End must be complete
   - No deadlocks (processes getting stuck)
   - All activities must be reachable
   - Gateways must be properly balanced (splits have corresponding joins)
4. **Follow BPMN 2.0 specification** strictly
5. **Return ONLY valid XML** - no explanations, no markdown, just pure XML

### Common Fixes:
- Add missing sequence flows
- Balance parallel gateways (every parallel split needs a parallel join)
- Ensure exclusive gateways have all branches defined
- Check that all activities can reach the end event
- Verify that all elements have proper IDs and references

## 📤 Output Format
Return ONLY the corrected BPMN XML, starting with:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions ...>
```

**DO NOT include any explanations or comments. ONLY XML.**
"""
    
    return prompt


def format_petri_net_result(
    validation_result: Dict[str, any],
    iteration_number: int,
    is_final: bool = False
) -> str:
    """
    Format Petri Net validation result for logging and user display.
    
    Args:
        validation_result: Result from Petri Net validation
        iteration_number: Current iteration number
        is_final: Whether this is the final result
        
    Returns:
        Formatted string
    """
    if validation_result['valid']:
        info = validation_result.get('petri_net_info', {})
        result = f"""
{'='*80}
🎉 PETRI NET VALIDATION SUCCESSFUL (Iteration {iteration_number})
{'='*80}
✅ The BPMN model is SOUND and structurally correct!

Petri Net Statistics:
  - Places: {info.get('places', 'N/A')}
  - Transitions: {info.get('transitions', 'N/A')}
  - Arcs: {info.get('arcs', 'N/A')}

This means:
  ✓ All process paths can reach completion
  ✓ No deadlocks or unreachable states
  ✓ Proper gateway balancing
  ✓ Valid BPMN 2.0 structure
{'='*80}
"""
    else:
        status = "FINAL RESULT" if is_final else f"Attempt {iteration_number}"
        result = f"""
{'='*80}
❌ PETRI NET VALIDATION FAILED ({status})
{'='*80}
Error Type: {validation_result.get('error_type', 'unknown')}
Message: {validation_result.get('message', 'Unknown error')}

This indicates structural issues in the BPMN model.
{'='*80}
"""
    
    return result


def should_enable_petri_net_validation() -> bool:
    """
    Check if Petri Net validation is enabled in configuration.
    
    Returns:
        True if enabled, False otherwise
    """
    return ENABLE_PETRI_NET_VALIDATION


def get_max_petri_net_iterations() -> int:
    """
    Get maximum number of Petri Net fix iterations from configuration.
    
    Returns:
        Maximum iterations
    """
    return MAX_PETRI_NET_FIX_ITERATIONS


def is_strict_mode() -> bool:
    """
    Check if strict mode is enabled (reject if not sound).
    
    Returns:
        True if strict mode enabled, False for warning-only mode
    """
    return PETRI_NET_STRICT_MODE
