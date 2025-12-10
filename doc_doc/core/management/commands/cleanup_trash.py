"""
Management command to automatically clean up trash (delete files/folders older than 30 days).
"""
import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from doc_doc.core.models import File, Folder

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Permanently delete files and folders that have been in trash for more than 30 days'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days after which to permanently delete items (default: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']

        cutoff_date = timezone.now() - timedelta(days=days)

        self.stdout.write(self.style.SUCCESS(
            f"{'[DRY RUN] ' if dry_run else ''}Cleaning up trash older than {days} days "
            f"(deleted before {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')})"
        ))

        # Find old deleted files
        old_files = File.objects.filter(
            deleted_at__isnull=False,
            deleted_at__lt=cutoff_date
        )

        file_count = old_files.count()
        total_size = sum(f.size for f in old_files)

        # Find old deleted folders
        old_folders = Folder.objects.filter(
            deleted_at__isnull=False,
            deleted_at__lt=cutoff_date
        )

        folder_count = old_folders.count()

        if file_count == 0 and folder_count == 0:
            self.stdout.write(self.style.WARNING('No items to clean up.'))
            return

        # Display what will be deleted
        self.stdout.write(f"\nFound {file_count} file(s) and {folder_count} folder(s) to delete:")
        self.stdout.write(f"Total file size: {self._format_bytes(total_size)}")

        if not dry_run:
            # Delete files
            deleted_files = 0
            deleted_size = 0
            for file_obj in old_files:
                try:
                    file_size = file_obj.size
                    file_name = file_obj.name
                    owner = file_obj.owner.username

                    # Delete the actual file from storage
                    if file_obj.file:
                        file_obj.file.delete(save=False)

                    # Delete the database record
                    file_obj.delete()

                    deleted_files += 1
                    deleted_size += file_size

                    logger.info(
                        f"Permanently deleted file: {file_name} "
                        f"(owner: {owner}, size: {file_size} bytes)"
                    )

                except Exception as e:
                    logger.error(f"Error deleting file {file_obj.id}: {str(e)}")
                    self.stdout.write(self.style.ERROR(
                        f"Failed to delete file {file_obj.name}: {str(e)}"
                    ))

            # Delete folders
            deleted_folders = 0
            for folder_obj in old_folders:
                try:
                    folder_name = folder_obj.name
                    owner = folder_obj.owner.username

                    folder_obj.delete()

                    deleted_folders += 1

                    logger.info(
                        f"Permanently deleted folder: {folder_name} (owner: {owner})"
                    )

                except Exception as e:
                    logger.error(f"Error deleting folder {folder_obj.id}: {str(e)}")
                    self.stdout.write(self.style.ERROR(
                        f"Failed to delete folder {folder_obj.name}: {str(e)}"
                    ))

            # Summary
            self.stdout.write(self.style.SUCCESS(
                f"\nSuccessfully deleted:\n"
                f"  - {deleted_files} file(s) ({self._format_bytes(deleted_size)})\n"
                f"  - {deleted_folders} folder(s)"
            ))
        else:
            # Dry run - just show what would be deleted
            self.stdout.write(self.style.WARNING(
                "\n[DRY RUN] No items were actually deleted. Run without --dry-run to delete."
            ))

            # Show some examples
            self.stdout.write("\nExample files that would be deleted:")
            for file_obj in old_files[:5]:
                self.stdout.write(
                    f"  - {file_obj.name} ({self._format_bytes(file_obj.size)}) "
                    f"- deleted {file_obj.deleted_at.strftime('%Y-%m-%d')}"
                )

            if old_folders.count() > 0:
                self.stdout.write("\nExample folders that would be deleted:")
                for folder_obj in old_folders[:5]:
                    self.stdout.write(
                        f"  - {folder_obj.name} "
                        f"- deleted {folder_obj.deleted_at.strftime('%Y-%m-%d')}"
                    )

    def _format_bytes(self, bytes_val):
        """Format bytes into human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f} PB"
