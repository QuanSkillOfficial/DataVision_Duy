"""
Document Loader - Loads documents from various formats

Handles loading Duy's document_pages.jsonl format (PDF page-level extraction)
and converts them to chunks with proper metadata for the RAG pipeline.
"""

import json
import os
from typing import List, Dict, Optional, Iterator
from pathlib import Path


class DocumentLoader:
    """Loads documents from various formats and prepares them for RAG."""
    
    @staticmethod
    def load_document_pages_jsonl(path: str) -> List[Dict]:
        """
        Load document pages from JSONL format (Duy's PDF output).
        
        Expected format for each line:
        {
            "document_id": "doc_001",
            "file_name": "sample_pdf.pdf",
            "page_number": 1,
            "text": "...",
            "character_count": 2650,
            "is_empty": false
        }
        
        Args:
            path: Path to document_pages.jsonl file
        
        Returns:
            List of page dictionaries
        
        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If line is not valid JSON
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Document file not found: {path}")
        
        pages = []
        
        with open(path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                
                try:
                    page = json.loads(line)
                    page_text = page.get("text") or page.get("page_text") or page.get("page_content") or ""
                    page["text"] = page_text
                    page.setdefault("page_text", page_text)
                    pages.append(page)
                except json.JSONDecodeError as e:
                    print(f"Warning: Could not parse line {line_num}: {e}")
                    continue
        
        return pages
    
    @staticmethod
    def load_document_pages_jsonl_streaming(path: str) -> Iterator[Dict]:
        """
        Stream document pages from JSONL (memory-efficient for large files).
        
        Args:
            path: Path to document_pages.jsonl file
        
        Yields:
            Page dictionaries one at a time
        
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Document file not found: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    page = json.loads(line)
                    page_text = page.get("text") or page.get("page_text") or page.get("page_content") or ""
                    page["text"] = page_text
                    page.setdefault("page_text", page_text)
                    yield page
                except json.JSONDecodeError as e:
                    print(f"Warning: Could not parse line {line_num}: {e}")
                    continue
    
    @staticmethod
    def pages_to_chunks(
        pages: List[Dict],
        chunk_size: int = 512,
        overlap: int = 50
    ) -> List[Dict]:
        """
        Convert pages to chunks while preserving page-level metadata.
        
        Creates chunks with structure:
        {
            "document_id": "doc_001",
            "chunk_id": "doc_001_page_1_chunk_000",
            "chunk_text": "...",
            "metadata": {
                "file_name": "sample_pdf.pdf",
                "page_number": 1,
                "source": "sample_pdf.pdf"
            }
        }
        
        Args:
            pages: List of page dictionaries from document_pages.jsonl
            chunk_size: Maximum characters per chunk
            overlap: Overlap between chunks
        
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        
        for page in pages:
            # Skip empty pages
            if page.get("is_empty", False):
                continue
            
            # Extract page info
            document_id = page.get("document_id", "unknown")
            file_name = page.get("file_name", "unknown")
            page_number = page.get("page_number", 1)
            text = page.get("text", "")
            
            if not text:
                continue
            
            # Create metadata for this page
            metadata = {
                "file_name": file_name,
                "page_number": page_number,
                "source": file_name,  # For citations
                "character_count": len(text)
            }
            
            # Chunk the page text
            start = 0
            chunk_num = 0
            
            while start < len(text):
                end = min(start + chunk_size, len(text))
                chunk_text = text[start:end]
                
                # Create chunk ID including page number
                chunk_id = f"{document_id}_page_{page_number}_chunk_{chunk_num:03d}"
                
                chunk_dict = {
                    "document_id": document_id,
                    "chunk_id": chunk_id,
                    "chunk_text": chunk_text,
                    "chunk_index": chunk_num,
                    "start_char": start,
                    "end_char": end,
                    "metadata": metadata.copy()
                }
                
                chunks.append(chunk_dict)
                
                # Move forward with overlap
                start = end - overlap if chunk_num < (len(text) - 1) // chunk_size else end
                chunk_num += 1
        
        return chunks
    
    @staticmethod
    def load_text_file(path: str, document_id: Optional[str] = None) -> Dict:
        """
        Load a plain text file.
        
        Args:
            path: Path to text file
            document_id: Optional document identifier (uses filename if None)
        
        Returns:
            Dictionary with document info
        
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        
        file_name = os.path.basename(path)
        doc_id = document_id or file_name.replace('.', '_')
        
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        return {
            "document_id": doc_id,
            "file_name": file_name,
            "text": text,
            "metadata": {
                "source": file_name,
                "file_path": os.path.abspath(path)
            }
        }
    
    @staticmethod
    def validate_pages(pages: List[Dict]) -> Dict:
        """
        Validate document pages and return statistics.
        
        Args:
            pages: List of page dictionaries
        
        Returns:
            Dictionary with validation results
        """
        total_pages = len(pages)
        empty_pages = sum(1 for p in pages if p.get("is_empty", False))
        total_chars = sum(len(p.get("text", "")) for p in pages)
        unique_documents = len(set(p.get("document_id") for p in pages))
        unique_files = len(set(p.get("file_name") for p in pages))
        
        return {
            "total_pages": total_pages,
            "empty_pages": empty_pages,
            "non_empty_pages": total_pages - empty_pages,
            "total_characters": total_chars,
            "unique_documents": unique_documents,
            "unique_files": unique_files,
            "is_valid": total_pages > 0 and (total_pages - empty_pages) > 0
        }


