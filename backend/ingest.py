from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()

def get_embeddings():
    """Initializes the embedding model."""
    return HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

def process_pdfs_to_chunks(pdf_paths, original_names=None):
    """
    Loads PDFs, splits them into chunks, and calculates 
    precise metadata including original line numbers.
    """
    all_chunks = []

    # 'add_start_index=True' is the key to fixing the Line 1 bug.
    # It tracks the character offset of each chunk within the page.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True
    )

    for i, pdf_path in enumerate(pdf_paths):
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()

        for page in pages:
            # Add the source file name to the page metadata
            source_name = original_names[i] if original_names and i < len(original_names) else os.path.basename(pdf_path)
            
            # Split this specific page into chunks
            page_chunks = splitter.split_documents([page])

            for chunk in page_chunks:
                # 1. Assign the correct source name
                chunk.metadata['source'] = source_name
                
                # 2. CALCULATE REAL LINE NUMBER:
                # Get the character index where this chunk starts on the page.
                start_char_index = chunk.metadata.get('start_index', 0)
                
                # Count how many newlines (\n) exist in the page text BEFORE this chunk.
                text_before_chunk = page.page_content[:start_char_index]
                real_line_number = text_before_chunk.count('\n') + 1
                
                # Update the metadata with the actual line number
                chunk.metadata['start_line'] = real_line_number

                # 3. Create a clean preview for the UI
                clean_text = ' '.join(chunk.page_content.split())
                preview = clean_text[:120]
                chunk.metadata['preview'] = preview + "..." if len(clean_text) > 120 else clean_text

                all_chunks.append(chunk)

    return all_chunks

def ingest_pdfs(pdf_paths, original_names=None, existing_vectorstore=None):
    """
    Main entry point to embed chunks and store them in ChromaDB.
    """
    embeddings = get_embeddings()
    new_chunks = process_pdfs_to_chunks(pdf_paths, original_names=original_names)

    if existing_vectorstore is None:
        # If no existing DB, create a new one
        vectorstore = Chroma.from_documents(
            documents=new_chunks,
            embedding=embeddings,
            persist_directory="./chroma_db" # Persists the data locally
        )
    else:
        # If DB exists, just add the new documents
        existing_vectorstore.add_documents(new_chunks)
        vectorstore = existing_vectorstore

    return vectorstore