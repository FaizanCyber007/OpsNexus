import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.factories import (
    AuditLogFactory,
    OrganizationFactory,
    PlaybookFactory,
    UserFactory,
    UserProfileFactory,
)
from core.middleware import reset_audit_context, set_audit_context
from core.models import AuditLog, HealthRule, UserProfile
from documents.factories import DocumentFactory


User = get_user_model()


@pytest.fixture
def org_admin():
    org = OrganizationFactory()
    user = UserFactory()
    UserProfileFactory(user=user, organization=org, role=UserProfile.Role.ADMIN)
    return user, org


@pytest.fixture
def org_member():
    org = OrganizationFactory()
    user = UserFactory()
    UserProfileFactory(user=user, organization=org, role=UserProfile.Role.MEMBER)
    return user, org


@pytest.mark.django_db
class TestSOC2AuditLogSignals:
    def test_admin_creating_health_rule_generates_audit_log(self, org_admin):
        user, org = org_admin
        tokens = set_audit_context(user=user, ip_address="192.168.1.100")

        try:
            rule = HealthRule.objects.create(
                organization=org,
                name="High Latency Alert",
                metric="latency_p99",
                threshold=500.0,
            )

            log = AuditLog.objects.filter(
                resource_type="HealthRule", resource_id=str(rule.id)
            ).first()
            assert log is not None
            assert log.action == AuditLog.Action.CREATE
            assert log.user == user
            assert log.organization == org
            assert log.ip_address == "192.168.1.100"
        finally:
            reset_audit_context(tokens)

    def test_admin_updating_playbook_generates_audit_log(self, org_admin):
        user, org = org_admin
        tokens = set_audit_context(user=user, ip_address="10.0.0.5")

        try:
            playbook = PlaybookFactory(organization=org, name="Initial Playbook")
            AuditLog.objects.all().delete()  # Clear create log

            playbook.name = "Updated Incident Response"
            playbook.content = "New mitigation instructions"
            playbook.save()

            log = AuditLog.objects.filter(
                resource_type="Playbook", resource_id=str(playbook.id)
            ).first()
            assert log is not None
            assert log.action == AuditLog.Action.UPDATE
            assert log.user == user
            assert log.organization == org
            assert log.ip_address == "10.0.0.5"
        finally:
            reset_audit_context(tokens)

    def test_admin_deleting_document_generates_audit_log(self, org_admin):
        user, org = org_admin
        tokens = set_audit_context(user=user, ip_address="172.16.0.1")

        try:
            doc = DocumentFactory(organization=org)
            AuditLog.objects.all().delete()

            doc_id = str(doc.id)
            doc.delete()

            log = AuditLog.objects.filter(
                resource_type="Document", resource_id=doc_id
            ).first()
            assert log is not None
            assert log.action == AuditLog.Action.DELETE
            assert log.user == user
            assert log.organization == org
            assert log.ip_address == "172.16.0.1"
        finally:
            reset_audit_context(tokens)

    def test_non_admin_member_does_not_trigger_audit_log(self, org_member):
        user, org = org_member
        tokens = set_audit_context(user=user, ip_address="192.168.1.200")

        try:
            HealthRule.objects.create(
                organization=org,
                name="Member Rule",
                metric="error_rate",
                threshold=5.0,
            )
            assert AuditLog.objects.count() == 0
        finally:
            reset_audit_context(tokens)


@pytest.mark.django_db
class TestAuditLogsAPIEndpoint:
    def test_unauthenticated_request_denied(self):
        client = APIClient()
        response = client.get("/api/v1/audit-logs/")
        assert response.status_code in (401, 403)

    def test_non_admin_member_returns_403(self, org_member):

        user, _ = org_member
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get("/api/v1/audit-logs/")
        assert response.status_code == 403

    def test_admin_can_view_organization_audit_logs(self, org_admin):
        user, org = org_admin
        other_org = OrganizationFactory()

        # Audit logs for target org
        log1 = AuditLogFactory(
            organization=org,
            user=user,
            action=AuditLog.Action.CREATE,
            resource_type="HealthRule",
        )
        log2 = AuditLogFactory(
            organization=org,
            user=user,
            action=AuditLog.Action.DELETE,
            resource_type="Document",
        )

        # Audit log for other org
        AuditLogFactory(
            organization=other_org,
            action=AuditLog.Action.CREATE,
            resource_type="Playbook",
        )

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get("/api/v1/audit-logs/")
        assert response.status_code == 200
        assert len(response.data) == 2

        ids = [item["id"] for item in response.data]
        assert str(log1.id) in ids
        assert str(log2.id) in ids

    def test_filter_by_resource_type_and_action(self, org_admin):
        user, org = org_admin
        log_rule = AuditLogFactory(
            organization=org,
            user=user,
            action=AuditLog.Action.CREATE,
            resource_type="HealthRule",
        )
        AuditLogFactory(
            organization=org,
            user=user,
            action=AuditLog.Action.DELETE,
            resource_type="Document",
        )

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get("/api/v1/audit-logs/?resource_type=HealthRule")
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["id"] == str(log_rule.id)

        response_action = client.get("/api/v1/audit-logs/?action=DELETE")
        assert response_action.status_code == 200
        assert len(response_action.data) == 1
        assert response_action.data[0]["action"] == "DELETE"

    def test_audit_logs_endpoint_is_read_only(self, org_admin):
        user, org = org_admin
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(
            "/api/v1/audit-logs/",
            {
                "action": "CREATE",
                "resource_type": "Document",
                "resource_id": "test",
            },
        )
        assert response.status_code == 405
