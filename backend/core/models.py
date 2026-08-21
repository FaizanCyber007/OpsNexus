import uuid

from django.conf import settings
from django.db import models


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        abstract = True


class Organization(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class UserProfile(BaseModel):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        MEMBER = "member", "Member"
        VIEWER = "viewer", "Viewer"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="members",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
    )

    def __str__(self):
        return f"{self.user} ({self.organization})"


class HealthRule(BaseModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="health_rules",
        db_index=True,
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    metric = models.CharField(max_length=100, default="cpu_usage")
    threshold = models.FloatField(default=80.0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.organization})"


class Playbook(BaseModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="playbooks",
        db_index=True,
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    content = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.organization})"


class AuditLog(BaseModel):
    class Action(models.TextChoices):
        CREATE = "CREATE", "Create"
        UPDATE = "UPDATE", "Update"
        DELETE = "DELETE", "Delete"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="audit_logs",
        db_index=True,
    )
    action = models.CharField(
        max_length=20,
        choices=Action.choices,
        db_index=True,
    )
    resource_type = models.CharField(max_length=100, db_index=True)
    resource_id = models.CharField(max_length=255, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return (
            f"[{self.timestamp}] {self.action} {self.resource_type}:"
            f"{self.resource_id} by {self.user}"
        )
