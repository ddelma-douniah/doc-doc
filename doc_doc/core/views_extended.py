"""
Extended views for doc-doc application.

This module contains views for favorites, recent files, trash, and search functionality.
"""

import logging
from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, QuerySet, Sum
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, View

from .models import File, Folder

logger = logging.getLogger(__name__)


class FavoritesView(LoginRequiredMixin, ListView):
    """
    View showing all favorited files and folders.
    """
    template_name = 'favorites.html'
    context_object_name = 'items'
    paginate_by = 50

    def get_queryset(self) -> QuerySet:
        """Return empty queryset as we handle this in get_context_data."""
        return []

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Add favorite folders and files to context.
        """
        context = super().get_context_data(**kwargs)

        # Get favorite folders (not deleted)
        context['folders'] = Folder.objects.filter(
            owner=self.request.user,
            is_favorite=True,
            deleted_at__isnull=True
        ).select_related('owner', 'parent').order_by('-updated_at')

        # Get favorite files (not deleted)
        context['files'] = File.objects.filter(
            owner=self.request.user,
            is_favorite=True,
            deleted_at__isnull=True
        ).select_related('owner', 'folder').order_by('-updated_at')

        logger.info(
            f"User {self.request.user.username} viewed favorites: "
            f"{context['folders'].count()} folders, {context['files'].count()} files"
        )

        return context


class RecentFilesView(LoginRequiredMixin, ListView):
    """
    View showing recently accessed or modified files.
    """
    template_name = 'recent.html'
    context_object_name = 'files'
    paginate_by = 50

    def get_queryset(self) -> QuerySet:
        """
        Get recently accessed files, falling back to recently modified files.
        """
        # Get files accessed in last 30 days or recently modified
        return File.objects.filter(
            owner=self.request.user,
            deleted_at__isnull=True
        ).filter(
            Q(last_accessed__isnull=False) | Q(updated_at__isnull=False)
        ).select_related('owner', 'folder').order_by('-last_accessed', '-updated_at')[:50]


class TrashView(LoginRequiredMixin, ListView):
    """
    View showing deleted files and folders (trash/recycle bin).
    """
    template_name = 'trash.html'
    context_object_name = 'items'
    paginate_by = 50

    def get_queryset(self) -> QuerySet:
        """Return empty queryset as we handle this in get_context_data."""
        return []

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Add deleted folders and files to context.
        """
        context = super().get_context_data(**kwargs)

        # Get deleted folders
        context['folders'] = Folder.objects.filter(
            owner=self.request.user,
            deleted_at__isnull=False
        ).select_related('owner').order_by('-deleted_at')

        # Get deleted files
        context['files'] = File.objects.filter(
            owner=self.request.user,
            deleted_at__isnull=False
        ).select_related('owner').order_by('-deleted_at')

        logger.info(
            f"User {self.request.user.username} viewed trash: "
            f"{context['folders'].count()} folders, {context['files'].count()} files"
        )

        return context


class ToggleFavoriteFileView(LoginRequiredMixin, View):
    """
    Toggle favorite status for a file.
    """

    def post(self, request: HttpRequest, file_id: int) -> HttpResponse:
        """Toggle favorite and redirect back."""
        file = get_object_or_404(File, id=file_id, owner=request.user)
        file.toggle_favorite()

        status = "added to" if file.is_favorite else "removed from"
        messages.success(request, _(f'File "{file.name}" {status} favorites.'))
        logger.info(
            f"User {request.user.username} toggled favorite for file: {file.name} "
            f"(now favorite: {file.is_favorite})"
        )

        # Redirect back to referrer or dashboard
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


class ToggleFavoriteFolderView(LoginRequiredMixin, View):
    """
    Toggle favorite status for a folder.
    """

    def post(self, request: HttpRequest, folder_id: int) -> HttpResponse:
        """Toggle favorite and redirect back."""
        folder = get_object_or_404(Folder, id=folder_id, owner=request.user)
        folder.toggle_favorite()

        status = "added to" if folder.is_favorite else "removed from"
        messages.success(request, _(f'Folder "{folder.name}" {status} favorites.'))
        logger.info(
            f"User {request.user.username} toggled favorite for folder: {folder.name} "
            f"(now favorite: {folder.is_favorite})"
        )

        # Redirect back to referrer or dashboard
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


