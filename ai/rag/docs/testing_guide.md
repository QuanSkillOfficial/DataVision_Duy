# Week 2 RAG Prototype Testing Guide

## Overview

This guide provides step-by-step instructions for testing the Week 2 RAG prototype components.

## Prerequisites

Install required dependencies:

```bash
pip install sentence-transformers numpy scikit-learn
```

## 1. Test Chunker Module

### Run Built-in Tests

```bash
cd c:/Users/WINDOWS/Desktop/folder/ai
python rag\chunker.py
```

### Expected Output

```
=== Testing fixed_size_chunk ===
Generated 5 chunks

Chunk 1 (200 chars): Machine learning is a field of artificial intelligence that uses statistical techniques to give computer systems the ability to learn from data. It is seen as a subset of artificial intelligence. Machine learning algorithms build a mathematical model ...

=== Testing create_chunks ===
Generated 5 formatted chunks

Chunk 1:
  chunk_id: doc_001_chunk_001
  document_id: doc_001
  start_char: 0
  end_char: 200
  metadata: {'source': 'ai_textbook.pdf', 'page_number': 1}
  text_preview: Machine learning is a field of artificial intelligence that uses statistical techniques to give computer systems the ability to learn from data. It is seen as a subset of artificial intelligence...
```

### What It Tests

- Fixed-size chunking with overlap
- Chunk metadata structure
- Character position tracking
- Document ID and chunk ID generation

## 2. Test Embedder Module

### Run Built-in Tests

```bash
python ai/rag/embedder.py
```

### Expected Output

```
Loaded model: sentence-transformers/all-MiniLM-L6-v2
=== Testing embed_texts ===
Shape: (3, 384)
Dimension: 384

=== Testing embed_query ===
Query embedding shape: (384,)

=== Testing similarity ===
Similarity scores: [0.1234 0.8765 0.4567]
Most similar: 'Machine learning is a subset of artificial intelligence.'
```

### What It Tests

- Model loading from HuggingFace
- Text embedding generation
- Query embedding generation
- Embedding dimension verification (384)
- Cosine similarity computation

## 3. Test Retriever Module

### Run Built-in Tests

```bash
python ai/rag/retriever.py
```

### Expected Output

```
Loaded model: sentence-transformers/all-MiniLM-L6-v2
Query: What is deep learning?

Top 3 results:

--- Result 1 ---
Chunk ID: doc_001_chunk_002
Document ID: doc_001
Similarity Score: 0.8234
Metadata: {'source': 'ai_textbook.pdf', 'page_number': 1}
Text: Deep learning is part of a broader family of machine learning methods based on artificial neural networks with representation learning. Learning can be supervised, semi-supervised or unsupervised...

--- Result 2 ---
Chunk ID: doc_001_chunk_001
Document ID: doc_001
Similarity Score: 0.6543
Metadata: {'source': 'ai_textbook.pdf', 'page_number': 1}
Text: Machine learning is a field of artificial intelligence that uses statistical techniques to give computer systems the ability to learn from data...
```

### What It Tests

- Query embedding generation
- Cosine similarity computation
- Top-k retrieval
- Result formatting with metadata
- Similarity score calculation

## 4. Run Jupyter Notebook Demo

### Start Jupyter

```bash
jupyter notebook notebooks/ai_team/chunking_embedding_search_demo.ipynb
```

### Execute Cells Sequentially

1. **Imports** - Load required libraries
2. **Load Sample Text** - Display document length
3. **Chunk Sample Text** - Generate chunks with metadata
4. **Generate Embeddings** - Show embedding shape and dimension
5. **Take User Query** - Display test queries
6. **Generate Query Embedding** - Show query embedding shape
7. **Compute Cosine Similarity** - Display similarity range
8. **Return Top-k Chunks** - Show retrieval function
9. **Show Similarity Scores** - Display results with scores
10. **Test Multiple Queries** - Test all sample queries

### Expected Results

- 7-8 chunks generated from sample text
- Embeddings shape: (n_chunks, 384)
- Query embedding shape: (384,)
- Similarity scores between 0.0 and 1.0
- Top results should be semantically relevant to queries

## 5. End-to-End Integration Test

### Create Test Script

Create `test_week2.py` in the project root:

