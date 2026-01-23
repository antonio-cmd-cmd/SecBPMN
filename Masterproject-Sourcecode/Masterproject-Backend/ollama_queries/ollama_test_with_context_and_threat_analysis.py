import ollama

client = ollama.Client()

model = "deepseek-r1:14b"

with open("resources/testBusinessProcessSIMPLIFIED.bpmn", "r", encoding="utf-8") as file:
    bpmn_file = file.read()


prompt = f"""You are an expert in business process modeling (BPMN).  
# BPMN Process Analyzer

You are an expert in business process analysis. Extract and explain the business process from this BPMN XML file.

## IMPORTANT RULES:
- DO NOT describe XML structure or technical elements
- DO NOT mention IDs, coordinates, or diagram specifics
- ONLY focus on named elements that describe the business process flow

## EXTRACTION STEPS:

STEP 1: Extract ALL elements with name attributes into this format:
- Start Events: [list all <startEvent name="X">]
- Tasks: [list all <task name="X"> or variants]
- Gateways: [list all <gateway name="X"> and their types]
- Sequence Flows with names: [list all flows with names/conditions]
- End Events: [list all <endEvent name="X">]

STEP 2: Identify the process participant(s) and their role.

STEP 3: Create a human-readable process description using ONLY these extracted names.

## OUTPUT FORMAT:

**Process Title:** [Create a descriptive title based on the process]

**Process Overview:**
- This process handles: [Main purpose/goal]
- Key participants: [Who performs the activities]
- Starts when: [Trigger or initial condition]
- Ends when: [Final outcome or condition]

**Process Flow:**
1. The process begins when [start event name].
2. First, [first task name] occurs.
3. Then, at [gateway name] decision point:
   - If [condition 1], then [next task on this path]
   - If [condition 2], then [next task on alternate path]
4. [Continue describing each step in order]
5. The process ends with [end event name].

**Key Decision Points:**
- [Decision 1]: [Explain the decision logic and outcomes]
- [Decision 2]: [Explain the decision logic and outcomes]

## EXAMPLE OUTPUT:

For a BPMN process about order processing:

**Process Title:** Customer Order Fulfillment Process

**Process Overview:**
- This process handles: Customer order processing from receipt to delivery
- Key participants: Sales department, Warehouse staff, Shipping team
- Starts when: A new order is received
- Ends when: Order is delivered or canceled

**Process Flow:**
1. The process begins when "new order received".
2. First, "validate order details" occurs.
3. Then, at "is order valid?" decision point:
   - If "yes", then "process payment" occurs
   - If "no", then "contact customer" occurs
4. After "process payment", "check inventory" determines stock availability.
5. If "items available", then "pack items" and "ship order" occur.
6. The process ends with "order delivered" or "order canceled".

**Key Decision Points:**
- "is order valid?": Determines whether to proceed with order processing or contact customer for corrections
- "items available?": Determines whether to fulfill order immediately or place on backorder

Now analyze the provided BPMN XML using this exact approach.
Here is the diagram:\n\n{bpmn_file}\n\n"""

# Ask the user to give some context about the business process
print("Please answer the following question:")
print("Can you give me a brief summary of the business process described in the BPMN XML file?")
print("(Type your answer and press Enter when finished)")

# Get user input and save it in userAnswer variable
userAnswer = input("> ")

# Confirm the answer was recorded
print("\nThank you for your response!")

# Add userAnswer to the prompt
if userAnswer:
   prompt += "Consider the following background information for the interpretation of the business process:\n"
   prompt += userAnswer

# print(prompt)

response = client.generate(model=model, prompt=prompt)

print(f"\n\nResponse from Ollama {model}:")
print(response.response)

print("\n\nNow let's see what threats the LLM can find in the BPMN XML file.")

second_prompt = f"""You are an expert in business process modeling (BPMN) and threat analysis.
# BPMN Process Threat Analyzer
You are an expert in business process analysis and threat modeling. Analyze the BPMN XML file for potential threats or vulnerabilities.
## IMPORTANT RULES:
- DO NOT describe XML structure or technical elements
- DO NOT mention IDs, coordinates, or diagram specifics
- ONLY focus on named elements that describe the business process flow

Consider the response from the previous analysis as background information for your interpretation of the business process:
{response.response}
__________________________________________________________________________________________________

## PROCESS THREAT ANALYSIS STEPS:
STEP 1: Identify potential threats or vulnerabilities in the process flow.
STEP 2: Describe the potential location in the business process of each identified threat.
STEP 3: Show what impact each threat could have on the business process.
STEP 4: Suggest mitigation strategies or recommendations to address each threat."""

#print("\n\nSecond prompt:")
#print(second_prompt)

response2 = client.generate(model=model, prompt=second_prompt)

print(f"\n\nResponse from Ollama {model}:")
print(response2.response)