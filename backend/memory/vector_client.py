"""Stubbed vector-store client for the future OpsNexus semantic memory layer.

Week 6 will back this with a real ChromaDB collection, embedding documents
locally via a HuggingFace `sentence-transformers` model (no external API
calls needed for embedding) so the Supervisor/Worker agents can retrieve
similar prior documents, answers, and citations at query time. Everything
here is a stub -- no `chromadb` dependency is installed yet.
"""

from typing import Any


class ChromaDBClient:
    """Stub wrapper around a ChromaDB collection.

    Method signatures are shaped for the Week 6 swap-in: callers can be
    written against this interface now, then start getting real results
    once initialize_collection/add_documents/semantic_search are backed by
    an actual ChromaDB PersistentClient + HuggingFace embedding function.
    """

    def __init__(self, collection_name: str = "opsnexus_documents"):
        self.collection_name = collection_name

    def initialize_collection(self) -> None:
        """Create or open the ChromaDB collection for this client.

        Week 6: `chromadb.PersistentClient(...).get_or_create_collection(
        self.collection_name, embedding_function=<HuggingFace embedder>)`.
        """
        raise NotImplementedError("ChromaDB collection initialization is a Week 6 task")

    def add_documents(self, documents: list[dict[str, Any]]) -> None:
        """Embed and upsert documents (id, text, metadata) into the collection.

        Week 6: batches `documents` through the local HuggingFace embedder
        and calls `collection.upsert(...)`.
        """
        raise NotImplementedError("Document embedding/upsert is a Week 6 task")

    def semantic_search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Return the top_k most semantically similar documents to `query`.

        Week 6: embeds `query` locally and calls `collection.query(...)`.
        """
        raise NotImplementedError("Semantic search is a Week 6 task")
