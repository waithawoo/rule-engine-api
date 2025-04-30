from django.core.management.base import BaseCommand

from apps.authentication.models import User


class Command(BaseCommand):
    help = 'Create a client user easily'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, required=True, help='Email for client')
        parser.add_argument('--password', type=str, required=True, help='Password for client')

    def handle(self, *args, **kwargs):
        email = kwargs['email']
        password = kwargs['password']

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f"Email '{email}' already exists."))
        else:
            user = User.objects.create_user(
                email=email,
                password=password,
                role='client'
            )
            self.stdout.write(self.style.SUCCESS(f"Client email '{email}' created successfully."))
