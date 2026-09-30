from django.core.management.base import BaseCommand, CommandError

from apps.accounts.services_sms import envoyer_otp, normaliser_telephone


class Command(BaseCommand):
    help = "Teste l'envoi d'un SMS OTP via l'API FastAPI/Twilio."

    def add_arguments(self, parser):
        parser.add_argument("telephone")

    def handle(self, *args, **options):
        try:
            numero = normaliser_telephone(options["telephone"])
        except ValueError as exc:
            raise CommandError(str(exc))
        self.stdout.write(f"Numéro normalisé : {numero}")
        result = envoyer_otp(numero, origine="EESAG")
        if not result.get("ok"):
            raise CommandError(result.get("error", "Échec de l'envoi SMS."))
        self.stdout.write(self.style.SUCCESS(
            f"SMS OTP accepté par Twilio pour {numero}. SID={result.get('sid', '')}"
        ))
