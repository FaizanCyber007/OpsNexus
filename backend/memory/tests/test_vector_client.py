from unittest.mock import patch

from memory.vector_client import ingest_document


class _FakeFieldFile:
    """Mimics a Django FieldFile backed by django-storages' S3Storage.

    S3Storage has no local filesystem access, so accessing `.path` raises
    NotImplementedError -- only the storage-agnostic File API (`.open()`/
    `.chunks()`) works. This stub proves ingest_document never touches
    `.path`.
    """

    def __init__(self, name: str, content: bytes):
        self.name = name
        self._content = content

    @property
    def path(self):
        raise NotImplementedError("This backend doesn't support absolute paths.")

    def open(self, mode="rb"):
        return self

    def chunks(self):
        yield self._content

    def close(self):
        pass

    def __bool__(self):
        return True


class _FakeDocument:
    def __init__(self, file_field, document_id="doc-1", organization_id="org-1"):
        self.file = file_field
        self.id = document_id
        self.organization_id = organization_id


def test_ingest_document_works_without_field_file_path():
    document = _FakeDocument(
        _FakeFieldFile("documents/policy.txt", b"OpsNexus SOC2 policy details.")
    )

    with patch("memory.vector_client.ChromaDBClient") as MockClient:
        ingest_document(document)

    MockClient.return_value.delete_by_document_id.assert_called_once_with("doc-1")
    MockClient.return_value.add_documents.assert_called_once()
    added_docs = MockClient.return_value.add_documents.call_args.args[0]
    assert added_docs[0]["text"].startswith("OpsNexus SOC2 policy")


def test_ingest_document_no_op_for_undecodable_file():
    document = _FakeDocument(_FakeFieldFile("documents/image.png", b"\xff\xd8\xff\xe0"))

    with patch("memory.vector_client.ChromaDBClient") as MockClient:
        ingest_document(document)

    MockClient.return_value.add_documents.assert_not_called()
