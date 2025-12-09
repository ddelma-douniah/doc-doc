"""
Admin configuration for doc-doc core models.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import File, Folder, Share


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    """Admin interface for Folder model."""

    list_display = ['name', 'owner', 'parent', 'file_count', 'created_at', 'updated_at']
    list_filter = ['owner', 'created_at', 'updated_at']
    search_fields = ['name', 'owner__username', 'owner__email']
    readonly_fields = ['created_at', 'updated_at', 'get_path_display', 'get_size_display']
    raw_id_fields = ['owner', 'parent']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'owner', 'parent')
        }),
        (_('Computed Information'), {
            'fields': ('get_path_display', 'get_size_display'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_path_display(self, obj):
        """Display folder path."""
        return obj.get_path()
    get_path_display.short_description = _('Path')

    def get_size_display(self, obj):
        """Display folder size."""
        return obj.get_size()
    get_size_display.short_description = _('Total Size')

    def file_count(self, obj):
        """Display number of files in folder."""
        return obj.files.count()
    file_count.short_description = _('Files')


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    """Admin interface for File model."""

    list_display = ['name', 'owner', 'folder', 'size_display', 'mime_type', 'created_at']
    list_filter = ['owner', 'mime_type', 'created_at', 'updated_at']
    search_fields = ['name', 'owner__username', 'owner__email']
    readonly_fields = ['created_at', 'updated_at', 'size', 'mime_type', 'formatted_size']
    raw_id_fields = ['owner', 'folder']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'file', 'owner', 'folder')
        }),
        (_('File Information'), {
            'fields': ('size', 'formatted_size', 'mime_type'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def size_display(self, obj):
        """Display formatted file size."""
        return obj.formatted_size
    size_display.short_description = _('Size')


@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    """Admin interface for Share model."""

    list_display = ['id_short', 'shared_object', 'is_active', 'has_password', 'expires_at', 'access_count', 'created_at']
    list_filter = ['is_active', 'created_at', 'expires_at']
    search_fields = ['id', 'file__name', 'folder__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'access_count', 'get_share_url']
    raw_id_fields = ['file', 'folder']
    filter_horizontal = ['shared_with']

    fieldsets = (
        (_('Share Information'), {
            'fields': ('id', 'file', 'folder', 'is_active')
        }),
        (_('Security'), {
            'fields': ('password', 'expires_at', 'shared_with')
        }),
        (_('Statistics'), {
            'fields': ('access_count', 'get_share_url'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def id_short(self, obj):
        """Display shortened UUID."""
        return str(obj.id)[:8]
    id_short.short_description = _('Share ID')

    def shared_object(self, obj):
        """Display what is being shared."""
        return obj.get_shared_object()
    shared_object.short_description = _('Shared Object')

    def has_password(self, obj):
        """Display if share has password."""
        if obj.password:
            return format_html('<i class="fas fa-lock" style="color: green;"></i> Yes')
        return format_html('<i class="fas fa-lock-open" style="color: gray;"></i> No')
    has_password.short_description = _('Password')

    def get_share_url(self, obj):
        """Display shareable URL."""
        from django.urls import reverse
        from django.conf import settings
        path = reverse('shared_view', kwargs={'share_id': obj.id})
        url = f"{settings.SITE_URL}{path}"
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)
    get_share_url.short_description = _('Share URL')
