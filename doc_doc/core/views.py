"""
Views for the doc-doc core application.

This module contains all views for folder and file management, including
dashboard, folder browsing, file uploads, and sharing functionality.
"""

import logging
from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Q, QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    View,
)

from .models import File, Folder, Share
from .validators import validate_file, sanitize_filename

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    """
    Landing page view for unauthenticated users.
    """
    template_name = 'home.html'

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Redirect to dashboard if user is authenticated."""
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().get(request, *args, **kwargs)


class DashboardView(LoginRequiredMixin, ListView):
    """
    Main dashboard view showing user's root-level folders and files.

    Displays all folders and files that don't have a parent folder,
    effectively showing the user's root directory.
    """
    template_name = 'dashboard.html'
    context_object_name = 'items'
    paginate_by = 50

    def get_queryset(self) -> QuerySet:
        """
        Get root-level folders and files for the current user.

        Returns:
            QuerySet: Combined queryset of folders and files.
        """
        # This will be split in get_context_data
        return []

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Add folders and files to the context.

        Returns:
            Dict containing folders and files.
        """
        context = super().get_context_data(**kwargs)

        # Get root folders (no parent, not deleted)
        context['folders'] = Folder.objects.filter(
            owner=self.request.user,
            parent__isnull=True,
            deleted_at__isnull=True
        ).select_related('owner').annotate(
            file_count=Count('files'),
            subfolder_count=Count('subfolders')
        )

        # Get root files (no folder, not deleted)
        context['files'] = File.objects.filter(
            owner=self.request.user,
            folder__isnull=True,
            deleted_at__isnull=True
        ).select_related('owner')

        logger.info(
            f"User {self.request.user.username} accessed dashboard "
            f"with {context['folders'].count()} folders and {context['files'].count()} files"
        )

        return context

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Handle folder creation and file upload.
        """
        if 'create_folder' in request.POST:
            return self._create_folder(request)
        elif 'upload_file' in request.POST:
            return self._upload_file(request)
        return self.get(request, *args, **kwargs)

    @transaction.atomic
    def _create_folder(self, request: HttpRequest) -> HttpResponseRedirect:
        """
        Create a new root-level folder.

        Args:
            request: The HTTP request object.

        Returns:
            Redirect to dashboard.
        """
        folder_name = request.POST.get('folder_name', '').strip()

        if not folder_name:
            messages.error(request, _('Folder name is required.'))
            logger.warning(f"User {request.user.username} attempted to create folder without name")
            return redirect('dashboard')

        try:
            folder = Folder.objects.create(
                name=folder_name,
                owner=request.user,
                parent=None
            )
            messages.success(request, _(f'Folder "{folder.name}" created successfully.'))
            logger.info(f"User {request.user.username} created folder: {folder.name}")
        except Exception as e:
            messages.error(request, _('Failed to create folder. Please try again.'))
            logger.error(f"Error creating folder for user {request.user.username}: {str(e)}")

        return redirect('dashboard')

    @transaction.atomic
    def _upload_file(self, request: HttpRequest) -> HttpResponseRedirect:
        """
        Upload a new file to root level.

        Args:
            request: The HTTP request object.

        Returns:
            Redirect to dashboard.
        """
        uploaded_file = request.FILES.get('file')

        if not uploaded_file:
            messages.error(request, _('Please select a file to upload.'))
            logger.warning(f"User {request.user.username} attempted to upload without selecting file")
            return redirect('dashboard')

        try:
            # Validate file
            from django.core.exceptions import ValidationError
            try:
                validate_file(uploaded_file)
            except ValidationError as ve:
                messages.error(request, str(ve))
                logger.warning(f"User {request.user.username} attempted invalid file upload: {ve}")
                return redirect('dashboard')

            # Sanitize filename
            safe_name = sanitize_filename(uploaded_file.name)

            file_obj = File.objects.create(
                name=safe_name,
                file=uploaded_file,
                owner=request.user,
                folder=None
            )
            messages.success(
                request,
                _(f'File "{file_obj.name}" ({file_obj.formatted_size}) uploaded successfully.')
            )
            logger.info(
                f"User {request.user.username} uploaded file: {file_obj.name} "
                f"({file_obj.size} bytes)"
            )
        except Exception as e:
            import traceback
            messages.error(request, _('Failed to upload file. Please try again.'))
            logger.error(
                f"Error uploading file for user {request.user.username}: {str(e)}\n"
                f"Traceback: {traceback.format_exc()}"
            )

        return redirect('dashboard')


class FolderDetailView(LoginRequiredMixin, DetailView):
    """
    Detailed view of a folder showing its contents.

    Displays subfolders and files within the specified folder.
    """
    model = Folder
    template_name = 'folder_detail.html'
    context_object_name = 'folder'
    pk_url_kwarg = 'folder_id'

    def get_queryset(self) -> QuerySet:
        """
        Ensure users can only access their own folders.

        Returns:
            QuerySet filtered by current user.
        """
        return Folder.objects.filter(owner=self.request.user).select_related(
            'owner', 'parent'
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Add subfolders and files to context.

        Returns:
            Dict containing folder contents.
        """
        context = super().get_context_data(**kwargs)
        folder = self.object

        # Get subfolders (not deleted)
        context['folders'] = Folder.objects.filter(
            owner=self.request.user,
            parent=folder,
            deleted_at__isnull=True
        ).annotate(
            file_count=Count('files'),
            subfolder_count=Count('subfolders')
        )

        # Get files in this folder (not deleted)
        context['files'] = File.objects.filter(
            owner=self.request.user,
            folder=folder,
            deleted_at__isnull=True
        )

        # Add breadcrumb trail
        context['breadcrumbs'] = self._get_breadcrumbs(folder)

        logger.info(
            f"User {self.request.user.username} accessed folder: {folder.name} "
            f"(ID: {folder.id})"
        )

        return context

    def _get_breadcrumbs(self, folder: Folder) -> list:
        """
        Generate breadcrumb navigation trail.

        Args:
            folder: The current folder.

        Returns:
            List of tuples containing (name, url) for each level.
        """
        breadcrumbs = [('Dashboard', reverse('dashboard'))]
        path = []
        current = folder

        while current:
            path.insert(0, current)
            current = current.parent

        for f in path:
            breadcrumbs.append((f.name, reverse('folder_detail', kwargs={'folder_id': f.id})))

        return breadcrumbs

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Handle subfolder creation and file upload within folder.
        """
        self.object = self.get_object()

        if 'create_folder' in request.POST:
            return self._create_subfolder(request, self.object)
        elif 'upload_file' in request.POST:
            return self._upload_file_to_folder(request, self.object)

        return self.get(request, *args, **kwargs)

    @transaction.atomic
    def _create_subfolder(self, request: HttpRequest, parent: Folder) -> HttpResponseRedirect:
        """
        Create a subfolder within the current folder.

        Args:
            request: The HTTP request object.
            parent: The parent folder.

        Returns:
            Redirect to current folder.
        """
        folder_name = request.POST.get('folder_name', '').strip()

        if not folder_name:
            messages.error(request, _('Folder name is required.'))
            return redirect('folder_detail', folder_id=parent.id)

        try:
            folder = Folder.objects.create(
                name=folder_name,
                owner=request.user,
                parent=parent
            )
            messages.success(request, _(f'Subfolder "{folder.name}" created successfully.'))
            logger.info(
                f"User {request.user.username} created subfolder: {folder.name} "
                f"in folder: {parent.name}"
            )
        except Exception as e:
            messages.error(request, _('Failed to create subfolder. Please try again.'))
            logger.error(
                f"Error creating subfolder for user {request.user.username}: {str(e)}"
            )

        return redirect('folder_detail', folder_id=parent.id)

    @transaction.atomic
    def _upload_file_to_folder(
        self, request: HttpRequest, folder: Folder
    ) -> HttpResponseRedirect:
        """
        Upload a file to the current folder.

        Args:
            request: The HTTP request object.
            folder: The target folder.

        Returns:
            Redirect to current folder.
        """
        uploaded_file = request.FILES.get('file')

        if not uploaded_file:
            messages.error(request, _('Please select a file to upload.'))
            return redirect('folder_detail', folder_id=folder.id)

        try:
            # Validate file
            from django.core.exceptions import ValidationError
            try:
                validate_file(uploaded_file)
            except ValidationError as ve:
                messages.error(request, str(ve))
                logger.warning(f"User {request.user.username} attempted invalid file upload: {ve}")
                return redirect('folder_detail', folder_id=folder.id)

            # Sanitize filename
            safe_name = sanitize_filename(uploaded_file.name)

            file_obj = File.objects.create(
                name=safe_name,
                file=uploaded_file,
                owner=request.user,
                folder=folder
            )
            messages.success(
                request,
                _(f'File "{file_obj.name}" ({file_obj.formatted_size}) uploaded successfully.')
            )
            logger.info(
                f"User {request.user.username} uploaded file: {file_obj.name} "
                f"to folder: {folder.name}"
            )
        except Exception as e:
            import traceback
            messages.error(request, _('Failed to upload file. Please try again.'))
            logger.error(
                f"Error uploading file to folder for user {request.user.username}: {str(e)}\n"
                f"Traceback: {traceback.format_exc()}"
            )

        return redirect('folder_detail', folder_id=folder.id)


class ShareFileView(LoginRequiredMixin, View):
    """
    Create a share link for a file.
    """

    def get(self, request: HttpRequest, file_id: int) -> HttpResponse:
        """
        Generate or retrieve share link for a file.

        Args:
            request: The HTTP request object.
            file_id: ID of the file to share.

        Returns:
            Rendered share link page.
        """
        file = get_object_or_404(File, id=file_id, owner=request.user)

        # Get or create share
        share, created = Share.objects.get_or_create(
            file=file,
            folder=None,
            defaults={'is_active': True}
        )

        share_url = request.build_absolute_uri(
            reverse('shared_view', kwargs={'share_id': share.id})
        )

        action = "created" if created else "retrieved"
        logger.info(
            f"User {request.user.username} {action} share link for file: {file.name}"
        )

        return render(request, 'share_link.html', {
            'share_url': share_url,
            'share': share,
            'object': file,
        })


class ShareFolderView(LoginRequiredMixin, View):
    """
    Create a share link for a folder.
    """

    def get(self, request: HttpRequest, folder_id: int) -> HttpResponse:
        """
        Generate or retrieve share link for a folder.

        Args:
            request: The HTTP request object.
            folder_id: ID of the folder to share.

        Returns:
            Rendered share link page.
        """
        folder = get_object_or_404(Folder, id=folder_id, owner=request.user)

        # Get or create share
        share, created = Share.objects.get_or_create(
            folder=folder,
            file=None,
            defaults={'is_active': True}
        )

        share_url = request.build_absolute_uri(
            reverse('shared_view', kwargs={'share_id': share.id})
        )

        action = "created" if created else "retrieved"
        logger.info(
            f"User {request.user.username} {action} share link for folder: {folder.name}"
        )

        return render(request, 'share_link.html', {
            'share_url': share_url,
            'share': share,
            'object': folder,
        })


class SharedView(View):
    """
    View for accessing shared files or folders via share link.

    This view is accessible without authentication but enforces share
    permissions and expiration.
    """

    def get(self, request: HttpRequest, share_id: str) -> HttpResponse:
        """
        Display shared content if share is valid.

        Args:
            request: The HTTP request object.
            share_id: UUID of the share.

        Returns:
            Rendered page with shared content or error.
        """
        share = get_object_or_404(Share, id=share_id)

        # Check if share is active
        if not share.is_active:
            logger.warning(f"Attempt to access inactive share: {share_id}")
            return render(request, 'share_error.html', {
                'error': _('This share link is no longer active.')
            }, status=403)

        # Check if share has expired
        if share.is_expired():
            logger.warning(f"Attempt to access expired share: {share_id}")
            return render(request, 'share_error.html', {
                'error': _('This share link has expired.')
            }, status=403)

        # Check password protection
        if share.password:
            session_key = f'share_password_verified_{share_id}'
            if not request.session.get(session_key):
                # Show password form
                return render(request, 'share_password.html', {
                    'share': share,
                    'share_id': share_id
                })

        # Check shared_with restrictions (if authenticated)
        if share.shared_with.exists():
            if not request.user.is_authenticated:
                logger.warning(f"Unauthenticated attempt to access restricted share: {share_id}")
                return render(request, 'share_error.html', {
                    'error': _('This share requires authentication. Please log in.')
                }, status=403)

            if request.user not in share.shared_with.all():
                logger.warning(f"User {request.user.username} attempted to access restricted share: {share_id}")
                return render(request, 'share_error.html', {
                    'error': _('You do not have permission to access this share.')
                }, status=403)

        # Increment access count
        share.increment_access_count()

        # Determine template based on content type
        if share.file:
            template = 'shared_file.html'
            context = {'file': share.file, 'share': share}
            logger.info(f"Share {share_id} accessed for file: {share.file.name}")
        else:
            template = 'shared_folder.html'
            # Get folder contents
            files = File.objects.filter(folder=share.folder)
            subfolders = Folder.objects.filter(parent=share.folder).annotate(
                file_count=Count('files')
            )
            context = {
                'folder': share.folder,
                'files': files,
                'subfolders': subfolders,
                'share': share
            }
            logger.info(f"Share {share_id} accessed for folder: {share.folder.name}")

        return render(request, template, context)

    def post(self, request: HttpRequest, share_id: str) -> HttpResponse:
        """
        Handle password verification for protected shares.

        Args:
            request: The HTTP request object.
            share_id: UUID of the share.

        Returns:
            Redirect to GET if password correct, otherwise show error.
        """
        share = get_object_or_404(Share, id=share_id)
        password = request.POST.get('password', '')

        if share.check_password(password):
            # Store verification in session
            session_key = f'share_password_verified_{share_id}'
            request.session[session_key] = True
            logger.info(f"Successful password verification for share: {share_id}")
            return redirect('shared_view', share_id=share_id)
        else:
            logger.warning(f"Failed password attempt for share: {share_id}")
            messages.error(request, _('Incorrect password. Please try again.'))
            return render(request, 'share_password.html', {
                'share': share,
                'share_id': share_id,
                'error': True
            })


# Error handlers
def handler404(request, exception):
    """Custom 404 error handler."""
    return render(request, '404.html', status=404)


def handler500(request):
    """Custom 500 error handler."""
    return render(request, '500.html', status=500)
