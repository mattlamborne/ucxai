"""
RAG (Retrieval Augmented Generation) utilities
Processes documents and creates searchable embeddings
"""

import os
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import PyPDF2
import docx
from supabase import Client
import numpy as np

# Initialize embedding model (lightweight and fast)
embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        print(f"Error reading DOCX: {e}")
        return ""

def extract_text_from_txt(file_path: str) -> str:
    """Extract text from TXT file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading TXT: {e}")
        return ""

def extract_text(file_path: str, doc_type: str = None) -> str:
    """Extract text from any supported document type"""
    if doc_type is None:
        doc_type = file_path.split('.')[-1].lower()

    extractors = {
        'pdf': extract_text_from_pdf,
        'docx': extract_text_from_docx,
        'doc': extract_text_from_docx,
        'txt': extract_text_from_txt,
        'md': extract_text_from_txt,
    }

    extractor = extractors.get(doc_type, extract_text_from_txt)
    return extractor(file_path)

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks for better context preservation

    Args:
        text: The text to chunk
        chunk_size: Maximum characters per chunk
        overlap: Characters to overlap between chunks
    """
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size

        # Try to break at sentence boundaries
        if end < text_length:
            # Look for sentence endings
            for punct in ['. ', '! ', '? ', '\n\n']:
                last_punct = text[start:end].rfind(punct)
                if last_punct != -1:
                    end = start + last_punct + len(punct)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap

    return chunks

def create_embeddings(texts: List[str]) -> np.ndarray:
    """Create embeddings for a list of texts"""
    return embedding_model.encode(texts, show_progress_bar=True)

def store_document(
    supabase: Client,
    title: str,
    content: str,
    source: str,
    doc_type: str,
    metadata: Dict[str, Any] = None
) -> str:
    """
    Store a document and its chunks in Supabase

    Returns:
        document_id: UUID of the stored document
    """
    # Store the document
    doc_result = supabase.table("documents").insert({
        "title": title,
        "content": content,
        "source": source,
        "doc_type": doc_type,
        "metadata": metadata or {}
    }).execute()

    document_id = doc_result.data[0]['id']

    # Chunk the document
    chunks = chunk_text(content)
    print(f"Created {len(chunks)} chunks for {title}")

    # Create embeddings for chunks
    embeddings = create_embeddings(chunks)

    # Store chunks with embeddings
    chunk_records = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        chunk_records.append({
            "document_id": document_id,
            "content": chunk,
            "chunk_index": i,
            "embedding": embedding.tolist(),
            "metadata": {"chunk_length": len(chunk)}
        })

    # Insert chunks in batches
    batch_size = 100
    for i in range(0, len(chunk_records), batch_size):
        batch = chunk_records[i:i + batch_size]
        supabase.table("document_chunks").insert(batch).execute()

    print(f"✅ Stored document '{title}' with {len(chunks)} chunks")
    return document_id

def search_similar_chunks(
    supabase: Client,
    query: str,
    top_k: int = 5,
    threshold: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Search for similar document chunks using semantic search

    Args:
        supabase: Supabase client
        query: Search query
        top_k: Number of results to return
        threshold: Similarity threshold (0-1)

    Returns:
        List of matching chunks with metadata
    """
    # Create embedding for the query
    query_embedding = embedding_model.encode([query])[0].tolist()

    # Search using Supabase RPC function
    try:
        result = supabase.rpc(
            'search_documents',
            {
                'query_embedding': query_embedding,
                'match_threshold': threshold,
                'match_count': top_k
            }
        ).execute()

        return result.data
    except Exception as e:
        print(f"Search error: {e}")
        return []

def get_context_for_query(supabase: Client, query: str, top_k: int = 3) -> str:
    """
    Get relevant context from documents for a query

    Returns a formatted string with context to add to the prompt
    """
    results = search_similar_chunks(supabase, query, top_k=top_k)

    if not results:
        return ""

    context_parts = ["Here is relevant information from the knowledge base:\n"]

    for i, result in enumerate(results, 1):
        context_parts.append(f"\n[Source {i}: {result['document_title']}]")
        context_parts.append(f"{result['content']}")
        context_parts.append(f"(Relevance: {result['similarity']:.2%})\n")

    return "\n".join(context_parts)
