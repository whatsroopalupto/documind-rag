from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import os
import warnings
from dotenv import load_dotenv

# Suppress warnings
warnings.filterwarnings("ignore")
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"


load_dotenv()

def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )


def process_pdfs_to_chunks(pdf_paths, original_names=None):
    all_documents = []

    for i, pdf_path in enumerate(pdf_paths):
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()

        if original_names and i < len(original_names):
            for doc in documents:
                doc.metadata['source'] = original_names[i]

        all_documents.extend(documents)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = splitter.split_documents(all_documents)

    # Add line number and preview to each chunk's metadata
    for chunk in chunks:
        page_text = chunk.page_content

        lines = page_text.split('\n')
        chunk.metadata['start_line'] = 1

        for line_num, line in enumerate(lines, start=1):
            if line.strip():
                chunk.metadata['start_line'] = line_num
                break

        preview = ' '.join(page_text.split())[:120]
        chunk.metadata['preview'] = preview + "..." if len(preview) >= 120 else preview

    return chunks


def ingest_pdfs(pdf_paths, original_names=None, existing_vectorstore=None):
    embeddings = get_embeddings()

    new_chunks = process_pdfs_to_chunks(pdf_paths, original_names=original_names)

    if existing_vectorstore is None:
        vectorstore = Chroma.from_documents(
            documents=new_chunks,
            embedding=embeddings
        )
    else:
        existing_vectorstore.add_documents(new_chunks)
        vectorstore = existing_vectorstore

    return vectorstore