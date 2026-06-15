# pdf-rag-chatbot


A Retrieval-Augmented Generation (RAG) chatbot that allows users to upload PDF documents and ask questions about their content.

## Features

- Upload PDF documents
- Extract text from PDFs
- Split text into chunks
- Generate embeddings using Hugging Face
- Store vectors in FAISS
- Retrieve relevant chunks using similarity search
- Generate answers using Gemini 2.5 Flash
- Streamlit web interface

## Tech Stack

- Python
- Streamlit
- LangChain
- FAISS
- Hugging Face Embeddings
- Gemini 2.5 Flash

## Workflow

PDF → Text Extraction → Chunking → Embeddings → FAISS → Retrieval → Gemini → Answer

## Installation

```bash
pip install -r requirements.txt
streamlit run app.py
```
