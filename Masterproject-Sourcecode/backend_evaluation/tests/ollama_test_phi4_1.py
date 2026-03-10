import ollama

def read_bpmn_file(file_path, model, prompt=None):
    # Initialize the ollama client with the specified model
    client = ollama.Client(model=model)

    # Read the BPMN file
    with open(file_path, 'r') as file:
        bpmn_content = file.read()

    # Use the client to process the BPMN file content
    if prompt:
        response = client.analyze(bpmn_content, prompt=prompt)
    else:
        response = client.analyze(bpmn_content)

    return response

# Path to your BPMN file
file_path = 'resources/insiderThreatBPMN.bpmn'

# Call the function with the model 'phi4'
# Optionally, you can add a custom prompt by specifying the prompt parameter
response = read_bpmn_file(file_path, model='phi4', prompt="Analyze potential threats")

# Print the response from the ollama client
print(response)

