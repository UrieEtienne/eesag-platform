from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Vérifie la configuration locale Supabase utilisée par EESAG sans afficher de secret."

    def handle(self, *args, **options):
        url = str(getattr(settings, "SUPABASE_URL", "") or "").strip()
        key = str(getattr(settings, "SUPABASE_PUBLISHABLE_KEY", "") or "").strip()
        provider = str(getattr(settings, "SMS_PROVIDER", "") or "").strip().lower()

        self.stdout.write(f"SMS_PROVIDER = {provider or '(vide)'}")
        self.stdout.write(f"SUPABASE_URL = {'OK' if url else 'MANQUANT'}")
        self.stdout.write(f"SUPABASE_PUBLISHABLE_KEY = {'OK' if key else 'MANQUANT'}")

        if url and not url.startswith(("https://", "http://")):
            self.stdout.write(self.style.ERROR("SUPABASE_URL doit commencer par https:// ou http://"))
        if key and (key.startswith("sb_secret_") or key.startswith("service_role")):
            self.stdout.write(self.style.ERROR("N'utilisez pas une clé secrète/service_role pour cette intégration OTP. Utilisez la Publishable key côté client/Auth."))

        if provider == "supabase" and url and key and url.startswith(("https://", "http://")):
            self.stdout.write(self.style.SUCCESS("Configuration Django locale : OK"))
            self.stdout.write("Étape suivante : activez Authentication → Providers → Phone dans Supabase et configurez le fournisseur SMS.")
        else:
            self.stdout.write(self.style.ERROR("Configuration incomplète : renseignez backend/.env avant de tester un OTP."))
