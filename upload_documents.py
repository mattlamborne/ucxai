#!/usr/bin/env python3
"""
Easy document upload script for UCX AI Chatbot
Upload PDFs, DOCX, TXT files to train your chatbot

Usage:
    python upload_documents.py file1.pdf file2.pdf folder/*.txt
    python upload_documents.py --folder ./my_docs
"""

import os
import sys
import glob
from dotenv import load_dotenv
from supabase import create_client
from rag_utils import extract_text, store_document

load_dotenv()

def upload_file(supabase, file_path: str):
    """Upload a single file"""
    try:
        # Get file info
        filename = os.path.basename(file_path)
        doc_type = file_path.split('.')[-1].lower()

        print(f"\n📄 Processing: {filename}")

        # Extract text
        content = extract_text(file_path, doc_type)

        if not content or len(content.strip()) < 10:
            print(f"⚠️  Skipping {filename} - no content found")
            return False

        print(f"   Text extracted: {len(content)} characters")

        # Store in database
        document_id = store_document(
            supabase,
            title=filename,
            content=content,
            source=file_path,
            doc_type=doc_type,
            metadata={
                "file_size": os.path.getsize(file_path),
                "file_path": file_path
            }
        )

        print(f"   ✅ Uploaded successfully! ID: {document_id}")
        return True

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("📚 UCX AI Chatbot - Document Upload Tool")
    print("=" * 60)

    # Check for files
    if len(sys.argv) < 2:
        print("\n❌ No files specified!")
        print("\nUsage:")
        print("  python upload_documents.py file1.pdf file2.txt")
        print("  python upload_documents.py --folder ./my_docs")
        print("  python upload_documents.py *.pdf")
        print("\nSupported formats: PDF, DOCX, TXT, MD")
        sys.exit(1)

    # Initialize Supabase
    try:
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Could not connect to Supabase: {e}")
        print("\nMake sure you have:")
        print("1. Run the SQL schema: supabase_rag_schema.sql")
        print("2. Set SUPABASE_URL and SUPABASE_KEY in .env")
        sys.exit(1)

    # Collect files to upload
    files_to_upload = []

    if sys.argv[1] == "--folder":
        if len(sys.argv) < 3:
            print("❌ Please specify a folder path")
            sys.exit(1)

        folder = sys.argv[2]
        for ext in ['*.pdf', '*.txt', '*.docx', '*.md']:
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
        if upload_file(supabase, file_path):
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
    print("🎉 Your chatbot is now trained on your documents!")
    print("   Test it: curl -X POST http://localhost:8000/api/chat \\")
    print('            -H "Content-Type: application/json" \\')
    print('            -d \'{"message": "What do you know about...?"}\'')
    print()

if __name__ == "__main__":
    main()
