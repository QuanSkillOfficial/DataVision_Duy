"""Load Duy document_pages.jsonl into the pgvector-backed document_chunks table."""

import argparse
import json
import time
import sys
from pathlib import Path
from typing import List, Dict, Optional
import os

try:
    from .document_loader import DocumentLoader
    from .embedder import Embedder
    from .vector_store import VectorStore, resolve_document_db_id
except ImportError:  # pragma: no cover - direct script execution fallback
    from document_loader import DocumentLoader
    from embedder import Embedder
    from vector_store import VectorStore, resolve_document_db_id


def load_and_ingest(
    document_pages_path: str,
    document_external_id: str,
    chunk_size: int = 512,
    overlap: int = 50,
    connection_string: Optional[str] = None,
    prediction_metadata: Optional[Dict] = None,
    skip_duplicates: bool = True,
    output_result_path: Optional[str] = None,
) -> Dict:
    """
    Load document pages, chunk them, generate embeddings, and insert into pgvector.
    
    Args:
        document_pages_path: Path to document_pages.jsonl file
        document_external_id: External document ID for resolution
        chunk_size: Character size for chunks
        overlap: Character overlap between chunks
        connection_string: Database connection string
        prediction_metadata: Optional prediction metadata to include
        skip_duplicates: Whether to skip duplicate chunks
        output_result_path: Optional path to write result JSON
    
    Returns:
        Dictionary with insertion results and statistics
    """
    start_total = time.time()
    result = {
        "status": "pending",
        "document_external_id": document_external_id,
        "document_db_id": None,
        "pages_loaded": 0,
        "non_empty_pages": 0,
        "empty_pages_skipped": 0,
        "total_characters": 0,
        "chunks_created": 0,
        "chunks_inserted": 0,
        "duplicate_chunks_skipped": 0,
        "embeddings_generated": 0,
        "embedding_dimension": 384,
        "insertion_time_ms": 0,
        "total_time_ms": 0,
        "errors": []
    }
    
    try:
        # Step 1: Validate input file
        if not Path(document_pages_path).exists():
            raise FileNotFoundError(f"Document pages file not found: {document_pages_path}")
        
        # Step 2: Load and validate pages
        print(f"Loading document pages from {document_pages_path}...")
        pages = DocumentLoader.load_document_pages_jsonl(document_pages_path)
        validation = DocumentLoader.validate_pages(pages)
        
        result["pages_loaded"] = validation["total_pages"]
        result["non_empty_pages"] = validation["non_empty_pages"]
        result["empty_pages_skipped"] = validation["empty_pages"]
        result["total_characters"] = validation["total_characters"]
        
        if not validation["is_valid"]:
            raise ValueError(f"Page validation failed: {validation}")
        
        print(f"Loaded {validation['total_pages']} pages ({validation['non_empty_pages']} non-empty)")
        
        # Step 3: Convert to chunks
        print("Converting pages to chunks...")
        chunks = DocumentLoader.pages_to_chunks(pages, chunk_size=chunk_size, overlap=overlap)
        result["chunks_created"] = len(chunks)
        print(f"Created {len(chunks)} chunks")
        
        # Step 4: Generate embeddings
        print("Generating embeddings...")
        embedder = Embedder()
        texts = [chunk["chunk_text"] for chunk in chunks]
        embeddings = embedder.embed(texts)
        result["embeddings_generated"] = len(embeddings)
        result["embedding_dimension"] = embedder.get_embedding_dimension()
        print(f"Generated {len(embeddings)} embeddings (dimension: {result['embedding_dimension']})")
        
        # Step 5: Connect to database
        print("Connecting to pgvector database...")
        vector_store = VectorStore(use_pgvector=True, connection_string=connection_string)
        if not getattr(vector_store, "connection", None):
            raise RuntimeError("Unable to connect to pgvector - check connection string")
        
        # Step 6: Resolve document_external_id to document_db_id
        print(f"Resolving document_external_id: {document_external_id}")
        document_db_id = resolve_document_db_id(vector_store.connection, document_external_id)
        result["document_db_id"] = document_db_id
        print(f"Resolved to document_db_id: {document_db_id}")
        # Capture existing rows/chunk ids for this document so we can report and remove stale chunks
        try:
            cursor = vector_store.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM document_chunks WHERE document_id = %s", (document_db_id,))
            rows_before = cursor.fetchone()[0]
            cursor.execute("SELECT chunk_id FROM document_chunks WHERE document_id = %s", (document_db_id,))
            existing_chunk_ids = {row[0] for row in cursor.fetchall()}
            cursor.close()
        except Exception:
            rows_before = 0
            existing_chunk_ids = set()
        result["rows_before"] = rows_before
        print(f"Existing rows for document {document_db_id}: {rows_before}")
        
        # Step 7: Prepare chunks with metadata
        print("Preparing chunks for insertion...")
        for chunk in chunks:
            chunk["document_external_id"] = document_external_id
            chunk["document_id_fk"] = document_db_id  # For pgvector insertion
            chunk.setdefault("metadata", {})
            chunk["metadata"]["document_external_id"] = document_external_id
            if prediction_metadata:
                chunk["metadata"].update(prediction_metadata)
        
        # Step 8: Check for duplicates if requested
        duplicate_count = 0
        if skip_duplicates:
            print("Checking for duplicate chunks...")
            cursor = vector_store.connection.cursor()
            for chunk in chunks:
                cursor.execute(
                    "SELECT chunk_id FROM document_chunks WHERE chunk_id = %s",
                    (chunk["chunk_id"],)
                )
                if cursor.fetchone():
                    duplicate_count += 1
            cursor.close()
            result["duplicate_chunks_skipped"] = duplicate_count
            print(f"Found {duplicate_count} duplicate chunks")
            
            if duplicate_count > 0:
                # Filter out duplicates
                existing_chunk_ids = set()
                cursor = vector_store.connection.cursor()
                cursor.execute("SELECT chunk_id FROM document_chunks WHERE document_id = %s", (document_db_id,))
                for row in cursor.fetchall():
                    existing_chunk_ids.add(row[0])
                cursor.close()
                
                chunks = [c for c in chunks if c["chunk_id"] not in existing_chunk_ids]
                embeddings = embeddings[:len(chunks)]  # Adjust embeddings array
                print(f"Filtered to {len(chunks)} unique chunks")
        
        # Step 9: Insert chunks
        if len(chunks) == 0:
            print("No chunks to insert (all duplicates or empty document)")
            result["status"] = "success"
            result["chunks_inserted"] = 0
        else:
            print(f"Inserting {len(chunks)} chunks into document_chunks...")
            start_insert = time.time()
            inserted_ids = vector_store.add_chunks(chunks, embeddings)
            insertion_time = (time.time() - start_insert) * 1000  # Convert to ms
            result["chunks_inserted"] = len(inserted_ids)
            result["insertion_time_ms"] = round(insertion_time, 2)
            print(f"Inserted {len(inserted_ids)} chunks in {insertion_time:.2f}ms")
            # After insertion, compute rows after and delete any stale chunk_ids that no longer exist in the new set
            try:
                cursor = vector_store.connection.cursor()
                cursor.execute("SELECT chunk_id FROM document_chunks WHERE document_id = %s", (document_db_id,))
                all_after = {row[0] for row in cursor.fetchall()}
                cursor.execute("SELECT COUNT(*) FROM document_chunks WHERE document_id = %s", (document_db_id,))
                rows_after = cursor.fetchone()[0]
                cursor.close()
            except Exception:
                all_after = set()
                rows_after = result.get("chunks_inserted", 0)

            new_chunk_ids = {c["chunk_id"] for c in chunks}
            # Stale IDs are those that existed before but are not present in the new chunk set
            stale_ids = list(existing_chunk_ids - new_chunk_ids)
            deleted = 0
            if stale_ids:
                print(f"Deleting {len(stale_ids)} stale chunk(s) for document {document_db_id}...")
                try:
                    success = vector_store.delete(stale_ids)
                    if success:
                        deleted = len(stale_ids)
                except Exception as e:
                    print(f"Warning: could not delete stale chunks: {e}")

            result["rows_after"] = rows_after
            result["rows_deleted"] = deleted
            result["stale_chunk_ids_deleted"] = stale_ids
        
        # Step 10: Finalize
        result["status"] = "success"
        result["total_time_ms"] = round((time.time() - start_total) * 1000, 2)
        print(f"Total time: {result['total_time_ms']}ms")
        
    except FileNotFoundError as e:
        result["status"] = "error"
        result["errors"].append(f"File not found: {e}")
        print(f"ERROR: {e}")
        
    except ValueError as e:
        result["status"] = "error"
        result["errors"].append(f"Validation error: {e}")
        print(f"ERROR: {e}")
        
    except RuntimeError as e:
        result["status"] = "error"
        result["errors"].append(f"Database error: {e}")
        print(f"ERROR: {e}")
        
    except Exception as e:
        result["status"] = "error"
        result["errors"].append(f"Unexpected error: {e}")
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 11: Write result to file if requested
    if output_result_path:
        try:
            with open(output_result_path, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"Result written to {output_result_path}")
        except Exception as e:
            print(f"Warning: Could not write result to {output_result_path}: {e}")
    
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Load document_pages.jsonl into pgvector")
    parser.add_argument("--document-pages", required=True, help="Path to document_pages.jsonl file")
    parser.add_argument("--document-external-id", required=True, help="External document ID")
    parser.add_argument("--chunk-size", type=int, default=512, help="Character size for chunks")
    parser.add_argument("--overlap", type=int, default=50, help="Character overlap between chunks")
    parser.add_argument("--connection-string", default=None, help="Database connection string")
    parser.add_argument("--skip-duplicates", action="store_true", default=True, help="Skip duplicate chunks")
    parser.add_argument("--no-skip-duplicates", action="store_false", dest="skip_duplicates", help="Do not skip duplicate chunks")
    parser.add_argument("--output-result", default=None, help="Path to write result JSON")
    args = parser.parse_args()

    result = load_and_ingest(
        document_pages_path=args.document_pages,
        document_external_id=args.document_external_id,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        connection_string=args.connection_string,
        skip_duplicates=args.skip_duplicates,
        output_result_path=args.output_result,
    )
    
    print(json.dumps(result, indent=2))
    
    # Exit with error code if status is error
    if result["status"] == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
