from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
import chromadb
import os
from llama_index.readers.file import PDFReader
from llama_index.vector_stores.chroma import ChromaVectorStore


def load_pdf_for_rag(pdf_path, storage_context):
    # Load the pdf as documents
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"The PDF file '{pdf_path}' does not exist.")

    pdf_reader = PDFReader()
    documents = pdf_reader.load_data(file=pdf_path)

    # Initialize the VectorStoreIndex with the loaded documents
    index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
    return index

def load_index_for_rag(index_name):
    # generate database name to load
    db_name = "index_dbs/" + index_name + "_db"
    if not os.path.exists(db_name):
        create_db = True
    else:
        create_db = False

    # initialize client, setting path to save data
    db = chromadb.PersistentClient(path=db_name)

    # create collection
    chroma_collection = db.get_or_create_collection("quickstart")

    # assign chroma as the vector_store to the context
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    if create_db:
        # load index from pdf file and create the database for next time
        pdf_path = "data/" + index_name + ".pdf"
        index = load_pdf_for_rag(pdf_path, storage_context)
    else:
        # load index from database
        index = VectorStoreIndex.from_vector_store(
            vector_store, storage_context=storage_context
        )

    # Create a retriever from the index
    retriever = index.as_retriever()
    return retriever

def fetch_relevant_documents(message, retriever):
    if retriever is None:
        raise ValueError("Retriever has not been initialized. Call load_pdf_for_rag() first.")
    
    # Retrieve relevant nodes based on the input message
    retrieved_nodes = retriever.retrieve(message)
    print(f"{len(retrieved_nodes)} documents found.")
    
    if not retrieved_nodes:
        return "No relevant information found."
    
    # Combine the content of retrieved nodes into a single string
    relevant_content = "\n\n\n".join([node.node.text for node in retrieved_nodes])

    return relevant_content