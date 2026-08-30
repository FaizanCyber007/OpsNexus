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
import tempfile
import threading
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

_embeddings: "HuggingFaceEmbeddings | None" = None
_embeddings_lock = threading.Lock()


def _get_embeddings() -> "HuggingFaceEmbeddings":
    """Lazily construct the shared embedding model (loading it is expensive).

    Each document upload runs on its own background thread, so this can be
    called concurrently; double-checked locking ensures only one thread ever
    constructs the model and every caller shares that one cached instance.
    """
    global _embeddings
    if _embeddings is None:
        with _embeddings_lock:
            if _embeddings is None:
                from langchain_huggingface import HuggingFaceEmbeddings

                _embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    return _embeddings


def attempt_pending_cleanup(pending: Any) -> bool:
    """Try to delete one PendingVectorCleanup's vectors from Chroma.

    On success the record is deleted (fully resolved). On failure the
    record's attempt count/last_error are updated and it is kept for a later
    retry (via the `retry_vector_cleanup` management command) instead of the
    failure being silently logged and discarded.

    Neither the ChromaDB deletion nor the record persistence step is allowed
    to propagate an exception -- a failure in one record must never halt the
    processing of subsequent retry records.
    """
    try:
        client = ChromaDBClient(
            collection_name=get_organization_collection_name(pending.organization_id)
        )
        client.delete_by_document_id(str(pending.document_id))
    except Exception as exc:
        pending.attempts += 1
        pending.last_error = str(exc)
        try:
            pending.save(update_fields=["attempts", "last_error"])
        except Exception as save_exc:
            logger.exception(
                "Failed to persist failure state for document %s cleanup record: %s",
                pending.document_id,
                save_exc,
            )
        logger.exception(
            "Failed to remove ChromaDB vectors for document %s (attempt %d)",
            pending.document_id,
            pending.attempts,
        )
        return False
    else:
        try:
            pending.delete()
        except Exception as del_exc:
            logger.exception(
                "Failed to delete cleanup record for document %s after successful "
                "ChromaDB deletion: %s",
                pending.document_id,
                del_exc,
            )
            return False
        return True


def get_organization_collection_name(organization_id: Any) -> str:
    """The ChromaDB collection name for one organization's document vectors.

    Shared naming contract between where vectors are written (`ingest_document`)
    and where they're deleted (`documents.signals`) -- both must agree on this
    string or deletes silently miss the collection they should be clearing.
    """
    return f"org_{organization_id}"


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

    def delete_by_document_id(self, document_id: str) -> None:
        """Remove every chunk previously ingested for one source document.

        Re-ingesting a document (e.g. after a manual retry) reuses the same
        deterministic chunk ids for however many chunks the new extraction
        produces; if the new run produces fewer chunks than the old one, the
        extra old ones would otherwise linger in the collection forever.
        """
        store = self.initialize_collection()
        store.delete(where={"document_id": document_id})

    def semantic_search(
        self, query: str, top_k: int = 5, document_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Return the top_k most semantically similar chunks to `query`."""
        store = self.initialize_collection()
        kwargs: dict[str, Any] = {"k": top_k}
        if document_id is not None:
            kwargs["filter"] = {"document_id": str(document_id)}
        results = store.similarity_search_with_score(query, **kwargs)
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
        try:
            from langchain_community.document_loaders import PyPDFLoader

            pages = PyPDFLoader(file_path).load()
            text = "\n".join(page.page_content for page in pages)
        except Exception:
            logger.warning(
                "Skipping PDF extraction for %s: unreadable or corrupt PDF",
                file_path,
                exc_info=True,
            )
            return ""
    elif extension == ".docx":
        try:
            from langchain_community.document_loaders import Docx2txtLoader

            pages = Docx2txtLoader(file_path).load()
            text = "\n".join(page.page_content for page in pages)
        except Exception:
            logger.warning(
                "Skipping DOCX extraction for %s: unreadable or corrupt DOCX",
                file_path,
                exc_info=True,
            )
            return ""
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


def extract_text_from_fieldfile(field_file: Any) -> str:
    """Stage a FieldFile to a local temp path, then extract raw text.

    `extract_text` needs a real filesystem path (PyPDFLoader/Docx2txtLoader
    both require one) -- `field_file.path` only works for storage backends
    with local filesystem access. `django-storages`'s `S3Storage` (wired up
    via settings.USE_S3) has no `.path` and raises `NotImplementedError`.
    Reading through `field_file.open()`/`.chunks()` instead works
    identically for every storage backend, local included, ensuring handles
    and temporary files are always cleaned up.
    """
    if not field_file:
        return ""

    file_name = getattr(field_file, "name", "") or "document"
    suffix = os.path.splitext(file_name)[1]
    fd, tmp_path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)

    try:
        field_file.open("rb")
        try:
            with open(tmp_path, "wb") as tmp:
                for chunk in field_file.chunks():
                    tmp.write(chunk)
        finally:
            field_file.close()

        return extract_text(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def _extract_document_chunks(document: Any) -> list[str]:
    """Extract and split document text into chunks using extract_text_from_fieldfile."""
    text = extract_text_from_fieldfile(document.file)
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

    chunks = _extract_document_chunks(document)
    if not chunks:
        return

    client = ChromaDBClient(
        collection_name=get_organization_collection_name(document.organization_id)
    )
    client.delete_by_document_id(str(document.id))
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