def load_document_pages_jsonl(path: str) -> List[Dict]:
    """
    Functional interface to load document pages from JSONL.
    
    Args:
        path: Path to document_pages.jsonl file
    
    Returns:
        List of page dictionaries
    """
    return DocumentLoader.load_document_pages_jsonl(path)


def pages_to_chunks(
    pages: List[Dict],
    chunk_size: int = 512,
    overlap: int = 50
) -> List[Dict]:
    """
    Functional interface to convert pages to chunks.
    
    Args:
        pages: List of page dictionaries
        chunk_size: Maximum characters per chunk
        overlap: Overlap between chunks
    
    Returns:
        List of chunk dictionaries
    """
    return DocumentLoader.pages_to_chunks(pages, chunk_size, overlap)


if __name__ == "__main__":
    # Test the document loader
    print("=== Testing DocumentLoader ===\n")
    
    # Example: Create sample data
    sample_pages = [
        {
            "document_id": "doc_001",
            "file_name": "sample_pdf.pdf",
            "page_number": 1,
            "text": "Machine learning is a field of artificial intelligence that uses statistical techniques. " * 10,
            "character_count": 900,
            "is_empty": False
        },
        {
            "document_id": "doc_001",
            "file_name": "sample_pdf.pdf",
            "page_number": 2,
            "text": "Deep learning is part of a broader family of machine learning methods. " * 10,
            "character_count": 700,
            "is_empty": False
        }
    ]
    
    # Test validation
    print("Validating pages...")
    stats = DocumentLoader.validate_pages(sample_pages)
    print(f" Pages are valid: {stats['is_valid']}")
    print(f"  Total pages: {stats['total_pages']}")
    print(f"  Total characters: {stats['total_characters']}")
    print(f"  Unique documents: {stats['unique_documents']}\n")
    
    # Test conversion to chunks
    print("Converting pages to chunks...")
    chunks = DocumentLoader.pages_to_chunks(sample_pages, chunk_size=100, overlap=10)
    print(f" Created {len(chunks)} chunks")
    print(f"  Sample chunk IDs: {[c['chunk_id'] for c in chunks[:3]]}\n")
    
    # Show chunk details
    print("Sample chunk:")
    if chunks:
        chunk = chunks[0]
        print(f"  ID: {chunk['chunk_id']}")
        print(f"  Document: {chunk['document_id']}")
        print(f"  Page: {chunk['metadata']['page_number']}")
        print(f"  Text preview: {chunk['chunk_text'][:80]}...")
