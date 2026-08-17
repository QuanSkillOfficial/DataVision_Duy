import numpy as np

from ai.rag.load_document_pages_to_pgvector import _filter_existing_chunk_pairs


def test_duplicate_filter_preserves_chunk_embedding_alignment():
    chunks = [
        {"chunk_id": "existing"},
        {"chunk_id": "new-a"},
        {"chunk_id": "new-b"},
    ]
    embeddings = np.array([[1.0, 0.0], [0.0, 2.0], [3.0, 3.0]])

    filtered_chunks, filtered_embeddings = _filter_existing_chunk_pairs(
        chunks, embeddings, {"existing"}, 2
    )

    assert [chunk["chunk_id"] for chunk in filtered_chunks] == ["new-a", "new-b"]
    assert filtered_embeddings.tolist() == [[0.0, 2.0], [3.0, 3.0]]


def test_all_duplicates_return_an_empty_matrix_with_expected_dimension():
    chunks = [{"chunk_id": "a"}, {"chunk_id": "b"}]
    embeddings = np.ones((2, 384), dtype=np.float32)

    filtered_chunks, filtered_embeddings = _filter_existing_chunk_pairs(
        chunks, embeddings, {"a", "b"}, 384
    )

    assert filtered_chunks == []
    assert filtered_embeddings.shape == (0, 384)
