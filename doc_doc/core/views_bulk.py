"""
Bulk operations views for files and folders.
"""
import logging
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views import View

from .models import File, Folder

logger = logging.getLogger(__name__)


class BulkFileActionView(LoginRequiredMixin, View):
    """
    Handle bulk actions on multiple files.
    """

    @transaction.atomic
    def post(self, request):
        """
        Perform bulk action on selected files.

        Actions: delete, favorite, unfavorite, move
        """
        action = request.POST.get('action')
        file_ids = request.POST.getlist('file_ids')

        if not file_ids:
            messages.warning(request, _('No files selected.'))
            return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

        # Get files owned by the current user
        files = File.objects.filter(
            id__in=file_ids,
            owner=request.user,
            deleted_at__isnull=True
        )

        count = files.count()

        if count == 0:
            messages.warning(request, _('No valid files found.'))
            return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

        try:
            if action == 'delete':
                # Move to trash
                for file in files:
                    file.move_to_trash()
                messages.success(request, _(f'{count} file(s) moved to trash.'))
                logger.info(f"User {request.user.username} bulk deleted {count} files")

            elif action == 'favorite':
                files.update(is_favorite=True)
                messages.success(request, _(f'{count} file(s) added to favorites.'))
                logger.info(f"User {request.user.username} bulk favorited {count} files")

            elif action == 'unfavorite':
                files.update(is_favorite=False)
                messages.success(request, _(f'{count} file(s) removed from favorites.'))
                logger.info(f"User {request.user.username} bulk unfavorited {count} files")

            elif action == 'move':
                folder_id = request.POST.get('target_folder')
                if folder_id:
                    target_folder = Folder.objects.get(id=folder_id, owner=request.user)
                    files.update(folder=target_folder)
                    messages.success(request, _(f'{count} file(s) moved to {target_folder.name}.'))
                    logger.info(f"User {request.user.username} bulk moved {count} files to {target_folder.name}")
                else:
                    # Move to root
                    files.update(folder=None)
                    messages.success(request, _(f'{count} file(s) moved to root.'))
                    logger.info(f"User {request.user.username} bulk moved {count} files to root")

            else:
                messages.error(request, _('Invalid action.'))

        except Exception as e:
            import traceback
            logger.error(
                f"Error performing bulk action {action} for user {request.user.username}: {str(e)}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            messages.error(request, _('An error occurred. Please try again.'))

        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


class BulkFolderActionView(LoginRequiredMixin, View):
    """
    Handle bulk actions on multiple folders.
    """

    @transaction.atomic
    def post(self, request):
        """
        Perform bulk action on selected folders.

        Actions: delete, favorite, unfavorite
        """
        action = request.POST.get('action')
        folder_ids = request.POST.getlist('folder_ids')

        if not folder_ids:
            messages.warning(request, _('No folders selected.'))
            return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

        # Get folders owned by the current user
        folders = Folder.objects.filter(
            id__in=folder_ids,
            owner=request.user,
            deleted_at__isnull=True
        )

        count = folders.count()

        if count == 0:
            messages.warning(request, _('No valid folders found.'))
            return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

        try:
            if action == 'delete':
                # Move to trash
                for folder in folders:
                    folder.move_to_trash()
                messages.success(request, _(f'{count} folder(s) moved to trash.'))
                logger.info(f"User {request.user.username} bulk deleted {count} folders")

            elif action == 'favorite':
                folders.update(is_favorite=True)
                messages.success(request, _(f'{count} folder(s) added to favorites.'))
                logger.info(f"User {request.user.username} bulk favorited {count} folders")

            elif action == 'unfavorite':
                folders.update(is_favorite=False)
                messages.success(request, _(f'{count} folder(s) removed from favorites.'))
                logger.info(f"User {request.user.username} bulk unfavorited {count} folders")

            else:
                messages.error(request, _('Invalid action.'))

        except Exception as e:
            import traceback
            logger.error(
                f"Error performing bulk action {action} for user {request.user.username}: {str(e)}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            messages.error(request, _('An error occurred. Please try again.'))

        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
