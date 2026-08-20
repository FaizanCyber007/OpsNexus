from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "organization", "doc_type", "status", "created_at")
    list_filter = ("doc_type", "status", "organization")
    search_fields = ("file_path",)
