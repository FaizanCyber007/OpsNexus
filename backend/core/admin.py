from django.contrib import admin

from .models import AuditLog, HealthRule, Organization, Playbook, UserProfile


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at")
    search_fields = ("name", "slug")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "role", "created_at")
    list_filter = ("role", "organization")


@admin.register(HealthRule)
class HealthRuleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "organization",
        "metric",
        "threshold",
        "is_active",
    )
    list_filter = ("organization", "is_active")
    search_fields = ("name", "metric")


@admin.register(Playbook)
class PlaybookAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "is_active", "created_at")
    list_filter = ("organization", "is_active")
    search_fields = ("name",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "timestamp",
        "action",
        "resource_type",
        "resource_id",
        "user",
        "organization",
        "ip_address",
    )
    list_filter = ("action", "resource_type", "organization")
    search_fields = ("resource_id", "user__username", "ip_address")
    readonly_fields = [f.name for f in getattr(AuditLog, "_meta").fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
