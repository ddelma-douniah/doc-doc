"""
Custom middleware for error handling and logging.
"""
import logging
import traceback
from django.http import HttpResponseServerError
from django.shortcuts import render
from django.conf import settings

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware:
    """
    Middleware to catch and handle all unhandled exceptions gracefully.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            return self.handle_exception(request, e)

    def handle_exception(self, request, exception):
        """
        Handle exceptions and return appropriate error response.

        Args:
            request: The HTTP request object
            exception: The exception that was raised

        Returns:
            HTTP 500 response with error page
        """
        # Log the full traceback
        logger.error(
            f"Unhandled exception in {request.path}:\n"
            f"User: {request.user if request.user.is_authenticated else 'Anonymous'}\n"
            f"Method: {request.method}\n"
            f"Error: {str(exception)}\n"
            f"Traceback:\n{traceback.format_exc()}"
        )

        # In debug mode, let Django handle it (shows nice debug page)
        if settings.DEBUG:
            raise exception

        # In production, show custom 500 page
        try:
            return render(request, '500.html', status=500)
        except Exception as render_error:
            # If even rendering fails, return a basic error response
            logger.error(f"Failed to render 500 page: {render_error}")
            return HttpResponseServerError(
                b"<h1>500 Internal Server Error</h1>"
                b"<p>Something went wrong. Please try again later.</p>"
            )

    def process_exception(self, request, exception):
        """
        Django middleware hook for exception processing.

        Args:
            request: The HTTP request object
            exception: The exception that was raised

        Returns:
            HTTP response or None
        """
        return self.handle_exception(request, exception)
