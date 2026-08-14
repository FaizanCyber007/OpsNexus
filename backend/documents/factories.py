import factory
from factory.django import DjangoModelFactory

from core.factories import OrganizationFactory

from .models import Document


class DocumentFactory(DjangoModelFactory):
    class Meta:
        model = Document

    organization = factory.SubFactory(OrganizationFactory)
    doc_type = Document.DocType.OTHER
    status = Document.Status.PENDING
    file_path = factory.Sequence(lambda n: f"documents/test-file-{n}.txt")
