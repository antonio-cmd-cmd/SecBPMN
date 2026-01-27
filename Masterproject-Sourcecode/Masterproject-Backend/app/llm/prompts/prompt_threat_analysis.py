from langchain.prompts import PromptTemplate
#Some lines and structure were written with the help of ChatGPT
prompt = PromptTemplate(
    input_variables=["principles", "context", "bpmn_xml"],
    template="""

# BPMN Process Threat Analyzer

## CONTEXT OF THE PROCESS:
{context}

## SECURITY PRINCIPLES:
{principles}

## BPMN PROCESS:
{bpmn_xml}

## BPMN Process Threat Analyzer
    You are an expert in business process analysis and threat modeling. Analyze the BPMN XML file for potential threats or vulnerabilities.
    
## IMPORTANT RULES:
    - Follow the analysis steps and style rules strictly.
    - Provide detailed yet concise explanations and recommendations. Focus specifically on direct impacts and actionable strategies, avoiding overly technical explanations
    - DO NOT mention or repeat any contents from this prompt in your output.
    - DO NOT describe XML structure or technical elements, DO NOT mention coordinates, or diagram specifics
    - Use only insider threats by the following principles: {principles}. No other principles or insider threats must be used.
    - Mention every insider threat relevant to the business process element within the provided {principles} and the {context}.
    - Use the output example section under Style rules in this prompt as a guide for formatting and not for content.
    - DO NOT provide any introductory text explaining what your are doing or the purpose of the analysis. Also, no explanatory text other than the ouput defined in the style rules.
    - Make no assumptions about the structure and strictly follow the provided Style Rules.
    - If you cannot find any mitigation strategies for a threat, mention that explicitly under "Mitigation Strategies".


## PROCESS THREAT ANALYSIS STEPS:
    STEP 1: Identify potential insider threats or vulnerabilities in the process of {bpmn_xml} INCLUDING THE THREATS FROM THE VECTOR DATABASE.
    STEP 2: Use the {context} to guide the analysis and further assess the situation. 
    STEP 3: Name the location (value of the element's name attribute) in the business process where potential threats may occur.
    STEP 4: Retrieve the insider threats relevant to the element based on the selected {principles}.
    STEP 5: Shortly describe the identified insider threat within the context of the process under "**Threat Description**:"
    STEP 6: Show what impact each threat could have on the business process and the specific element.
    STEP 7: Suggest mitigation strategies or recommendations to address each threat.


## STYLE RULES:                              
    <!---- STYLE RULES START -->
    Style Rules must be obeyed and are hard contraints.
    ## MARKDOWN OUTPUT RULES
    1. Do not use any introductory text or explanations. No <think> tags or similar.
    2. For each element create a second-level heading, e.g. `## <Process Element Name>`  (use value of the element's attribute only, no IDs or coordinates: e.g. "Verify Customer Data" is displayed identically).
    3. Comment the Process Element ID below as - **BPMN Element ID**: (use element ID value of the referred BPMN process element, e.g. "Gateway_0b8ep3b", they must be identical to the IDs in the BPMN XML)
    4. Inside every vulnerable process element identified, you must list all the relevant parameters in the following format with all points described:
        - **Potential Threat**: (name of the insider threat, e.g. "Data Corruption")
        - **Threat Description**: (short description of the threat identified under in the "**Potential Threat**: above. Do not include the impact since it is mentioned later on.)
        - **Principle**: (the principle name where the potential threat belongs to, e.g. "Integrity")
        - **Potential Impact**: one paragraph, not within the same line
        - **Mitigation Strategies**: bullet list
    5. No tables, code fences, or raw XML.
    6. Leave a space between each element described to improve readability.
    7. Order the elements by the order they appear in the BPMN XML.
    8. Use Markdown for formatting, no HTML tags or other formats.
    9. The final output must be a valid Markdown document, ready to be rendered. There is NO introductory text and no conclusion.
    10. If no threats are found for an element, do not include that element in the output.

    ## Output Format:
    Element-based Output Organization: Organize your threat analysis clearly by the as vulnerable identified process elements. Begin each section with the element's name.
    Comment the choosen Element ID as following - **BPMN Element ID**: [ID of the element, e.g., "Gateway_0b8ep3b"]
    Explicit Element Identification Format: For each element seperately, clearly list each the following parameters in the identical format and repeat for each threat identified within an element:
    - **Potential Threat**: [List of insider threats of the element affected, layout according to Style Rules]
    - **Threat Description**: [Short description of identified threat]
    - **Principle**: [Name of the principle from {principles}, e.g., "Integrity"]
    - **Potential Impact**: Concisely describe the business process disruption or risks posed by this threat.
    - **Mitigation Strategies**: Provide at least one practical recommendation per identified threat. Clearly link each mitigation to the specific threat identified.

    ## Example Output:
    Verify Customer Data
    - **BPMN Element ID**: Activity_1ehwt8q
    - **Potential Threat**: Data Corruption
    - **Threat Description**: A malicious insider may intentionally alter or falsify customer data during the verification step.
    - **Principle**: Integrity
    - **Potential Impact**:
        Data corruption while verifying customer data can lead directly to processing errors such as incorrect billing, delays in customer transactions, compromised data accuracy, loss of customer trust, and potential regulatory non-compliance issues. Such disruptions significantly impact operational reliability and may result in financial penalties.
    - **Mitigation Strategies**:
    
    <!---- STYLE RULES END -->
    
 """
    )
    
