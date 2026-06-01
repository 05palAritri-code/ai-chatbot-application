from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from typing import Any, Dict, Optional, TypedDict, Annotated
import tempfile
import os


embeddings = HuggingFaceEmbeddings(model_name = "sentence-transformers/all-MiniLM-L6-v2")

def thread_has_document(thread_id : str) -> bool:
    return str(thread_id) in _THREAD_RETRIEVERS

def thread_document_metadata(thread_id : str) -> dict:
    return _THREAD_METADATA.get(str(thread_id),{})

_THREAD_RETRIEVERS : Dict[str,Any] ={}
_THREAD_METADATA : Dict[str,dict] ={}

def _get_retriever(thread_id : Optional[str]):
    if thread_id and thread_id in _THREAD_RETRIEVERS:
        return _THREAD_RETRIEVERS[thread_id]
    return None

def ingest_pdf(file_bytes : bytes , thread_id : str , filename : Optional[str] = None) -> dict:
    '''Build a retirever for the uploaded pdf and store it for the thread.
    returns a summary dict that can be surfaced in the UI
    Ingest a PDF file, split it into chunks, create embeddings, and store in vector store'''

    if not file_bytes:
        raise ValueError('No bytes received for ingestion.')
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        temp_file.write(file_bytes)
        temp_path = temp_file.name
    try:
        loader = PyPDFLoader(temp_path)
        docs = loader.load()

        # if not docs:
        #     raise ValueError("PDF has no readable text.")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200, separators=["\n\n", "\n", " ", ""]
            )
        chunks = splitter.split_documents(docs)
        # if not chunks:
        #     raise ValueError("Chunking failed.")

        vector_store = Chroma.from_documents(chunks, embeddings)
        retriever = vector_store.as_retriever(
            search_type = 'mmr',search_kwargs = {'k':2}
        )

        _THREAD_RETRIEVERS[str(thread_id)] = retriever
        _THREAD_METADATA[str(thread_id)] = {
            'filename': filename or os.path.basename(temp_path),
            'documents' : len(docs),
            'chunks' : len(chunks)
        }

        return{
            'filename': filename or os.path.basename(temp_path),
            'documents' : len(docs),
            'chunks' : len(chunks)
        }

    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass