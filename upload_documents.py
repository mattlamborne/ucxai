#!/usr/bin/env python3
"""
Upload documents to Pinecone for UCX AI Chatbot RAG
Supports: PDF, TXT, MD files

Usage:
    python upload_documents.py file1.pdf file2.pdf
    python upload_documents.py --folder ./my_docs
    python upload_documents.py --list
"""

import os
import sys
import glob
import hashlib
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone

load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME", "ucx-chatbot"))

def get_embedding(text: str):
    """Get embedding from OpenAI"""
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small"  # $0.02 per 1M tokens
    )
    return response.data[0].embedding

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200):
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start += chunk_size - overlap
    return chunks

def read_pdf(file_path: str):
    """Read PDF file - requires PyPDF2"""
    try:
        import PyPDF2
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
    except ImportError:
        print("⚠️  PyPDF2 not installed. Install with: pip install PyPDF2")
        return None

def read_text_file(file_path: str):
    """Read text file"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def upload_file(file_path: str):
    """Upload a single file to Pinecone"""
    try:
        file_path = Path(file_path)

        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            return False

        print(f"\n📄 Processing: {file_path.name}")

        # Read file based on extension
        if file_path.suffix.lower() == '.pdf':
            text = read_pdf(file_path)
            if not text:
                return False
        elif file_path.suffix.lower() in ['.txt', '.md']:
            text = read_text_file(file_path)
        else:
            print(f"⚠️  Unsupported file type: {file_path.suffix}")
            return False

        if not text or len(text.strip()) < 10:
            print(f"⚠️  Skipping - no content found")
            return False

        print(f"   Text extracted: {len(text)} characters")

        # Chunk the text
        chunks = chunk_text(text)
        print(f"   Split into {len(chunks)} chunks")

        # Upload each chunk to Pinecone
        source = file_path.name
        vectors = []

        for i, chunk in enumerate(chunks):
            # Create unique ID for this chunk
            chunk_id = hashlib.md5(f"{source}_{i}".encode()).hexdigest()

            # Get embedding
            embedding = get_embedding(chunk)

            # Create vector with metadata
            vectors.append({
                "id": chunk_id,
                "values": embedding,
                "metadata": {
                    "text": chunk,
                    "source": source,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            })

            # Upload in batches of 100
            if len(vectors) >= 100:
                index.upsert(vectors=vectors)
                print(f"   ✅ Uploaded batch of {len(vectors)} chunks")
                vectors = []

        # Upload remaining vectors
        if vectors:
            index.upsert(vectors=vectors)
            print(f"   ✅ Uploaded final batch of {len(vectors)} chunks")

        print(f"✅ Done! {file_path.name} uploaded to Pinecone")
        return True

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def list_documents():
    """List documents in Pinecone index"""
    try:
        stats = index.describe_index_stats()
        print(f"\n📊 Pinecone Index Stats:")
        print(f"   Total vectors: {stats.total_vector_count}")
        print(f"   Dimension: {stats.dimension}")

        if stats.total_vector_count > 0:
            print("\n📄 Documents in index:")
            # Query with a zero vector to get samples
            results = index.query(
                vector=[0.0] * 1536,
                top_k=20,
                include_metadata=True
            )

            sources = set()
            for match in results.matches:
                if match.metadata and 'source' in match.metadata:
                    sources.add(match.metadata['source'])

            for source in sorted(sources):
                print(f"   - {source}")
        else:
            print("\n⚠️  No documents uploaded yet")
    except Exception as e:
        print(f"❌ Error: {e}")

def delete_all():
    """Delete all vectors from index"""
    confirm = input("\n⚠️  Delete ALL documents from Pinecone? (yes/no): ")
    if confirm.lower() == 'yes':
        index.delete(delete_all=True)
        print("✅ All documents deleted from Pinecone")
    else:
        print("❌ Cancelled")

def main():
    print("=" * 60)
    print("📚 UCX AI Chatbot - Pinecone Document Uploader")
    print("=" * 60)

    # Check for special commands
    if len(sys.argv) < 2:
        print("\n❌ No command specified!")
        print("\nUsage:")
        print("  python upload_documents.py file1.pdf file2.txt")
        print("  python upload_documents.py --folder ./my_docs")
        print("  python upload_documents.py --list")
        print("  python upload_documents.py --delete-all")
        print("\nSupported formats: PDF, TXT, MD")
        sys.exit(1)

    # Handle special commands
    if sys.argv[1] == "--list":
        list_documents()
        sys.exit(0)

    if sys.argv[1] == "--delete-all":
        delete_all()
        sys.exit(0)

    # Check environment variables
    if not os.getenv("PINECONE_API_KEY"):
        print("❌ PINECONE_API_KEY not set in .env")
        sys.exit(1)

    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set in .env (needed for embeddings)")
        sys.exit(1)

    print("✅ Connected to Pinecone")

    # Collect files to upload
    files_to_upload = []

    if sys.argv[1] == "--folder":
        if len(sys.argv) < 3:
            print("❌ Please specify a folder path")
            sys.exit(1)

        folder = sys.argv[2]
        for ext in ['*.pdf', '*.txt', '*.md']:
            files_to_upload.extend(glob.glob(os.path.join(folder, ext)))
            files_to_upload.extend(glob.glob(os.path.join(folder, '**', ext), recursive=True))
    else:
        # Expand glob patterns
        for pattern in sys.argv[1:]:
            matching_files = glob.glob(pattern)
            if matching_files:
                files_to_upload.extend(matching_files)
            elif os.path.isfile(pattern):
                files_to_upload.append(pattern)

    if not files_to_upload:
        print("❌ No files found!")
        sys.exit(1)

    # Remove duplicates
    files_to_upload = list(set(files_to_upload))

    print(f"\n📊 Found {len(files_to_upload)} files to upload\n")

    # Upload each file
    success_count = 0
    fail_count = 0

    for file_path in files_to_upload:
        if upload_file(file_path):
            success_count += 1
        else:
            fail_count += 1

    # Summary
    print("\n" + "=" * 60)
    print("📊 UPLOAD SUMMARY")
    print("=" * 60)
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {fail_count}")
    print(f"📁 Total: {len(files_to_upload)}")
    print()

    if success_count > 0:
        print("🎉 Your chatbot is now trained on your documents!")
        print("\n   Test it:")
        print("   curl -X POST https://ucxai-production.up.railway.app/api/chat \\")
        print('        -H "Content-Type: application/json" \\')
        print('        -d \'{"message": "What information do you have?"}\'')
        print()

        # Show current index stats
        list_documents()

if __name__ == "__main__":
    main()
