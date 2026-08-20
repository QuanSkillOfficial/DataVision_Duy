import numpy as np

from ai.rag.embedder import HashEmbedder, create_embedder


def test_hash_embedder_is_deterministic_and_384_dimensional():
    embedder = HashEmbedder()
    first = embedder.embed_query("What is the DataFlow pipeline?")
    second = embedder.embed_query("What is the DataFlow pipeline?")

    assert first.shape == (384,)
    np.testing.assert_array_equal(first, second)


def test_staging_factory_returns_truthfully_labelled_hash_embedder():
    embedder = create_embedder("staging")

    assert embedder.model_name == "datavision-hashing-384-v1"
    assert embedder.get_embedding_dimension() == 384