class MoveToTrashFileView(LoginRequiredMixin, View):
    """
    Move a file to trash (soft delete).
    """

    def post(self, request: HttpRequest, file_id: int) -> HttpResponse:
        """Move file to trash."""
        file = get_object_or_404(File, id=file_id, owner=request.user, deleted_at__isnull=True)
        file.move_to_trash()

        messages.success(request, _(f'File "{file.name}" moved to trash.'))
        logger.info(f"User {request.user.username} moved file to trash: {file.name}")

        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


class MoveToTrashFolderView(LoginRequiredMixin, View):
    """
    Move a folder to trash (soft delete).
    """

    def post(self, request: HttpRequest, folder_id: int) -> HttpResponse:
        """Move folder and its contents to trash."""
        folder = get_object_or_404(Folder, id=folder_id, owner=request.user, deleted_at__isnull=True)
        folder.move_to_trash()

        messages.success(request, _(f'Folder "{folder.name}" moved to trash.'))
        logger.info(f"User {request.user.username} moved folder to trash: {folder.name}")

        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


class RestoreFileView(LoginRequiredMixin, View):
    """
    Restore a file from trash.
    """

    def post(self, request: HttpRequest, file_id: int) -> HttpResponse:
        """Restore file from trash."""
        file = get_object_or_404(File, id=file_id, owner=request.user, deleted_at__isnull=False)
        file.restore_from_trash()

        messages.success(request, _(f'File "{file.name}" restored from trash.'))
        logger.info(f"User {request.user.username} restored file from trash: {file.name}")

        return redirect('trash')


class RestoreFolderView(LoginRequiredMixin, View):
    """
    Restore a folder from trash.
    """

    def post(self, request: HttpRequest, folder_id: int) -> HttpResponse:
        """Restore folder and its contents from trash."""
        folder = get_object_or_404(Folder, id=folder_id, owner=request.user, deleted_at__isnull=False)
        folder.restore_from_trash()

        messages.success(request, _(f'Folder "{folder.name}" restored from trash.'))
        logger.info(f"User {request.user.username} restored folder from trash: {folder.name}")

        return redirect('trash')


class PermanentDeleteFileView(LoginRequiredMixin, View):
    """
    Permanently delete a file from trash.
    """

    def post(self, request: HttpRequest, file_id: int) -> HttpResponse:
        """Permanently delete file."""
        file = get_object_or_404(File, id=file_id, owner=request.user, deleted_at__isnull=False)
        file_name = file.name
        file.delete()  # Hard delete

        messages.success(request, _(f'File "{file_name}" permanently deleted.'))
        logger.info(f"User {request.user.username} permanently deleted file: {file_name}")

        return redirect('trash')


class PermanentDeleteFolderView(LoginRequiredMixin, View):
    """
    Permanently delete a folder from trash.
    """

    def post(self, request: HttpRequest, folder_id: int) -> HttpResponse:
        """Permanently delete folder and all its contents."""
        folder = get_object_or_404(Folder, id=folder_id, owner=request.user, deleted_at__isnull=False)
        folder_name = folder.name
        folder.delete()  # Hard delete (cascades to all contents)

        messages.success(request, _(f'Folder "{folder_name}" permanently deleted.'))
        logger.info(f"User {request.user.username} permanently deleted folder: {folder_name}")

        return redirect('trash')


class EmptyTrashView(LoginRequiredMixin, View):
    """
    Empty trash - permanently delete all trashed items.
    """

    def post(self, request: HttpRequest) -> HttpResponse:
        """Permanently delete all trashed files and folders."""
        # Count items before deletion
        deleted_files = File.objects.filter(
            owner=request.user,
            deleted_at__isnull=False
        ).count()
        deleted_folders = Folder.objects.filter(
            owner=request.user,
            deleted_at__isnull=False
        ).count()

        # Permanently delete
        File.objects.filter(owner=request.user, deleted_at__isnull=False).delete()
        Folder.objects.filter(owner=request.user, deleted_at__isnull=False).delete()

        messages.success(
            request,
            _(f'Trash emptied: {deleted_files} files and {deleted_folders} folders permanently deleted.')
        )
        logger.info(
            f"User {request.user.username} emptied trash: "
            f"{deleted_files} files, {deleted_folders} folders"
        )

        return redirect('trash')


