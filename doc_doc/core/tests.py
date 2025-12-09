"""
Comprehensive test suite for doc-doc core application.

This module tests all major functionality including models, views, file uploads,
sharing, and security features.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
import uuid

from .models import Folder, File, Share
from .validators import validate_file_size, validate_file_extension, sanitize_filename


class TimeStampedModelTest(TestCase):
    """Test TimeStampedModel abstract base class."""

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'testpass123')

    def test_timestamps_auto_created(self):
        """Test that timestamps are automatically created."""
        folder = Folder.objects.create(name='Test Folder', owner=self.user)
        self.assertIsNotNone(folder.created_at)
        self.assertIsNotNone(folder.updated_at)


class FolderModelTest(TestCase):
    """Test Folder model functionality."""

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'testpass123')

    def test_create_folder(self):
        """Test basic folder creation."""
        folder = Folder.objects.create(name='My Folder', owner=self.user)
        self.assertEqual(folder.name, 'My Folder')
        self.assertEqual(folder.owner, self.user)
        self.assertIsNone(folder.parent)

    def test_folder_hierarchy(self):
        """Test parent-child folder relationships."""
        parent = Folder.objects.create(name='Parent', owner=self.user)
        child = Folder.objects.create(name='Child', owner=self.user, parent=parent)
        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.subfolders.all())

    def test_get_path(self):
        """Test folder path generation."""
        parent = Folder.objects.create(name='Parent', owner=self.user)
        child = Folder.objects.create(name='Child', owner=self.user, parent=parent)
        grandchild = Folder.objects.create(name='Grandchild', owner=self.user, parent=child)

        path = grandchild.get_path()
        self.assertEqual(len(path), 3)
        self.assertEqual([f.name for f in path], ['Parent', 'Child', 'Grandchild'])


class ShareModelTest(TestCase):
    """Test Share model functionality."""

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'testpass123')
        self.test_file = SimpleUploadedFile("test.txt", b"test content", content_type="text/plain")
        self.file = File.objects.create(name='test.txt', file=self.test_file, owner=self.user)

    def test_create_share(self):
        """Test basic share creation."""
        share = Share.objects.create(file=self.file, is_active=True)
        self.assertIsInstance(share.id, uuid.UUID)
        self.assertTrue(share.is_active)
        self.assertEqual(share.access_count, 0)

    def test_share_password_hashing(self):
        """Test password hashing for shares."""
        share = Share.objects.create(file=self.file)
        raw_password = 'mysecretpassword'

        # Set password
        share.set_password(raw_password)
        self.assertIsNotNone(share.password)
        self.assertNotEqual(share.password, raw_password)

        # Check password
        self.assertTrue(share.check_password(raw_password))
        self.assertFalse(share.check_password('wrongpassword'))

    def test_increment_access_count(self):
        """Test access count tracking."""
        share = Share.objects.create(file=self.file)
        self.assertEqual(share.access_count, 0)

        share.increment_access_count()
        self.assertEqual(share.access_count, 1)


class FileValidatorTest(TestCase):
    """Test file validation functions."""

    def test_file_size_validation(self):
        """Test file size validator."""
        # File within limit
        small_file = SimpleUploadedFile("test.txt", b"x" * 1024)  # 1KB
        try:
            validate_file_size(small_file)
        except ValidationError:
            self.fail("validate_file_size raised ValidationError unexpectedly")

        # File exceeds limit
        large_file = SimpleUploadedFile("large.txt", b"x" * 15 * 1024 * 1024)  # 15MB
        with self.assertRaises(ValidationError):
            validate_file_size(large_file)

    def test_file_extension_validation(self):
        """Test file extension validator."""
        # Safe extension
        safe_file = SimpleUploadedFile("test.txt", b"content")
        try:
            validate_file_extension(safe_file)
        except ValidationError:
            self.fail("validate_file_extension raised ValidationError unexpectedly")

        # Dangerous extension
        dangerous_file = SimpleUploadedFile("malware.exe", b"content")
        with self.assertRaises(ValidationError):
            validate_file_extension(dangerous_file)

    def test_filename_sanitization(self):
        """Test filename sanitization."""
        # Path traversal attempt
        dangerous_name = "../../etc/passwd"
        sanitized = sanitize_filename(dangerous_name)
        self.assertEqual(sanitized, "passwd")

        # Null byte injection
        null_name = "file\x00.txt"
        sanitized = sanitize_filename(null_name)
        self.assertNotIn('\x00', sanitized)


class DashboardViewTest(TestCase):
    """Test Dashboard view."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('testuser', 'test@example.com', 'testpass123')
        self.client.login(username='testuser', password='testpass123')

    def test_dashboard_requires_login(self):
        """Test that dashboard requires authentication."""
        self.client.logout()
        response = self.client.get(reverse('dashboard'))
        self.assertIn(response.status_code, [302, 403])
