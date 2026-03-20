from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()

def get_embeddings():
    """
    Returns the embeddings model.
    Separated into its own function so it can be reused
    without creating a new instance every time.
    """
    return GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )


def process_pdfs_to_chunks(pdf_paths):
    """
    Loads PDFs and splits them into chunks.
    Returns the chunks — does NOT touch the vectorstore.
    This way we can use it for both fresh ingestion
    and incremental updates.
    """
    all_documents = []

    for pdf_path in pdf_paths:
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        all_documents.extend(documents)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = splitter.split_documents(all_documents)
    return chunks


def ingest_pdfs(pdf_paths, existing_vectorstore=None):
    """
    Main ingestion function.

    Two modes:
    1. existing_vectorstore is None — fresh start, create a new ChromaDB
    2. existing_vectorstore is provided — just add new chunks to it

    This means if a user uploads 3 PDFs one by one:
    - First upload: creates vectorstore from scratch (slow is fine, only 1 PDF)
    - Second upload: adds only the new PDF chunks to existing vectorstore
    - Third upload: adds only the new PDF chunks to existing vectorstore

    Instead of re-processing all 3 PDFs every single time.
    """
    embeddings = get_embeddings()

    # Process only the new PDFs into chunks
    new_chunks = process_pdfs_to_chunks(pdf_paths)

    if existing_vectorstore is None:
        # Fresh start — create a brand new vectorstore
        vectorstore = Chroma.from_documents(
            documents=new_chunks,
            embedding=embeddings
        )
    else:
        # Incremental update — just add new chunks to existing vectorstore
        # This is the key fix — no re-processing of old files
        existing_vectorstore.add_documents(new_chunks)
        vectorstore = existing_vectorstore

    return vectorstore