class SearchView(LoginRequiredMixin, ListView):
    """
    Search files and folders by name.
    """
    template_name = 'search_results.html'
    context_object_name = 'results'
    paginate_by = 50

    def get_queryset(self) -> QuerySet:
        """Return empty queryset as we handle this in get_context_data."""
        return []

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Search files and folders with filters.
        """
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()
        file_type = self.request.GET.get('type', '').strip()
        size_filter = self.request.GET.get('size', '').strip()
        date_filter = self.request.GET.get('date', '').strip()

        context['query'] = query
        context['file_type'] = file_type
        context['size_filter'] = size_filter
        context['date_filter'] = date_filter

        if not query:
            context['folders'] = []
            context['files'] = []
            return context

        # Search folders (not deleted)
        context['folders'] = Folder.objects.filter(
            owner=self.request.user,
            name__icontains=query,
            deleted_at__isnull=True
        ).select_related('owner', 'parent').order_by('-updated_at')[:25]

        # Search files (not deleted)
        files = File.objects.filter(
            owner=self.request.user,
            name__icontains=query,
            deleted_at__isnull=True
        ).select_related('owner', 'folder')

        # Apply file type filter
        if file_type:
            if file_type == 'image':
                files = files.filter(mime_type__startswith='image/')
            elif file_type == 'pdf':
                files = files.filter(mime_type='application/pdf')
            elif file_type == 'document':
                files = files.filter(mime_type__in=[
                    'application/msword',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'application/vnd.ms-excel',
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                ])
            elif file_type == 'text':
                files = files.filter(mime_type__startswith='text/')

        # Apply size filter
        if size_filter:
            if size_filter == 'small':  # < 1MB
                files = files.filter(size__lt=1024*1024)
            elif size_filter == 'medium':  # 1-10MB
                files = files.filter(size__gte=1024*1024, size__lt=10*1024*1024)
            elif size_filter == 'large':  # > 10MB
                files = files.filter(size__gte=10*1024*1024)

        # Apply date filter
        if date_filter:
            from datetime import timedelta
            from django.utils import timezone
            now = timezone.now()
            if date_filter == 'today':
                files = files.filter(created_at__gte=now - timedelta(days=1))
            elif date_filter == 'week':
                files = files.filter(created_at__gte=now - timedelta(days=7))
            elif date_filter == 'month':
                files = files.filter(created_at__gte=now - timedelta(days=30))
            elif date_filter == 'year':
                files = files.filter(created_at__gte=now - timedelta(days=365))

        context['files'] = files.order_by('-updated_at')[:25]

        logger.info(
            f"User {self.request.user.username} searched '{query}' "
            f"(type={file_type}, size={size_filter}, date={date_filter}): "
            f"{len(context['folders'])} folders, {len(context['files'])} files"
        )

        return context


class StorageUsageView(LoginRequiredMixin, View):
    """
    Get storage usage information for the current user.
    """

    def get(self, request: HttpRequest) -> JsonResponse:
        """
        Return storage usage stats as JSON.
        """
        # Calculate total storage used
        total_size = File.objects.filter(
            owner=request.user,
            deleted_at__isnull=True
        ).aggregate(total=Sum('size'))['total'] or 0

        # Count items
        file_count = File.objects.filter(
            owner=request.user,
            deleted_at__isnull=True
        ).count()

        folder_count = Folder.objects.filter(
            owner=request.user,
            deleted_at__isnull=True
        ).count()

        # Storage limit from settings
        from django.conf import settings
        storage_limit = getattr(settings, 'USER_STORAGE_LIMIT', 15 * 1024 * 1024 * 1024)

        # Calculate percentage
        percentage = (total_size / storage_limit * 100) if storage_limit > 0 else 0

        # Format sizes
        def format_bytes(bytes_val):
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if bytes_val < 1024.0:
                    return f"{bytes_val:.1f} {unit}"
                bytes_val /= 1024.0
            return f"{bytes_val:.1f} PB"

        import json
        from django.http import HttpResponse

        data = {
            'total_size': total_size,
            'total_size_formatted': format_bytes(total_size),
            'storage_limit': storage_limit,
            'storage_limit_formatted': format_bytes(storage_limit),
            'percentage': round(percentage, 2),
            'file_count': file_count,
            'folder_count': folder_count,
        }

        # Return non-streaming JSON response to avoid ASGI warning
        return HttpResponse(
            json.dumps(data),
            content_type='application/json'
        )
