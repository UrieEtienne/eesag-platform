from django.core.management.base import BaseCommand, CommandError

from apps.accounts.services_sms import envoyer_otp_supabase


class Command(BaseCommand):
    help = "Teste l'envoi d'un OTP SMS via Supabase Auth."

    def add_arguments(self, parser):
        parser.add_argument("telephone")

    def handle(self, *args, **options):
        result = envoyer_otp_supabase(options["telephone"], creer_utilisateur=True)
        if not result.get("ok"):
            raise CommandError(result.get("error", "Échec OTP Supabase"))
        self.stdout.write(
            self.style.SUCCESS(
                f"OTP accepté par Supabase vers {result.get('to')} (fournisseur: supabase)"
            )
        )
