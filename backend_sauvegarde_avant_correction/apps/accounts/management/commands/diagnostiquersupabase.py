from django.core.management.base import BaseCommand
from django.conf import settings
from apps.accounts.services_sms import diagnostic_sms


class Command(BaseCommand):
    help = "Diagnostique le service SMS FastAPI/Twilio (ancien nom conservé pour compatibilité)."

    def handle(self, *args, **options):
        data = diagnostic_sms()
        self.stdout.write(f"SMS_PROVIDER = {data['provider']}")
        self.stdout.write(f"SMS_API_URL = {'OK' if data['sms_api_url_present'] else 'MANQUANT'}")
        self.stdout.write(f"SMS_API_KEY = {'OK' if data['sms_api_key_present'] else 'MANQUANT'}")
        self.stdout.write(f"TIMEOUT = {getattr(settings, 'SMS_REQUEST_TIMEOUT', 20)}s")
        self.stdout.write("Les secrets Twilio restent dans sms_api/.env.")
