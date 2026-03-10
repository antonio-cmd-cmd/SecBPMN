import ollama

client = ollama.Client()

model = "phi4"
with open("resources/insiderThreatBPMN.bpmn", "r", encoding="utf-8") as file:
    bpmn = file.read()
prompt = "Tell me what this process does."

print(model)
response = client.generate(model=model, prompt=prompt)

print("Response from Ollama:")
print(response.response)