```python
import sys
sys.path.append('.')

from ai.rag.chunker import create_chunks
from ai.rag.embedder import load_embedding_model, embed_texts, embed_query
from ai.rag.retriever import retrieve_top_k

# Sample document
sample_text = """Machine learning is a field of artificial intelligence that uses statistical techniques to give computer systems the ability to learn from data. It is seen as a subset of artificial intelligence. Machine learning algorithms build a mathematical model based on sample data, known as training data, in order to make predictions or decisions without being explicitly programmed to perform the task.

Deep learning is part of a broader family of machine learning methods based on artificial neural networks with representation learning. Learning can be supervised, semi-supervised or unsupervised. Deep learning architectures such as deep neural networks, deep belief networks, recurrent neural networks and convolutional neural networks have been applied to fields including computer vision, speech recognition, natural language processing, audio recognition, social network filtering, machine translation, bioinformatics and drug design.

Natural language processing (NLP) is a subfield of linguistics, computer science, and artificial intelligence concerned with the interactions between computers and human language. It focuses on how to program computers to process and analyze large amounts of natural language data."""

# Step 1: Chunk
print("=== Step 1: Chunking ===")
chunks = create_chunks(
    document_id="doc_001",
    text=sample_text,
    metadata={"source": "ai_textbook.pdf", "page_number": 1},
    chunk_size=300,
    overlap=30
)
print(f"Generated {len(chunks)} chunks")
print(f"First chunk ID: {chunks[0]['chunk_id']}")
print(f"First chunk text preview: {chunks[0]['chunk_text'][:100]}...")

# Step 2: Embed
print("\n=== Step 2: Embedding ===")
model = load_embedding_model()
chunk_texts = [chunk['chunk_text'] for chunk in chunks]
chunk_embeddings = embed_texts(chunk_texts, model)
print(f"Embeddings shape: {chunk_embeddings.shape}")
print(f"Embedding dimension: {chunk_embeddings.shape[1]}")

# Step 3: Retrieve
print("\n=== Step 3: Retrieval ===")
query = "What is deep learning?"
results = retrieve_top_k(query, chunks, chunk_embeddings, model, top_k=3)

print(f"Query: {query}")
print(f"\nTop {len(results)} results:")
for i, result in enumerate(results, 1):
    print(f"\n--- Result {i} ---")
    print(f"Chunk ID: {result['chunk_id']}")
    print(f"Document ID: {result['document_id']}")
    print(f"Similarity: {result['similarity_score']:.4f}")
    print(f"Metadata: {result['metadata']}")
    print(f"Text: {result['chunk_text'][:100]}...")

print("\n=== Test Complete ===")
print(" Chunking works")
print(" Embedding works")
print(" Retrieval works")
```

### Run Integration Test

```bash
python test_week2.py
```

### Expected Output

```
=== Step 1: Chunking ===
Generated 7 chunks
First chunk ID: doc_001_chunk_001
First chunk text preview: Machine learning is a field of artificial intelligence that uses statistical techniques to give computer systems the ability to learn from data...

=== Step 2: Embedding ===
Loaded model: sentence-transformers/all-MiniLM-L6-v2
Embeddings shape: (7, 384)
Embedding dimension: 384

=== Step 3: Retrieval ===
Query: What is deep learning?

Top 3 results:

--- Result 1 ---
Chunk ID: doc_001_chunk_002
Document ID: doc_001
Similarity: 0.8234
Metadata: {'source': 'ai_textbook.pdf', 'page_number': 1}
Text: Deep learning is part of a broader family of machine learning methods...

--- Result 2 ---
Chunk ID: doc_001_chunk_001
Document ID: doc_001
Similarity: 0.6543
Metadata: {'source': 'ai_textbook.pdf', 'page_number': 1}
Text: Machine learning is a field of artificial intelligence...

=== Test Complete ===
 Chunking works
 Embedding works
 Retrieval works
```

## 6. Verify Evaluation Test Cases

### Check Test Cases File

```bash
type ai\evaluation\retrieval_test_cases.csv
```

### Expected Content

CSV file with 10 test questions, expected chunk IDs, and columns for results.

## 7. Friday Demo Script

### Quick Demo Commands

```bash
# Test all components
python rag/chunker.py
python rag/embedder.py
python rag/retriever.py

# Run integration test
python test_week2.py

# Open notebook for visual demo
jupyter notebook notebooks/ai_team/chunking_embedding_search_demo.ipynb
```




