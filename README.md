# AI Study Assistant & Research Companion

## Overview

An AI-powered Study Assistant that helps users learn concepts, analyze documents, conduct research, and interact with uploaded PDF files through a conversational interface.
link : https://aichatbot-assistant.streamlit.app/

## Features

* User authentication and account management
* Persistent chat threads and conversation history
* PDF upload and document ingestion
* Retrieval-Augmented Generation (RAG) using PGVector
* AI-powered question answering from uploaded documents
* Study note generation
* Quiz and flashcard generation
* Real-time web search capabilities
* Wikipedia knowledge retrieval
* Built-in calculator tool
* Streaming AI responses
* Multi-session chat management

## Tech Stack

### Frontend

* Streamlit

### Backend

* Python
* LangGraph
* LangChain

### Database

* PostgreSQL
* PGVector

### AI & Embeddings

* Groq (Llama 3.3 70B)
* HuggingFace Embeddings
* Sentence Transformers

### Document Processing

* PyMUPDF
* LangChain Document Loaders
* Recursive Character Text Splitter

## Architecture

1. User uploads a PDF document.
2. The document is parsed and split into chunks.
3. Chunks are embedded and stored in PGVector.
4. User queries are routed through LangGraph.
5. Relevant document chunks are retrieved using semantic search.
6. Retrieved context is provided to the LLM for answer generation.
7. Responses are streamed back to the user.

## Future Improvements

* Multi-document upload
* comparison
