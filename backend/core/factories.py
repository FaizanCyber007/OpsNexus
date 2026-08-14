import factory
from factory.django import DjangoModelFactory

from .models import Organization


class OrganizationFactory(DjangoModelFactory):
    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: f"Test Org {n}")
    slug = factory.Sequence(lambda n: f"test-org-{n}")
    is_active = True
