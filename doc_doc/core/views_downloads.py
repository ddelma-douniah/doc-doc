"""
File download and preview views with access tracking.
"""
import logging
import mimetypes
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, FileResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import View

from .models import File

logger = logging.getLogger(__name__)


class FileDownloadView(LoginRequiredMixin, View):
    """
    Download file with access tracking.
    """

    def get(self, request, file_id):
        """
        Serve file for download and track access.

        Args:
            request: HTTP request
            file_id: ID of the file to download

        Returns:
            FileResponse with file content
        """
        file_obj = get_object_or_404(File, id=file_id, deleted_at__isnull=True)

        # Check permissions
        if file_obj.owner != request.user:
            logger.warning(
                f"User {request.user.username} attempted unauthorized access to file: {file_obj.name}"
            )
            raise PermissionDenied("You don't have permission to access this file.")

        try:
            # Mark as accessed
            file_obj.mark_accessed()

            # Get file from storage
            file_handle = file_obj.file.open('rb')

            # Determine content type
            content_type = file_obj.mime_type or 'application/octet-stream'

            # Create response
            response = FileResponse(
                file_handle,
                content_type=content_type,
                as_attachment=True,
                filename=file_obj.name
            )

            logger.info(
                f"User {request.user.username} downloaded file: {file_obj.name} "
                f"({file_obj.formatted_size})"
            )

            return response

        except Exception as e:
            import traceback
            logger.error(
                f"Error downloading file {file_obj.name} for user {request.user.username}: {str(e)}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            raise Http404("File not found or cannot be accessed.")


class FilePreviewView(LoginRequiredMixin, View):
    """
    Preview file inline (for images, PDFs, etc.).
    """

    # Supported preview types
    PREVIEWABLE_TYPES = {
        'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml',
        'application/pdf',
        'text/plain', 'text/html', 'text/css', 'text/javascript',
        'application/json', 'application/xml',
    }

    def get(self, request, file_id):
        """
        Serve file for preview or show preview page.

        Args:
            request: HTTP request
            file_id: ID of the file to preview

        Returns:
            HttpResponse with file content or preview page
        """
        file_obj = get_object_or_404(File, id=file_id, deleted_at__isnull=True)

        # Check permissions
        if file_obj.owner != request.user:
            logger.warning(
                f"User {request.user.username} attempted unauthorized preview of file: {file_obj.name}"
            )
            raise PermissionDenied("You don't have permission to preview this file.")

        # Mark as accessed
        file_obj.mark_accessed()

        # Check if file type is previewable
        mime_type = file_obj.mime_type or 'application/octet-stream'

        if mime_type not in self.PREVIEWABLE_TYPES:
            # Render preview page with download option
            return render(request, 'file_preview_unsupported.html', {
                'file': file_obj,
                'mime_type': mime_type,
            })

        try:
            # For images and PDFs, show inline preview page
            if mime_type.startswith('image/') or mime_type == 'application/pdf':
                return render(request, 'file_preview.html', {
                    'file': file_obj,
                    'mime_type': mime_type,
                    'is_image': mime_type.startswith('image/'),
                    'is_pdf': mime_type == 'application/pdf',
                })

            # For text files, serve inline
            file_handle = file_obj.file.open('rb')
            response = FileResponse(
                file_handle,
                content_type=mime_type,
                as_attachment=False,
                filename=file_obj.name
            )

            logger.info(
                f"User {request.user.username} previewed file: {file_obj.name}"
            )

            return response

        except Exception as e:
            import traceback
            logger.error(
                f"Error previewing file {file_obj.name} for user {request.user.username}: {str(e)}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            raise Http404("File not found or cannot be previewed.")


class FileServeView(LoginRequiredMixin, View):
    """
    Serve raw file content (for embedding in preview page).
    """

    def get(self, request, file_id):
        """
        Serve raw file content.

        Args:
            request: HTTP request
            file_id: ID of the file to serve

        Returns:
            HttpResponse with file content
        """
        file_obj = get_object_or_404(File, id=file_id, deleted_at__isnull=True)

        # Check permissions
        if file_obj.owner != request.user:
            raise PermissionDenied("You don't have permission to access this file.")

        try:
            file_handle = file_obj.file.open('rb')
            content_type = file_obj.mime_type or 'application/octet-stream'

            response = FileResponse(
                file_handle,
                content_type=content_type,
                as_attachment=False
            )

            # Add security headers
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'SAMEORIGIN'

            return response

        except Exception as e:
            logger.error(f"Error serving file {file_obj.name}: {str(e)}")
            raise Http404("File not found.")
