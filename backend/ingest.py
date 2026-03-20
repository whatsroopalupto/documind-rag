from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()

def ingest_pdfs(pdf_paths):
    all_documents = []

    # Step 1 - Load each PDF
    for pdf_path in pdf_paths:
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        all_documents.extend(documents)

    # Step 2 - Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = splitter.split_documents(all_documents)

    # Step 3 - Create embeddings and store in ChromaDB
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings
    )

    return vectorstore