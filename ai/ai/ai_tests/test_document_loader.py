"""
Tests for DocumentLoader - Week 5

Tests document loading from document_pages.jsonl format.
"""

import json
import os
import tempfile
import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from ai.rag.document_loader import DocumentLoader


def test_load_document_pages_jsonl():
    """Test loading document_pages.jsonl file."""
    # Create temporary JSONL file
    sample_pages = [
        {
            "document_id": "doc_001",
            "file_name": "sample.pdf",
            "page_number": 1,
            "text": "This is page 1 content.",
            "character_count": 22,
            "is_empty": False
        },
        {
            "document_id": "doc_001",
            "file_name": "sample.pdf",
            "page_number": 2,
            "text": "This is page 2 content.",
            "character_count": 22,
            "is_empty": False
        },
        {
            "document_id": "doc_001",
            "file_name": "sample.pdf",
            "page_number": 3,
            "text": "",
            "character_count": 0,
            "is_empty": True
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for page in sample_pages:
            f.write(json.dumps(page) + '\n')
        temp_path = f.name
    
    try:
        # Load pages
        pages = DocumentLoader.load_document_pages_jsonl(temp_path)
        
        # Assertions
        assert len(pages) == 3, f"Expected 3 pages, got {len(pages)}"
        assert pages[0]["document_id"] == "doc_001"
        assert pages[0]["page_number"] == 1
        assert pages[2]["is_empty"] == True
        
        print("✓ test_load_document_pages_jsonl passed")
    finally:
        os.unlink(temp_path)


def test_empty_pages_skipped():
    """Test that empty pages are skipped during chunking."""
    pages = [
        {
            "document_id": "doc_001",
            "file_name": "sample.pdf",
            "page_number": 1,
            "text": "Content here",
            "character_count": 12,
            "is_empty": False
        },
        {
            "document_id": "doc_001",
            "file_name": "sample.pdf",
            "page_number": 2,
            "text": "",
            "character_count": 0,
            "is_empty": True
        },
        {
            "document_id": "doc_001",
            "file_name": "sample.pdf",
            "page_number": 3,
            "text": "More content",
            "character_count": 12,
            "is_empty": False
        }
    ]
    
    chunks = DocumentLoader.pages_to_chunks(pages, chunk_size=100, overlap=10)
    
    # Empty page (page 2) should be skipped
    page_numbers_in_chunks = [c["metadata"]["page_number"] for c in chunks]
    assert 2 not in page_numbers_in_chunks, "Empty page should be skipped"
    assert 1 in page_numbers_in_chunks
    assert 3 in page_numbers_in_chunks
    
    print("✓ test_empty_pages_skipped passed")


def test_validate_pages():
    """Test page validation."""
    pages = [
        {
            "document_id": "doc_001",
            "file_name": "sample.pdf",
            "page_number": 1,
            "text": "Content",
            "character_count": 7,
            "is_empty": False
        },
        {
            "document_id": "doc_001",
            "file_name": "sample.pdf",
            "page_number": 2,
            "text": "",
            "character_count": 0,
            "is_empty": True
        }
    ]
    
    stats = DocumentLoader.validate_pages(pages)
    
    assert stats["total_pages"] == 2
    assert stats["empty_pages"] == 1
    assert stats["non_empty_pages"] == 1
    assert stats["total_characters"] == 7
    assert stats["is_valid"] == True
    
    print("✓ test_validate_pages passed")


def test_chunk_id_preserves_page_number():
    """Test that chunk IDs preserve page numbers."""
    pages = [
        {
            "document_id": "doc_001",
            "file_name": "sample.pdf",
            "page_number": 5,
            "text": "This is a test page with enough content to create multiple chunks.",
            "character_count": 70,
            "is_empty": False
        }
    ]
    
    chunks = DocumentLoader.pages_to_chunks(pages, chunk_size=30, overlap=5)
    
    # All chunks should have page_number in their ID
    for chunk in chunks:
        assert "_page_5_" in chunk["chunk_id"], f"Chunk ID {chunk['chunk_id']} should contain '_page_5_'"
        assert chunk["metadata"]["page_number"] == 5
    
    print("✓ test_chunk_id_preserves_page_number passed")


def test_load_document_pages_jsonl_supports_page_text_field():
    """Test that Duy-style page_text JSONL input is normalized correctly."""
    sample_pages = [
        {
            "document_id": "doc_002",
            "file_name": "duy_report.pdf",
            "page_number": 2,
            "page_text": "Duy style extraction content.",
            "character_count": 30,
            "is_empty": False
        }
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for page in sample_pages:
            f.write(json.dumps(page) + '\n')
        temp_path = f.name

    try:
        pages = DocumentLoader.load_document_pages_jsonl(temp_path)
        assert len(pages) == 1
        assert pages[0]["page_number"] == 2
        assert pages[0]["text"] == "Duy style extraction content."
        chunks = DocumentLoader.pages_to_chunks(pages, chunk_size=20, overlap=2)
        assert chunks, "Expected page_text input to produce at least one chunk"
    finally:
        os.unlink(temp_path)

    print("✓ test_load_document_pages_jsonl_supports_page_text_field passed")


def test_document_loader_total_characters():
    """Test that total characters are calculated correctly."""
    pages = [
        {
            "document_id": "doc_001",
            "file_name": "sample.pdf",
            "page_number": 1,
            "text": "Hello",
            "character_count": 5,
            "is_empty": False
        },
        {
            "document_id": "doc_001",
            "file_name": "sample.pdf",
            "page_number": 2,
            "text": "World",
            "character_count": 5,
            "is_empty": False
        }
    ]
    
    stats = DocumentLoader.validate_pages(pages)
    
    assert stats["total_characters"] == 10
    
    print("✓ test_document_loader_total_characters passed")


def test_document_loader_all_empty_pages():
    """Test validation when all pages are empty."""
    pages = [
        {
            "document_id": "doc_001",
            "file_name": "sample.pdf",
            "page_number": 1,
            "text": "",
            "character_count": 0,
            "is_empty": True
        },
        {
            "document_id": "doc_001",
            "file_name": "sample.pdf",
            "page_number": 2,
            "text": "",
            "character_count": 0,
            "is_empty": True
        }
    ]
    
    stats = DocumentLoader.validate_pages(pages)
    
    assert stats["total_pages"] == 2
    assert stats["empty_pages"] == 2
    assert stats["non_empty_pages"] == 0
    
    print("✓ test_document_loader_all_empty_pages passed")


def test_document_loader_chunk_count():
    """Test that chunk count is reasonable for page content."""
    pages = [
        {
            "document_id": "doc_001",
            "file_name": "sample.pdf",
            "page_number": 1,
            "text": "A" * 200,  # 200 characters
            "character_count": 200,
            "is_empty": False
        }
    ]
    
    chunks = DocumentLoader.pages_to_chunks(pages, chunk_size=50, overlap=10)
    
    # With 200 chars, chunk_size=50, overlap=10, should get multiple chunks
    assert len(chunks) > 1, "Should create multiple chunks from long text"
    
    print("✓ test_document_loader_chunk_count passed")


if __name__ == "__main__":
    test_load_document_pages_jsonl()
    test_empty_pages_skipped()
    test_validate_pages()
    test_chunk_id_preserves_page_number()
    test_load_document_pages_jsonl_supports_page_text_field()
    test_document_loader_total_characters()
    test_document_loader_all_empty_pages()
    test_document_loader_chunk_count()
    print("\n✓ All document_loader tests passed!")
