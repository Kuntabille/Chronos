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

def load_index(index_name):
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
    return index

def load_index_for_rag(index_name):
    index = load_index(index_name)
    # Create a retriever from the index
    #retriever = index.as_retriever()
    retriever = index.as_retriever(retrieval_mode='similarity', k=4)
    return retriever

def load_query_engine(index_name):
    index = load_index(index_name)
    # Create query engine from the index
    query_engine = index.as_query_engine()
    return query_engine

# The score_threshold determines how relevant a node's text must be to add it
#  to the content.  Typicaly 0.63 or higher yields relevant content.  Default
#  is 0, which means any returned node will be used.
def fetch_relevant_documents(message, retriever, score_threshold=0.0):
    if retriever is None:
        raise ValueError("Retriever has not been initialized. Call load_pdf_for_rag() first.")

    # Retrieve relevant nodes based on the input message
    retrieved_nodes = retriever.retrieve(message)

    if not retrieved_nodes:
        return "No relevant information found."

    # Combine the content of retrieved nodes into a single string
    relevant_content = "\n\n\n"
    for node in retrieved_nodes:
        if node.score > score_threshold:
            # only add content that is above the score threshold
            relevant_content += node.node.text
    return relevant_content