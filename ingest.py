# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_community.document_loaders import PyPDFLoader
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# # from langchain_community.vectorstores import Chroma
# from langchain_postgres import PGVector
# from typing import Any, Dict, Optional
# import tempfile
# import os
# from dotenv import load_dotenv

# load_dotenv()

# db_url = os.getenv("DATABASE_URL")

# embeddings = HuggingFaceEmbeddings(model_name = "sentence-transformers/all-MiniLM-L6-v2")




# _THREAD_RETRIEVERS : Dict[str,Any] ={}
# _THREAD_METADATA : Dict[str,dict] ={}

# # def thread_has_document(thread_id : str) -> bool:
# #     return str(thread_id) in _THREAD_RETRIEVERS

# def thread_has_document(thread_id: str) -> bool:
#     return True

# def thread_document_metadata(thread_id : str) -> dict:
#     return _THREAD_METADATA.get(str(thread_id),{})

# # def _get_retriever(thread_id : Optional[str]):
# #     if thread_id and thread_id in _THREAD_RETRIEVERS:
# #         return _THREAD_RETRIEVERS[thread_id]
# #     return None

# def _get_retriever(thread_id):

#     if not thread_id:
#         return None

#     vector_store = PGVector(
#         embeddings=embeddings,
#         collection_name="documents",
#         connection=db_url,
#     )

#     return vector_store.as_retriever(
#         search_type="mmr",
#         search_kwargs={
#             "k": 2,
#             "filter": {
#                 "thread_id": str(thread_id)
#             }
#         }
#     )


# def ingest_pdf(file_bytes : bytes , thread_id : str , filename : Optional[str] = None) -> dict:
#     '''Build a retirever for the uploaded pdf and store it for the thread.
#     returns a summary dict that can be surfaced in the UI
#     Ingest a PDF file, split it into chunks, create embeddings, and store in vector store'''

#     if not file_bytes:
#         raise ValueError('No bytes received for ingestion.')
#     with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
#         temp_file.write(file_bytes)
#         temp_path = temp_file.name
#     try:
#         loader = PyPDFLoader(temp_path)
#         docs = loader.load()

#         # if not docs:
#         #     raise ValueError("PDF has no readable text.")

#         splitter = RecursiveCharacterTextSplitter(
#             chunk_size=1000, chunk_overlap=200, separators=["\n\n", "\n", " ", ""]
#             )
#         chunks = splitter.split_documents(docs)

#         # vector_store = Chroma.from_documents(chunks, embeddings)
#         # retriever = vector_store.as_retriever(
#         #     search_type = 'mmr',search_kwargs = {'k':2}
#         # )

#         # _THREAD_RETRIEVERS[str(thread_id)] = retriever

#         for chunk in chunks:
#             chunk.metadata["thread_id"] = str(thread_id)
#             chunk.metadata["filename"] = (
#                 filename or os.path.basename(temp_path)
#             )

#         vector_store = PGVector(
#             embeddings=embeddings,
#             collection_name="documents",
#             connection=db_url,
#         )

#         vector_store.add_documents(chunks)

#         _THREAD_METADATA[str(thread_id)] = {
#             "filename": filename or os.path.basename(temp_path),
#             "documents": len(docs),
#             "chunks": len(chunks),
#         }

#         return{
#             'filename': filename or os.path.basename(temp_path),
#             'documents' : len(docs),
#             'chunks' : len(chunks)
#         }

#     finally:
#         try:
#             os.remove(temp_path)
#         except OSError:
#             pass

from typing import Optional
import os
import tempfile
import streamlit as st
from dotenv import load_dotenv

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_postgres import PGVector
import psycopg

load_dotenv()

vector_db_url = os.getenv("VECTOR_DB_URL")

db_url =os.getenv("DATABASE_URL")

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

def get_vector_store():
    return PGVector(
        embeddings=embeddings,
        collection_name="documents",
        connection=vector_db_url,
    )


# def thread_has_document(thread_id: str) -> bool:
#     return str(thread_id) in _THREAD_METADATA
def thread_has_document(thread_id: str):

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cursor:

            cursor.execute(
                """
                SELECT 1
                FROM uploaded_documents
                WHERE thread_id = %s
                LIMIT 1
                """,
                (str(thread_id),)
            )

            return cursor.fetchone() is not None


# def thread_document_metadata(thread_id: str) -> dict:
#     return _THREAD_METADATA.get(str(thread_id), {})

def thread_document_metadata(thread_id: str):

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    filename,
                    page_count,
                    chunk_count
                FROM uploaded_documents
                WHERE thread_id = %s
                ORDER BY uploaded_at DESC
                LIMIT 1
                """,
                (str(thread_id),)
            )

            row = cursor.fetchone()

    if not row:
        return {}

    return {
        "filename": row[0],
        "documents": row[1],
        "chunks": row[2],
    }


def _get_retriever(thread_id: Optional[str]):

    print("RETRIEVER THREAD:", thread_id)

    if not thread_id:
        return None
    
    vector_store = get_vector_store()

    return vector_store.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 5,
            "fetch_k": 20,
            "filter": {
                "thread_id": str(thread_id)
            }
        }
    )


def ingest_pdf(file_bytes: bytes, thread_id: str, filename: Optional[str] = None) -> dict:

    '''Build a retirever for the uploaded pdf and store it for the thread.
    returns a summary dict that can be surfaced in the UI
    Ingest a PDF file, split it into chunks, create embeddings, and store in vector store'''
    

    # print("INGEST THREAD:", thread_id)
    


    if not file_bytes:
        raise ValueError("No bytes received for ingestion.")

    thread_id = str(thread_id)


    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    ) as temp_file:

        temp_file.write(file_bytes)
        temp_path = temp_file.name

    try:

        loader = PyPDFLoader(temp_path)
        docs = loader.load()


        if not docs:
            raise ValueError(
                "PDF contains no readable text."
            )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150,
            separators=[
                "\n\n",
                "\n",
                ". ",
                " ",
                ""
            ]
        )

        chunks = splitter.split_documents(docs)

        if not chunks:
            raise ValueError(
                "Unable to extract content from this PDF."
            )

        actual_filename = (
            filename or os.path.basename(temp_path)
        )

        vector_store = get_vector_store()

        for chunk in chunks:

            chunk.metadata.update(
                {
                    "thread_id": thread_id,
                    "filename": actual_filename,
                    "source": "pdf",
                    "page": chunk.metadata.get(
                        "page",
                        0
                    ),
                }
            )

        vector_store.add_documents(chunks)

        with psycopg.connect(db_url) as conn:
            
            with conn.cursor() as cursor:

                page_count = len(
                                set(
                                    chunk.metadata.get("page", 0)
                                    for chunk in chunks
                                )
                            )
                cursor.execute(
                    """
                    INSERT INTO uploaded_documents
                    (
                        thread_id,
                        user_email,
                        filename,
                        page_count,
                        chunk_count
                    )
                    VALUES (%s,%s,%s,%s,%s)
                    """,
                    (
                        thread_id,
                        st.session_state['email'],
                        actual_filename,
                        page_count,
                        len(chunks)
                    )
                )

                conn.commit()

        return {
            "filename": actual_filename,
            "documents": page_count,
            "chunks": len(chunks),
        }

    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass
