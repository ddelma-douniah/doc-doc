"""
Custom email backend with graceful error handling.

Falls back to console backend if SMTP fails.
"""
import logging
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend
from django.core.mail.backends.console import EmailBackend as ConsoleBackend

logger = logging.getLogger(__name__)


class GracefulEmailBackend(SMTPBackend):
    """
    Email backend that gracefully handles SMTP failures.

    If sending via SMTP fails, it logs the error and falls back to console output
    instead of crashing the application.
    """

    def __init__(self, *args, **kwargs):
        self.console_backend = None
        super().__init__(*args, **kwargs)

    def send_messages(self, email_messages):
        """
        Send messages via SMTP, fall back to console if it fails.

        Args:
            email_messages: List of email messages to send

        Returns:
            Number of messages sent
        """
        try:
            return super().send_messages(email_messages)
        except Exception as e:
            logger.error(
                f"SMTP email sending failed: {e}. "
                f"Falling back to console output. "
                f"Please configure EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env file."
            )

            # Fall back to console backend
            if self.console_backend is None:
                self.console_backend = ConsoleBackend()

            try:
                return self.console_backend.send_messages(email_messages)
            except Exception as console_error:
                logger.error(f"Console backend also failed: {console_error}")
                return 0
