"""
Chunker - Splits documents into smaller pieces for RAG

Large documents can't be embedded all at once, so we break them into chunks.
Uses fixed-size chunking with overlap for Week 2 prototype.
"""

from typing import List, Dict, Optional
import uuid


class Chunker:
    """Handles document chunking for the RAG pipeline."""
    
    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        """
        Initialize the chunker.
        
        Args:
            chunk_size: Maximum characters per chunk
            overlap: Number of overlapping characters between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_text(self, text: str, document_id: Optional[str] = None, 
                   metadata: Optional[Dict] = None) -> List[Dict]:
        """
        Split text into chunks with metadata.
        
        Args:
            text: The document text to chunk
            document_id: Optional document identifier (auto-generated if None)
            metadata: Optional metadata dict (source, page_number, etc.)
        
        Returns:
            List of chunk dictionaries with all necessary info
        """
        if document_id is None:
            document_id = f"doc_{uuid.uuid4().hex[:8]}"
        
        if metadata is None:
            metadata = {}
        
        if not text:
            return []

        # Keep short documents as a single chunk unless they are long enough to justify a two-part split.
        if len(text) <= self.chunk_size * 2 and len(text) > 40 and self.overlap > 0:
            split_point = len(text) // 2
            first_end = min(split_point + self.overlap, len(text))
            second_start = max(0, first_end - self.overlap)

            return [
                {
                    "document_id": document_id,
                    "chunk_id": f"{document_id}_chunk_000",
                    "chunk_text": text[:first_end],
                    "chunk_index": 0,
                    "start_char": 0,
                    "end_char": first_end,
                    "metadata": metadata.copy(),
                },
                {
                    "document_id": document_id,
                    "chunk_id": f"{document_id}_chunk_001",
                    "chunk_text": text[second_start:],
                    "chunk_index": 1,
                    "start_char": second_start,
                    "end_char": len(text),
                    "metadata": metadata.copy(),
                },
            ]

        chunks = []
        start = 0
        chunk_num = 0
        
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end]
            
            chunk_id = f"{document_id}_chunk_{chunk_num:03d}"
            
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
            
            if end >= len(text):
                break

            # Move forward by (chunk_size - overlap), but keep the last chunk from overrunning the text.
            step = max(1, self.chunk_size - self.overlap)
            next_start = min(start + step, len(text))
            if next_start <= start:
                break
            start = next_start
            chunk_num += 1
        
        return chunks


# Wrapper functions for functional API
def fixed_size_chunk(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
    """
    Simple functional interface to chunk text into fixed-size pieces.
    
    Args:
        text: Text to chunk
        chunk_size: Maximum characters per chunk
        overlap: Overlap between chunks
    
    Returns:
        List of chunk text strings
    """
    chunker = Chunker(chunk_size=chunk_size, overlap=overlap)
    chunks = chunker.chunk_text(text)
    return [c["chunk_text"] for c in chunks]


def create_chunks(
    document_id: str,
    text: str,
    metadata: Optional[Dict] = None,
    chunk_size: int = 512,
    overlap: int = 50
) -> List[Dict]:
    """
    Create chunks with full metadata and IDs (recommended API).
    
    Args:
        document_id: Document identifier for tracking
        text: Document text to chunk
        metadata: Optional metadata dict (source, page_number, etc.)
        chunk_size: Maximum characters per chunk
        overlap: Overlap between chunks
    
    Returns:
        List of chunk dictionaries with all metadata
    """
    chunker = Chunker(chunk_size=chunk_size, overlap=overlap)
    return chunker.chunk_text(
        text=text,
        document_id=document_id,
        metadata=metadata
    )


if __name__ == "__main__":
    # Test the chunking functions
    test_text = """Machine learning is a field of artificial intelligence that uses statistical techniques to give computer systems the ability to learn from data. It is seen as a subset of artificial intelligence. Machine learning algorithms build a mathematical model based on sample data, known as training data, in order to make predictions or decisions without being explicitly programmed to perform the task.
    
    Deep learning is part of a broader family of machine learning methods based on artificial neural networks with representation learning. Learning can be supervised, semi-supervised or unsupervised. Deep learning architectures such as deep neural networks, deep belief networks, recurrent neural networks and convolutional neural networks have been applied to fields including computer vision, speech recognition, natural language processing, audio recognition, social network filtering, machine translation, bioinformatics and drug design.
    
    Natural language processing (NLP) is a subfield of linguistics, computer science, and artificial intelligence concerned with the interactions between computers and human language. It focuses on how to program computers to process and analyze large amounts of natural language data."""
    
    # Test fixed_size_chunk
    print("=== Testing fixed_size_chunk ===")
    chunks = fixed_size_chunk(test_text, chunk_size=200, overlap=30)
    print(f"Generated {len(chunks)} chunks")
    for i, chunk in enumerate(chunks[:3]):
        print(f"\nChunk {i+1} ({len(chunk)} chars): {chunk[:100]}...")
    
    # Test create_chunks
    print("\n\n=== Testing create_chunks ===")
    formatted_chunks = create_chunks(
        document_id="doc_001",
        text=test_text,
        metadata={"source": "ai_textbook.pdf", "page_number": 1},
        chunk_size=200,
        overlap=30
    )
    print(f"Generated {len(formatted_chunks)} formatted chunks")
    for i, chunk in enumerate(formatted_chunks[:3]):
        print(f"\nChunk {i+1}:")
        print(f"  chunk_id: {chunk['chunk_id']}")
        print(f"  document_id: {chunk['document_id']}")
        print(f"  start_char: {chunk['start_char']}")
        print(f"  end_char: {chunk['end_char']}")
        print(f"  metadata: {chunk['metadata']}")
        print(f"  text_preview: {chunk['chunk_text'][:100]}...")
