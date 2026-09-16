from django.core.management.base import BaseCommand, CommandError

from apps.accounts.services_sms import envoyer_otp_supabase, normaliser_telephone


class Command(BaseCommand):
    help = "Teste la normalisation et l'envoi d'un OTP SMS via Supabase Auth."

    def add_arguments(self, parser):
        parser.add_argument("telephone")

    def handle(self, *args, **options):
        telephone = options["telephone"]
        try:
            numero = normaliser_telephone(telephone)
        except ValueError as exc:
            raise CommandError(str(exc))

        self.stdout.write(f"Numéro normalisé : {numero}")
        result = envoyer_otp_supabase(numero, creer_utilisateur=True)
        if not result.get("ok"):
            raise CommandError(result.get("error", "Échec OTP Supabase"))
        self.stdout.write(
            self.style.SUCCESS(
                f"Supabase a accepté la demande OTP pour {numero}. Vérifiez maintenant le téléphone."
            )
        )
