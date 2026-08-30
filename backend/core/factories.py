import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

from .models import AuditLog, HealthRule, Organization, Playbook, UserProfile

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.Sequence(lambda n: f"user_{n}@example.com")
    is_active = True


class OrganizationFactory(DjangoModelFactory):
    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: f"Test Org {n}")
    slug = factory.Sequence(lambda n: f"test-org-{n}")
    is_active = True


class UserProfileFactory(DjangoModelFactory):
    class Meta:
        model = UserProfile

    user = factory.SubFactory(UserFactory)
    organization = factory.SubFactory(OrganizationFactory)
    role = UserProfile.Role.MEMBER


class HealthRuleFactory(DjangoModelFactory):
    class Meta:
        model = HealthRule

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.Sequence(lambda n: f"Health Rule {n}")
    description = "Test health rule description"
    metric = "cpu_usage"
    threshold = 85.0
    is_active = True


class PlaybookFactory(DjangoModelFactory):
    class Meta:
        model = Playbook

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.Sequence(lambda n: f"Playbook {n}")
    description = "Test playbook description"
    content = "# Incident Response Step 1: Verify alerting state"
    is_active = True


class AuditLogFactory(DjangoModelFactory):
    class Meta:
        model = AuditLog

    user = factory.SubFactory(UserFactory)
    organization = factory.SubFactory(OrganizationFactory)
    action = AuditLog.Action.CREATE
    resource_type = "Document"
    resource_id = factory.Faker("uuid4")
    ip_address = "127.0.0.1"
