# main.py
import json5
import requests
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableMap, RunnableLambda
from langchain.chains import RetrievalQA, StuffDocumentsChain, LLMChain
from langchain_core.output_parsers import StrOutputParser
from langchain.docstore.document import Document
from langchain.llms.base import LLM
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from app.llm.prompts.prompt_test1 import prompt
from langchain_community.vectorstores import LanceDB
from langchain_community.chat_models import ChatOllama
from typing import Optional, List
from langchain.llms.base import LLM
import lancedb
import os


LLM_MODEL = "llama3.2"

# --- Ollama Wrapper ---
class OllamaLLM(LLM):
    model: str = LLM_MODEL
    base_url: str = "http://localhost:11434"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False}
        )
        print("DEBUG Ollama API response:", response.json())
        return response.json()["response"]

    @property
    def _llm_type(self) -> str:
        return "ollama"

# --- Load JSON-ish JS File ---
def load_knowledge_base(js_path: str):
    with open(js_path, "r") as f:
        js_content = f.read()
    js_content = js_content.strip().rstrip(";")
    return json5.loads(js_content)

# --- Flatten into Documents ---
def extract_threat_docs(data):
    docs = []
    for i, item in enumerate(data):
        principle = item["principle"]
        for j, threat_group in enumerate(item["threats"]):
            tg_name = threat_group["threatGroup"]
            tg_desc = threat_group["description"]
            for k, threat in enumerate(threat_group["exampleThreats"]):
                doc_id = f"{i}_{j}_{k}"
                content = f"{principle} - {tg_name}: {threat} - {tg_desc}"
                doc = Document(page_content=content, metadata={"id": doc_id})
                docs.append(doc)
    return docs

# --- LanceDB Setup ---
def setup_vectorstore_lance(docs, db_path="lance_threat_db"):
    os.makedirs(db_path, exist_ok=True)
    embeddings_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    connection = lancedb.connect(db_path)

    texts = [doc.page_content for doc in docs]
    metadata = [doc.metadata for doc in docs]

    embeddings = embeddings_model.embed_documents(texts)

    data = [
        {"vector": emb, "text": text, "metadata": meta}
        for emb, text, meta in zip(embeddings, texts, metadata)
    ]

    if not data:
        raise ValueError("No documents to insert into LanceDB!")

    print(f"Embedding {len(docs)} documents...")
    table_name = "insider_threats"
    if table_name in connection.table_names():
        table = connection.open_table(table_name)
    else:
        table = connection.create_table(table_name, data=data)

    vectorstore = LanceDB(
        connection=connection,
        embedding=embeddings_model,
        table=table)

    return vectorstore

# --- QA Chain ---
def setup_qa_chain(vectorstore):
    retriever = vectorstore.as_retriever(search_type="similarity", k=5)
    llm = ChatOllama(model=LLM_MODEL)
    qa = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, return_source_documents=True)
    return qa
    

    chain = (
        {"context": RunnableLambda(lambda x: retriever.invoke(x["query"])),
        "question": RunnableLambda(lambda x: x["query"])
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    def qa_chain(inputs):
        result = chain.invoke(inputs)
        sources = retriever.get_relevant_documents(inputs["query"])
        return {
            "result": result,
            "source_documents": sources
        }

    return qa_chain


# --- Main ---
def random_threat_analyzer():
    kb_data = load_knowledge_base("resources/knowledgeBaseLLMWithThreats.json")
    docs = extract_threat_docs(kb_data)
    vs = setup_vectorstore_lance(docs)
    qa_chain = setup_qa_chain(vs)

    while True:
        query = input("Ask a security threat question (or type 'exit'): ")
        if query.lower() == "exit":
            break
        result = qa_chain({"query": query})
        print("\n🧠 Answer:")
        print(result["result"])
        print("\n📚 Source Context:")
        for doc in result["source_documents"]:
            print("-", doc.page_content)
