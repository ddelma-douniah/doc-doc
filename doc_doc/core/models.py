"""
Core models for the doc-doc application.

This module contains the data models for folders, files, and sharing functionality.
"""

import uuid
from typing import Optional

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class TimeStampedModel(models.Model):
    """
    Abstract base model that provides self-updating created and modified fields.
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text=_("Timestamp when the record was created")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("Timestamp when the record was last updated")
    )

    class Meta:
        abstract = True


class Folder(TimeStampedModel):
    """
    Represents a folder in the file system hierarchy.

    Folders can contain other folders (subfolders) and files, creating a tree structure.
    Each folder belongs to a single owner and can have one parent folder.
    """

    name = models.CharField(
        max_length=255,
        db_index=True,
        help_text=_("Name of the folder")
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subfolders',
        help_text=_("Parent folder, if this is a subfolder")
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='folders',
        db_index=True,
        help_text=_("Owner of the folder")
    )
    is_favorite = models.BooleanField(
        default=False,
        db_index=True,
        help_text=_("Whether this folder is marked as favorite")
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Timestamp when the folder was moved to trash")
    )

    class Meta:
        verbose_name = _("Folder")
        verbose_name_plural = _("Folders")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'parent']),
            models.Index(fields=['owner', 'created_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['owner', 'parent', 'name'],
                name='unique_folder_name_per_parent'
            )
        ]

    def __str__(self) -> str:
        """Return the folder name."""
        return self.name

    def clean(self) -> None:
        """
        Validate the folder instance.

        Raises:
            ValidationError: If the folder would create a circular reference.
        """
        super().clean()
        if self.parent and self._is_circular_reference():
            raise ValidationError(
                _("Cannot set parent: circular reference detected.")
            )

    def _is_circular_reference(self) -> bool:
        """
        Check if setting this parent would create a circular reference.

        Returns:
            bool: True if circular reference would be created, False otherwise.
        """
        current = self.parent
        while current:
            if current.id == self.id:
                return True
            current = current.parent
        return False

    def get_path(self) -> str:
        """
        Get the full path of the folder from root to this folder.

        Returns:
            str: The full path, e.g., "Documents/Projects/Python"
        """
        path_parts = [self.name]
        current = self.parent
        while current:
            path_parts.insert(0, current.name)
            current = current.parent
        return '/'.join(path_parts)

    def get_size(self) -> int:
        """
        Calculate total size of all files in this folder and subfolders.

        Returns:
            int: Total size in bytes.
        """
        size = sum(f.file.size for f in self.files.filter(deleted_at__isnull=True) if f.file)
        for subfolder in self.subfolders.filter(deleted_at__isnull=True):
            size += subfolder.get_size()
        return size

    def move_to_trash(self) -> None:
        """Move this folder and all its contents to trash (soft delete)."""
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])
        # Also trash all subfolders and files
        for subfolder in self.subfolders.all():
            subfolder.move_to_trash()
        for file in self.files.all():
            file.move_to_trash()

    def restore_from_trash(self) -> None:
        """Restore this folder and all its contents from trash."""
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])
        # Also restore all subfolders and files
        for subfolder in self.subfolders.all():
            subfolder.restore_from_trash()
        for file in self.files.all():
            file.restore_from_trash()

    def toggle_favorite(self) -> None:
        """Toggle favorite status."""
        self.is_favorite = not self.is_favorite
        self.save(update_fields=['is_favorite'])


class File(TimeStampedModel):
    """
    Represents a file in the system.

    Files can be stored in folders or at the root level. Each file belongs to
    a single owner and contains the actual file data stored in S3/MinIO.
    """

    name = models.CharField(
        max_length=255,
        db_index=True,
        help_text=_("Name of the file")
    )
    folder = models.ForeignKey(
        Folder,
        on_delete=models.CASCADE,
        related_name='files',
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Folder containing this file")
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='files',
        db_index=True,
        help_text=_("Owner of the file")
    )
    file = models.FileField(
        upload_to='files/%Y/%m/%d/',
        help_text=_("The actual file")
    )
    size = models.BigIntegerField(
        default=0,
        help_text=_("File size in bytes")
    )
    mime_type = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("MIME type of the file")
    )
    is_favorite = models.BooleanField(
        default=False,
        db_index=True,
        help_text=_("Whether this file is marked as favorite")
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Timestamp when the file was moved to trash")
    )
    last_accessed = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Last time the file was accessed/viewed")
    )

    class Meta:
        verbose_name = _("File")
        verbose_name_plural = _("Files")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'folder']),
            models.Index(fields=['owner', 'created_at']),
        ]

    def __str__(self) -> str:
        """Return the file name."""
        return self.name

    def save(self, *args, **kwargs) -> None:
        """
        Override save to populate size and mime_type automatically.
        """
        if self.file:
            self.size = self.file.size
            # Basic MIME type detection
            if not self.mime_type:
                self.mime_type = self._detect_mime_type()
        super().save(*args, **kwargs)

    def _detect_mime_type(self) -> str:
        """
        Detect MIME type based on file extension.

        Returns:
            str: MIME type string.
        """
        import mimetypes
        mime_type, _ = mimetypes.guess_type(self.name)
        return mime_type or 'application/octet-stream'

    def get_path(self) -> str:
        """
        Get the full path of the file including folder path.

        Returns:
            str: The full path, e.g., "Documents/Projects/file.pdf"
        """
        if self.folder:
            return f"{self.folder.get_path()}/{self.name}"
        return self.name

    @property
    def formatted_size(self) -> str:
        """
        Get human-readable file size.

        Returns:
            str: Formatted size string, e.g., "1.5 MB"
        """
        size = self.size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def move_to_trash(self) -> None:
        """Move this file to trash (soft delete)."""
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def restore_from_trash(self) -> None:
        """Restore this file from trash."""
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])

    def toggle_favorite(self) -> None:
        """Toggle favorite status."""
        self.is_favorite = not self.is_favorite
        self.save(update_fields=['is_favorite'])

    def mark_accessed(self) -> None:
        """Update last_accessed timestamp."""
        self.last_accessed = timezone.now()
        self.save(update_fields=['last_accessed'])


class Share(TimeStampedModel):
    """
    Represents a sharing link for a file or folder.

    Shares can have expiration dates and optional passwords for security.
    A share can also specify specific users who have access.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique share identifier")
    )
    file = models.ForeignKey(
        File,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='shares',
        help_text=_("File being shared")
    )
    folder = models.ForeignKey(
        Folder,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='shares',
        help_text=_("Folder being shared")
    )
    shared_with = models.ManyToManyField(
        User,
        blank=True,
        related_name='shared_with_me',
        help_text=_("Specific users who can access this share")
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text=_("When this share link expires")
    )
    password = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text=_("Optional password to access the share")
    )
    access_count = models.PositiveIntegerField(
        default=0,
        help_text=_("Number of times this share has been accessed")
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text=_("Whether this share is currently active")
    )

    class Meta:
        verbose_name = _("Share")
        verbose_name_plural = _("Shares")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'expires_at']),
        ]

    def __str__(self) -> str:
        """Return a string representation of the share."""
        if self.file:
            return f"Share of {self.file.name}"
        elif self.folder:
            return f"Share of {self.folder.name}"
        return f"Share {self.id}"

    def clean(self) -> None:
        """
        Validate the share instance.

        Raises:
            ValidationError: If both file and folder are set, or neither is set.
        """
        super().clean()
        if self.file and self.folder:
            raise ValidationError(
                _("A share cannot have both a file and a folder.")
            )
        if not self.file and not self.folder:
            raise ValidationError(
                _("A share must have either a file or a folder.")
            )

    def is_expired(self) -> bool:
        """
        Check if this share has expired.

        Returns:
            bool: True if the share has expired, False otherwise.
        """
        from django.utils import timezone
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    def increment_access_count(self) -> None:
        """Increment the access count for this share."""
        self.access_count += 1
        self.save(update_fields=['access_count'])

    def set_password(self, raw_password: str) -> None:
        """
        Set the password for this share (hashed).

        Args:
            raw_password: The plaintext password to hash and store.
        """
        if raw_password:
            self.password = make_password(raw_password)
        else:
            self.password = None

    def check_password(self, raw_password: str) -> bool:
        """
        Check if the provided password matches the stored hash.

        Args:
            raw_password: The plaintext password to check.

        Returns:
            bool: True if password matches, False otherwise.
        """
        if not self.password:
            return True
        return check_password(raw_password, self.password)

    def get_shared_object(self):
        """
        Get the file or folder being shared.

        Returns:
            File or Folder: The shared object.
        """
        return self.file if self.file else self.folder
