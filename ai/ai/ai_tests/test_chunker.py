"""
Tests for Chunker - Week 5

Tests document chunking functionality.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from ai.rag.chunker import Chunker


def test_chunk_text_basic():
    """Test basic text chunking."""
    chunker = Chunker(chunk_size=100, overlap=10)
    
    text = "This is a test document that will be chunked into multiple pieces for testing purposes."
    chunks = chunker.chunk_text(text, document_id="doc_001")
    
    assert len(chunks) > 1, "Should create multiple chunks"
    assert all("chunk_id" in c for c in chunks), "All chunks should have chunk_id"
    assert all("document_id" in c for c in chunks), "All chunks should have document_id"
    
    print("✓ test_chunk_text_basic passed")


def test_chunk_id_format():
    """Test chunk ID format."""
    chunker = Chunker(chunk_size=50, overlap=5)
    
    text = "Test text for chunking with proper ID format verification."
    chunks = chunker.chunk_text(text, document_id="doc_123")
    
    # Check chunk ID format: {document_id}_chunk_{num:03d}
    for i, chunk in enumerate(chunks):
        expected_id = f"doc_123_chunk_{i:03d}"
        assert chunk["chunk_id"] == expected_id, f"Expected {expected_id}, got {chunk['chunk_id']}"
    
    print("✓ test_chunk_id_format passed")


def test_chunk_overlap():
    """Test that chunks have proper overlap."""
    chunker = Chunker(chunk_size=50, overlap=10)
    
    text = "A" * 100  # 100 characters
    chunks = chunker.chunk_text(text, document_id="doc_001")
    
    # With 100 chars and chunk_size=50, overlap=10, we should get 2 chunks
    assert len(chunks) == 2, f"Expected 2 chunks, got {len(chunks)}"
    
    # Check overlap
    chunk1_end = chunks[0]["end_char"]
    chunk2_start = chunks[1]["start_char"]
    overlap = chunk1_end - chunk2_start
    assert overlap == 10, f"Expected overlap of 10, got {overlap}"
    
    print("✓ test_chunk_overlap passed")


def test_chunk_metadata():
    """Test that chunks preserve metadata."""
    chunker = Chunker(chunk_size=100, overlap=10)
    
    metadata = {"source": "test.pdf", "page_number": 1}
    text = "Test document with metadata."
    chunks = chunker.chunk_text(text, document_id="doc_001", metadata=metadata)
    
    for chunk in chunks:
        assert chunk["metadata"]["source"] == "test.pdf"
        assert chunk["metadata"]["page_number"] == 1
    
    print("✓ test_chunk_metadata passed")


def test_chunk_start_end_chars():
    """Test start_char and end_char positions."""
    chunker = Chunker(chunk_size=50, overlap=5)
    
    text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"  # 26 chars
    chunks = chunker.chunk_text(text, document_id="doc_001")
    
    # First chunk should start at 0
    assert chunks[0]["start_char"] == 0
    assert chunks[0]["end_char"] == 26  # Entire text
    
    # Chunk text should match start/end positions
    for chunk in chunks:
        expected_text = text[chunk["start_char"]:chunk["end_char"]]
        assert chunk["chunk_text"] == expected_text
    
    print("✓ test_chunk_start_end_chars passed")


def test_chunk_single_chunk():
    """Test that short text creates single chunk."""
    chunker = Chunker(chunk_size=1000, overlap=10)
    
    text = "Short text."
    chunks = chunker.chunk_text(text, document_id="doc_001")
    
    assert len(chunks) == 1, "Short text should create single chunk"
    
    print("✓ test_chunk_single_chunk passed")


def test_chunk_empty_text():
    """Test that empty text creates no chunks."""
    chunker = Chunker(chunk_size=100, overlap=10)
    
    text = ""
    chunks = chunker.chunk_text(text, document_id="doc_001")
    
    assert len(chunks) == 0, "Empty text should create no chunks"
    
    print("✓ test_chunk_empty_text passed")


def test_chunk_zero_overlap():
    """Test chunking with zero overlap."""
    chunker = Chunker(chunk_size=50, overlap=0)
    
    text = "A" * 100
    chunks = chunker.chunk_text(text, document_id="doc_001")
    
    # With 100 chars and chunk_size=50, overlap=0, we should get 2 chunks
    assert len(chunks) == 2
    
    # Check no overlap
    chunk1_end = chunks[0]["end_char"]
    chunk2_start = chunks[1]["start_char"]
    assert chunk1_end == chunk2_start, "Should have no overlap"
    
    print("✓ test_chunk_zero_overlap passed")


def test_chunk_large_overlap():
    """Test chunking with large overlap."""
    chunker = Chunker(chunk_size=50, overlap=25)
    
    text = "A" * 100
    chunks = chunker.chunk_text(text, document_id="doc_001")
    
    # Check overlap
    chunk1_end = chunks[0]["end_char"]
    chunk2_start = chunks[1]["start_char"]
    overlap = chunk1_end - chunk2_start
    assert overlap == 25, f"Expected overlap of 25, got {overlap}"
    
    print("✓ test_chunk_large_overlap passed")


def test_chunk_document_id_preserved():
    """Test that document_id is preserved in all chunks."""
    chunker = Chunker(chunk_size=50, overlap=10)
    
    text = "A" * 100
    chunks = chunker.chunk_text(text, document_id="doc_test_123")
    
    for chunk in chunks:
        assert chunk["document_id"] == "doc_test_123"
    
    print("✓ test_chunk_document_id_preserved passed")


if __name__ == "__main__":
    test_chunk_text_basic()
    test_chunk_id_format()
    test_chunk_overlap()
    test_chunk_metadata()
    test_chunk_start_end_chars()
    test_chunk_single_chunk()
    test_chunk_empty_text()
    test_chunk_zero_overlap()
    test_chunk_large_overlap()
    test_chunk_document_id_preserved()
    print("\n✓ All chunker tests passed!")
