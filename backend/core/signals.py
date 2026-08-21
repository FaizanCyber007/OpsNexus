"""SOC2 Audit Logging Signals for OpsNexus.

Automatically records AuditLog entries when an Organization Admin creates,
updates, or deletes monitored resources (HealthRule, Playbook, Document).
"""

import logging
from typing import Any

from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from core.middleware import get_client_ip, get_current_user
from core.models import AuditLog, HealthRule, Playbook, UserProfile
from documents.models import Document

logger = logging.getLogger(__name__)

AUDITED_MODELS = (HealthRule, Playbook, Document)


def is_organization_admin(user: Any) -> bool:
    """Check if the user has Organization Admin privileges."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        return True
    profile = getattr(user, "profile", None)
    return profile is not None and profile.role == UserProfile.Role.ADMIN


def _get_organization(instance: Any, user: Any):
    """Retrieve organization from instance or user profile."""
    if hasattr(instance, "organization") and instance.organization:
        return instance.organization
    if user and hasattr(user, "profile") and user.profile.organization:
        return user.profile.organization
    return None


@receiver(post_save, sender=HealthRule)
@receiver(post_save, sender=Playbook)
@receiver(post_save, sender=Document)
def log_resource_save(sender, instance, created, **kwargs):
    """Log CREATE or UPDATE actions performed by authenticated actors."""
    user = get_current_user() or getattr(instance, "_audit_user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return

    organization = _get_organization(instance, user)
    if not organization:
        logger.warning(
            "Skipping audit log for %s:%s - no organization found",
            sender.__name__,
            instance.pk,
        )
        return

    action = AuditLog.Action.CREATE if created else AuditLog.Action.UPDATE
    ip_address = get_client_ip() or getattr(instance, "_audit_ip", None)

    try:
        with transaction.atomic():
            AuditLog.objects.create(
                user=user if getattr(user, "is_authenticated", False) else None,
                organization=organization,
                action=action,
                resource_type=sender.__name__,
                resource_id=str(instance.pk),
                ip_address=ip_address,
            )
    except Exception:
        logger.exception(
            "Failed to create AuditLog for %s %s:%s",
            action,
            sender.__name__,
            instance.pk,
        )


@receiver(post_delete, sender=HealthRule)
@receiver(post_delete, sender=Playbook)
@receiver(post_delete, sender=Document)
def log_resource_delete(sender, instance, **kwargs):
    """Log DELETE actions performed by authenticated actors."""
    user = get_current_user() or getattr(instance, "_audit_user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return

    organization = _get_organization(instance, user)
    if not organization:
        logger.warning(
            "Skipping audit log for DELETE %s:%s - no organization found",
            sender.__name__,
            instance.pk,
        )
        return

    ip_address = get_client_ip() or getattr(instance, "_audit_ip", None)

    try:
        with transaction.atomic():
            AuditLog.objects.create(
                user=user if getattr(user, "is_authenticated", False) else None,
                organization=organization,
                action=AuditLog.Action.DELETE,
                resource_type=sender.__name__,
                resource_id=str(instance.pk),
                ip_address=ip_address,
            )
    except Exception:
        logger.exception(
            "Failed to create AuditLog for DELETE %s:%s",
            sender.__name__,
            instance.pk,
        )
