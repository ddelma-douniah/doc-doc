"""
Enhanced user dashboard with statistics and recent activity.
"""
import logging
from datetime import timedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count
from django.utils import timezone
from django.views.generic import TemplateView

from .models import File, Folder

logger = logging.getLogger(__name__)


class UserDashboardView(LoginRequiredMixin, TemplateView):
    """
    Enhanced dashboard with statistics and recent activity.
    """
    template_name = 'user_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Storage statistics
        total_size = File.objects.filter(
            owner=user,
            deleted_at__isnull=True
        ).aggregate(total=Sum('size'))['total'] or 0

        # File and folder counts
        file_count = File.objects.filter(owner=user, deleted_at__isnull=True).count()
        folder_count = Folder.objects.filter(owner=user, deleted_at__isnull=True).count()
        favorite_count = File.objects.filter(owner=user, is_favorite=True, deleted_at__isnull=True).count()
        trash_count = File.objects.filter(owner=user, deleted_at__isnull=False).count() + \
                     Folder.objects.filter(owner=user, deleted_at__isnull=False).count()

        # File type breakdown
        file_types = File.objects.filter(
            owner=user,
            deleted_at__isnull=True
        ).values('mime_type').annotate(
            count=Count('id'),
            total_size=Sum('size')
        ).order_by('-total_size')[:5]

        # Recent activity (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)

        recent_files = File.objects.filter(
            owner=user,
            created_at__gte=thirty_days_ago,
            deleted_at__isnull=True
        ).order_by('-created_at')[:10]

        recent_folders = Folder.objects.filter(
            owner=user,
            created_at__gte=thirty_days_ago,
            deleted_at__isnull=True
        ).order_by('-created_at')[:10]

        # Recently accessed files
        recently_accessed = File.objects.filter(
            owner=user,
            last_accessed__isnull=False,
            deleted_at__isnull=True
        ).order_by('-last_accessed')[:5]

        # Storage trends (last 7 days)
        storage_trend = []
        for i in range(7):
            date = timezone.now() - timedelta(days=i)
            size = File.objects.filter(
                owner=user,
                created_at__lte=date,
                deleted_at__isnull=True
            ).aggregate(total=Sum('size'))['total'] or 0
            storage_trend.insert(0, {
                'date': date.strftime('%m/%d'),
                'size': size,
                'size_mb': round(size / (1024 * 1024), 2)
            })

        context.update({
            'total_size': total_size,
            'total_size_formatted': self._format_bytes(total_size),
            'file_count': file_count,
            'folder_count': folder_count,
            'favorite_count': favorite_count,
            'trash_count': trash_count,
            'file_types': file_types,
            'recent_files': recent_files,
            'recent_folders': recent_folders,
            'recently_accessed': recently_accessed,
            'storage_trend': storage_trend,
        })

        logger.info(f"User {user.username} viewed dashboard statistics")

        return context

    def _format_bytes(self, bytes_val):
        """Format bytes into human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f} PB"
