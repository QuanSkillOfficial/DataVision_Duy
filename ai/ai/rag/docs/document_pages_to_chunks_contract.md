# Document Pages to Chunks Contract

**Data Flow**: Duy's `document_pages.jsonl` → Lap's chunks

## Input: document_pages.jsonl (from Duy)

Expected format (one JSON per line):

```json
{
  "document_id": "doc_001",
  "file_name": "sample_pdf.pdf",
  "page_number": 1,
  "text": "Page content...",
  "character_count": 2650,
  "is_empty": false
}
```

**Fields:**
- `document_id`: Unique identifier for the source document
- `file_name`: Original PDF filename
- `page_number`: Page number within the document
- `text`: Extracted text content from the page
- `character_count`: Length of extracted text
- `is_empty`: Boolean indicating if page had no text

## Processing: Chunking (in document_loader.py)

```python
from rag.document_loader import load_document_pages_jsonl, pages_to_chunks

# Load Duy's output
pages = load_document_pages_jsonl("path/to/document_pages.jsonl")

# Convert to chunks for RAG
chunks = pages_to_chunks(pages, chunk_size=512, overlap=50)
```

**Logic:**
1. Load all pages from JSONL
2. Skip empty pages (`is_empty=true`)
3. For each non-empty page:
   - Split into chunks of specified size with overlap
   - Preserve page metadata in each chunk
   - Generate page-aware chunk IDs

## Output: Chunks (for RAG pipeline)

Each chunk preserves page-level metadata:

```json
{
  "document_id": "doc_001",
  "chunk_id": "doc_001_page_1_chunk_000",
  "chunk_text": "Page content...",
  "chunk_index": 0,
  "start_char": 0,
  "end_char": 512,
  "metadata": {
    "file_name": "sample_pdf.pdf",
    "page_number": 1,
    "source": "sample_pdf.pdf",
    "character_count": 2650
  }
}
```

**Fields:**
- `document_id`: From Duy's input (preserved)
- `chunk_id`: Format: `{document_id}_page_{page_number}_chunk_{index:03d}`
- `chunk_text`: Actual text content
- `chunk_index`: Position within the page
- `start_char` / `end_char`: Character offsets within original page
- `metadata.page_number`: Page number from Duy's output
- `metadata.source`: File name for citations

## Integration Points

### In RAG Pipeline (rag_pipeline.py)

```python
from rag.document_loader import load_document_pages_jsonl, pages_to_chunks
from rag.rag_pipeline import RAGPipeline

# Load documents
pages = load_document_pages_jsonl("document_pages.jsonl")
chunks = pages_to_chunks(pages)

# Ingest into RAG
pipeline = RAGPipeline()

# Create a synthetic document with all chunks
full_text = "\n".join(c["chunk_text"] for c in chunks)
result = pipeline.ingest_document(
    text=full_text,
    document_id=chunks[0]["document_id"],
    metadata={"source": chunks[0]["metadata"]["file_name"]}
)
```

### Retrieval Preserves Metadata

When retrieving, each result includes:

```json
{
  "chunk_id": "doc_001_page_1_chunk_000",
  "document_id": "doc_001",
  "chunk_text": "...",
  "page_number": 1,
  "metadata": {
    "source": "sample_pdf.pdf",
    "page_number": 1
  },
  "score": 0.87
}
```

This allows downstream services (Phi's chatbot) to:
- Show which page the answer came from
- Filter by document or page
- Generate citations with page numbers

## Validation

Use `DocumentLoader.validate_pages()` to check:

```python
from rag.document_loader import DocumentLoader

pages = DocumentLoader.load_document_pages_jsonl("document_pages.jsonl")
stats = DocumentLoader.validate_pages(pages)

print(f"Total pages: {stats['total_pages']}")
print(f"Non-empty pages: {stats['non_empty_pages']}")
print(f"Total characters: {stats['total_characters']}")
print(f"Valid: {stats['is_valid']}")
```

## Error Handling

- **FileNotFoundError**: If document_pages.jsonl path is invalid
- **json.JSONDecodeError**: If a line in JSONL is malformed (warning logged, line skipped)
- **Empty pages**: Automatically skipped during chunking
- **Missing fields**: Defaults provided (e.g., "unknown" for missing file_name)

## Storage in pgvector

Chunks are stored in the `document_chunks` table with all metadata preserved:

```sql
INSERT INTO document_chunks (
    chunk_id,
    document_id,
    chunk_text,
    embedding,
    page_number,
    metadata
)
VALUES ('doc_001_page_1_chunk_000', 'doc_001', '...', [embeddings], 1, {...})
```

This enables Phi's dashboard to:
- Query by document_id
- Filter by page_number  
- Show source and page in retrieval results
- Track which PDF page a fact came from
