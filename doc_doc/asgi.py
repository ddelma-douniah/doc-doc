"""
ASGI config for doc_doc project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "doc_doc.settings")

# Initialize Django ASGI application early to ensure apps are loaded
django_asgi_app = get_asgi_application()


async def application(scope, receive, send):
    """
    ASGI application with lifespan support to prevent warnings.
    """
    if scope['type'] == 'lifespan':
        # Handle lifespan events
        while True:
            message = await receive()
            if message['type'] == 'lifespan.startup':
                await send({'type': 'lifespan.startup.complete'})
            elif message['type'] == 'lifespan.shutdown':
                await send({'type': 'lifespan.shutdown.complete'})
                return
    else:
        # Delegate all other requests to Django
        await django_asgi_app(scope, receive, send)
