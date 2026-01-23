from langchain.schema import Document
# --- Flatten into Documents ---
def extract_threat_docs(data):
    #This function was written with the help of ChatGPT.
    docs = []
    for i, item in enumerate(data):
        principle = item["principle"]
        for j, threat_group in enumerate(item["threats"]):
            tg_name = threat_group["threatGroup"]
            tg_desc = threat_group["description"]
            tg_examples = threat_group["exampleThreats"]

            # Format examples list as bullet points
            examples_formatted = "\n- " + "\n- ".join(tg_examples)

            # Build the document content
            content = (
                f"Security Principle: {principle}\n\n"
                f"Insider Threat: {tg_name}\n\n"
                f"Description: {tg_desc}\n\n"
                f"Example Threats: {examples_formatted}"
            )

            doc_id = f"{i}_{j}"
            doc = Document(
                page_content=content,
                metadata={
                    "id": doc_id,
                    "principle": principle,
                    "threat_group": tg_name,
                }
            )
            docs.append(doc)

    return docs