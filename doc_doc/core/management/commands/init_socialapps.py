"""
Management command to initialize Social Apps for django-allauth.
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = 'Initialize SocialApp objects for Google and GitHub OAuth providers'

    def handle(self, *args, **options):
        """Create or update SocialApp objects from environment variables."""
        site = Site.objects.get_current()

        # Google OAuth
        google_client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '')
        google_client_secret = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', '')

        if google_client_id and google_client_secret:
            google_app, created = SocialApp.objects.get_or_create(
                provider='google',
                defaults={
                    'name': 'Google',
                    'client_id': google_client_id,
                    'secret': google_client_secret,
                }
            )
            if not created:
                google_app.client_id = google_client_id
                google_app.secret = google_client_secret
                google_app.save()

            google_app.sites.add(site)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully {"created" if created else "updated"} Google SocialApp')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Skipping Google OAuth: GOOGLE_OAUTH_CLIENT_ID or GOOGLE_OAUTH_CLIENT_SECRET not set')
            )

        # GitHub OAuth
        github_client_id = os.environ.get('GITHUB_OAUTH_CLIENT_ID', '')
        github_client_secret = os.environ.get('GITHUB_OAUTH_CLIENT_SECRET', '')

        if github_client_id and github_client_secret:
            github_app, created = SocialApp.objects.get_or_create(
                provider='github',
                defaults={
                    'name': 'GitHub',
                    'client_id': github_client_id,
                    'secret': github_client_secret,
                }
            )
            if not created:
                github_app.client_id = github_client_id
                github_app.secret = github_client_secret
                github_app.save()

            github_app.sites.add(site)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully {"created" if created else "updated"} GitHub SocialApp')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Skipping GitHub OAuth: GITHUB_OAUTH_CLIENT_ID or GITHUB_OAUTH_CLIENT_SECRET not set')
            )

        self.stdout.write(self.style.SUCCESS('SocialApp initialization complete'))
