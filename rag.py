from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
import os
from llama_index.readers.file import PDFReader
from llama_index.core import Document


def load_pdf_for_rag(pdf_path):
    # Load the pdf as documents
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"The PDF file '{pdf_path}' does not exist.")

    pdf_reader = PDFReader()
    documents = pdf_reader.load_data(file=pdf_path)

    # Initialize the VectorStoreIndex with the loaded documents
    index = VectorStoreIndex.from_documents(documents)

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