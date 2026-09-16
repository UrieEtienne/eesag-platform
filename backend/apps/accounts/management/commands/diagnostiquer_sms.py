from django.core.management.base import BaseCommand
from apps.accounts.services_sms import diagnostic_sms


class Command(BaseCommand):
    help = "Diagnostique la configuration de l'API SMS FastAPI/Twilio."

    def handle(self, *args, **options):
        data = diagnostic_sms()
        for key, value in data.items():
            self.stdout.write(f"{key} = {value}")
