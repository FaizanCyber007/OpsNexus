"""
URL configuration for opsnexus_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from agents.views import AgentRunViewSet
from core.views import AuditLogViewSet
from documents.views import DocumentViewSet
from orchestration.views import DocumentChatView

router = DefaultRouter()
router.register(r"documents", DocumentViewSet, basename="document")
router.register(r"agent-runs", AgentRunViewSet, basename="agent-run")
router.register(r"audit-logs", AuditLogViewSet, basename="audit-log")


urlpatterns = [
    path("admin/", admin.site.urls),
    # OpenAPI Schema & Interactive Documentation
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/v1/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/v1/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path(
        "api/v1/documents/<uuid:document_id>/chat/",
        DocumentChatView.as_view(),
        name="document-chat-v1",
    ),
    path(
        "api/v1/documents/<str:document_id>/chat/",
        DocumentChatView.as_view(),
        name="document-chat-v1-str",
    ),
    path(
        "api/documents/<uuid:document_id>/chat/",
        DocumentChatView.as_view(),
        name="document-chat",
    ),
    path("api/v1/", include(router.urls)),
    path("api/", include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
