from langchain.chains import RetrievalQA
from langchain_ollama import ChatOllama
from app.config import LLM_MODEL, OLLAMA_BASE_URL


def build_qa_chain(vectorstore):
    retriever = vectorstore.as_retriever(search_type="similarity", k=5)

    llm = ChatOllama(
        model=LLM_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.3,
    )

    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=True
    )
