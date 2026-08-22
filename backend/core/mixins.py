import uuid
from rest_framework import exceptions


class TenantScopedViewSetMixin:
    """
    Mixin to enforce organization-based filtering on viewsets.
    It expects the viewset to define a `queryset` class attribute.
    """

    def get_queryset(self):
        # We assume the viewset has a base `queryset` defined.
        queryset = super().get_queryset()
        user = getattr(self.request, "user", None)

        if not user or not user.is_authenticated:
            return queryset.none()

        # Check if we need to filter by a different field (e.g., `document__organization`)
        filter_kwarg = getattr(self, "tenant_filter_kwarg", "organization")
        filter_id_kwarg = (
            filter_kwarg if filter_kwarg == "id" or filter_kwarg.endswith("_id") else f"{filter_kwarg}_id"
        )

        if user.is_superuser:
            org_id = self.request.query_params.get("organization")
            if org_id:
                try:
                    uuid.UUID(str(org_id))
                except (ValueError, AttributeError, TypeError):
                    raise exceptions.ValidationError(
                        {"organization": "Invalid UUID format."}
                    )
                queryset = queryset.filter(**{filter_id_kwarg: org_id})
            return queryset

        # Regular users can only see their own organization's data.
        profile = getattr(user, "profile", None)
        if profile and getattr(profile, "organization_id", None):
            queryset = queryset.filter(**{filter_id_kwarg: profile.organization_id})
        else:
            queryset = queryset.none()

        return queryset
