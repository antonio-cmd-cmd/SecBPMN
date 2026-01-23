import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import LanceDB
import lancedb

# --- LanceDB Setup ---
def setup_vectorstore_lance(docs, db_path="lance_threat_db"):

    #This function was written with the help of ChatGPT.

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