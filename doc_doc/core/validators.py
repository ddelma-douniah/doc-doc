"""
File validation utilities for doc-doc application.

This module provides validators for uploaded files to ensure security and data integrity.
"""

import os
import mimetypes
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_file_size(file):
    """
    Validate that the uploaded file does not exceed the maximum allowed size.

    Args:
        file: The uploaded file object.

    Raises:
        ValidationError: If the file size exceeds the limit.
    """
    max_size = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 10485760)
    if file.size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        raise ValidationError(
            _('File size must not exceed %(max_size).1f MB. Your file is %(file_size).1f MB.') % {
                'max_size': max_size_mb,
                'file_size': file.size / (1024 * 1024)
            }
        )


def validate_file_extension(file):
    """
    Validate that the file extension is not in the forbidden list.

    Args:
        file: The uploaded file object.

    Raises:
        ValidationError: If the file extension is forbidden.
    """
    ext = os.path.splitext(file.name)[1][1:].lower()
    forbidden = getattr(settings, 'FORBIDDEN_EXTENSIONS', set())

    if ext in forbidden:
        raise ValidationError(
            _('Files with extension ".%(ext)s" are not allowed for security reasons.') % {'ext': ext}
        )


def validate_file_mimetype(file):
    """
    Validate that the file MIME type is in the allowed list.

    Args:
        file: The uploaded file object.

    Raises:
        ValidationError: If the file MIME type is not allowed.
    """
    allowed_types = getattr(settings, 'ALLOWED_FILE_TYPES', set())

    if not allowed_types:
        return

    # Try to guess MIME type from file name
    mime_type, _ = mimetypes.guess_type(file.name)

    # Also check content_type from the uploaded file
    content_type = getattr(file, 'content_type', None)

    # Accept if either matches
    if mime_type not in allowed_types and content_type not in allowed_types:
        raise ValidationError(
            _('File type "%(mime_type)s" is not allowed. Allowed types: %(allowed)s') % {
                'mime_type': content_type or mime_type or 'unknown',
                'allowed': ', '.join(sorted(allowed_types))
            }
        )


def sanitize_filename(filename):
    """
    Sanitize filename to prevent path traversal and other security issues.

    Args:
        filename: The original filename.

    Returns:
        str: The sanitized filename.
    """
    # Get just the base name (no path components)
    filename = os.path.basename(filename)

    # Remove any null bytes
    filename = filename.replace('\x00', '')

    # Limit filename length
    name, ext = os.path.splitext(filename)
    max_name_length = 200
    if len(name) > max_name_length:
        name = name[:max_name_length]

    return name + ext


def validate_file(file):
    """
    Run all file validation checks.

    Args:
        file: The uploaded file object.

    Raises:
        ValidationError: If any validation check fails.
    """
    validate_file_size(file)
    validate_file_extension(file)
    validate_file_mimetype(file)
