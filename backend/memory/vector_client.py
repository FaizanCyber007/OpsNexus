"""Local RAG memory layer for OpsNexus.

Extracts text from an uploaded ``Document``, splits it into chunks, embeds the
chunks with a free local HuggingFace sentence-transformer, and stores them in a
per-organization ChromaDB collection so the future Supervisor/Worker agents can
retrieve similar prior documents/answers at query time. No paid APIs are used --
embeddings run entirely on-device via ``sentence-transformers``.

The `langchain`/`chromadb`/`torch` stack is imported lazily inside functions
rather than at module level: those libraries are heavy to import, and this
module is pulled in by `documents.views` at Django startup, so a top-level
import would pay that cost on every server start/reload instead of only when a
document is actually ingested.
"""

import logging
import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

_embeddings: "HuggingFaceEmbeddings | None" = None


def _get_embeddings() -> "HuggingFaceEmbeddings":
    """Lazily construct the shared embedding model (loading it is expensive)."""
    global _embeddings
    if _embeddings is None:
        from langchain_huggingface import HuggingFaceEmbeddings

        _embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    return _embeddings


class ChromaDBClient:
    """Wrapper around a per-organization ChromaDB collection."""

    def __init__(self, collection_name: str = "opsnexus_documents"):
        self.collection_name = collection_name
        self._store = None

    def initialize_collection(self):
        """Create or open the ChromaDB collection for this client."""
        if self._store is None:
            import chromadb
            from django.conf import settings
            from langchain_chroma import Chroma

            self._store = Chroma(
                collection_name=self.collection_name,
                embedding_function=_get_embeddings(),
                persist_directory=str(settings.CHROMA_PERSIST_DIR),
                client_settings=chromadb.config.Settings(anonymized_telemetry=False),
            )
        return self._store

    def add_documents(self, documents: list[dict[str, Any]]) -> None:
        """Embed and upsert documents (id, text, metadata) into the collection."""
        store = self.initialize_collection()
        store.add_texts(
            texts=[doc["text"] for doc in documents],
            metadatas=[doc.get("metadata", {}) for doc in documents],
            ids=[doc["id"] for doc in documents],
        )

    def semantic_search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Return the top_k most semantically similar chunks to `query`."""
        store = self.initialize_collection()
        results = store.similarity_search_with_score(query, k=top_k)
        return [
            {"text": doc.page_content, "metadata": doc.metadata, "distance": score}
            for doc, score in results
        ]


def _get_text_splitter():
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    return RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)


def extract_text(file_path: str) -> str:
    """Extract raw text from a file on disk, dispatching by extension.

    Handles PDFs and Word docs via LangChain loaders; falls back to a plain
    UTF-8 read for other text-bearing files (.txt, .md, .csv, .log, ...).
    Returns an empty string (rather than raising) for undecodable/binary files.
    """
    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".pdf":
        from langchain_community.document_loaders import PyPDFLoader

        pages = PyPDFLoader(file_path).load()
        text = "\n".join(page.page_content for page in pages)
    elif extension == ".docx":
        from langchain_community.document_loaders import Docx2txtLoader

        pages = Docx2txtLoader(file_path).load()
        text = "\n".join(page.page_content for page in pages)
    else:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        except (UnicodeDecodeError, OSError):
            logger.warning(
                "Skipping memory ingestion for %s: not a decodable text file",
                file_path,
            )
            return ""

    return text


def _load_document_text(file_path: str) -> list[str]:
    """Extract and chunk a file's text for embedding/ingestion."""
    text = extract_text(file_path)
    if not text.strip():
        return []

    return _get_text_splitter().split_text(text)


def ingest_document(document: Any) -> None:
    """Embed an uploaded Document's text into its organization's memory collection.

    No-op (with a logged warning) if the document has no file attached or its
    contents can't be extracted as text -- ingestion failures never block the
    rest of the upload/agent pipeline.
    """
    if not document.file:
        logger.warning(
            "Document %s has no attached file, skipping ingestion", document.id
        )
        return

    chunks = _load_document_text(document.file.path)
    if not chunks:
        return

    client = ChromaDBClient(collection_name=f"org_{document.organization_id}")
    client.add_documents(
        [
            {
                "id": f"{document.id}-{i}",
                "text": chunk,
                "metadata": {
                    "document_id": str(document.id),
                    "organization_id": str(document.organization_id),
                    "file_name": os.path.basename(document.file.name),
                },
            }
            for i, chunk in enumerate(chunks)
        ]
    )

    logger.info(
        "Ingested %d chunk(s) from document %s into collection org_%s",
        len(chunks),
        document.id,
        document.organization_id,
    )
