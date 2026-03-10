import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import LanceDB
from langchain.text_splitter import RecursiveCharacterTextSplitter
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


def setup_mitigation_vectorstore(docs, db_path="lance_mitigation_db", chunk_size=500, chunk_overlap=100):
    """
    Setup a separate vectorstore for mitigation best practices with chunking.
    
    Args:
        docs: List of Document objects containing mitigation practices
        db_path: Path to the LanceDB database for mitigations
        chunk_size: Size of text chunks (default: 500 characters)
        chunk_overlap: Overlap between chunks (default: 100 characters)
        
    Returns:
        LanceDB vectorstore instance
    """
    os.makedirs(db_path, exist_ok=True)
    embeddings_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    connection = lancedb.connect(db_path)

    # Initialize text splitter for chunking
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    # Split documents into chunks
    print(f"Splitting {len(docs)} mitigation documents into chunks...")
    chunked_docs = text_splitter.split_documents(docs)
    print(f"Created {len(chunked_docs)} chunks from {len(docs)} documents")

    # Add chunk information to metadata
    for i, doc in enumerate(chunked_docs):
        doc.metadata['chunk_id'] = i

    texts = [doc.page_content for doc in chunked_docs]
    metadata = [doc.metadata for doc in chunked_docs]

    embeddings = embeddings_model.embed_documents(texts)

    data = [
        {"vector": emb, "text": text, "metadata": meta}
        for emb, text, meta in zip(embeddings, texts, metadata)
    ]

    if not data:
        raise ValueError("No mitigation documents to insert into LanceDB!")

    print(f"Embedding {len(chunked_docs)} mitigation chunks...")
    table_name = "mitigation_practices"
    if table_name in connection.table_names():
        table = connection.open_table(table_name)
    else:
        table = connection.create_table(table_name, data=data)

    vectorstore = LanceDB(
        connection=connection,
        embedding=embeddings_model,
        table=table)

    return vectorstore