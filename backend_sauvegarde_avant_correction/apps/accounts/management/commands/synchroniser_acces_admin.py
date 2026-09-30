from django.core.management.base import BaseCommand

from apps.accounts.models import Role, Utilisateur, ROLES_NATIONAUX


class Command(BaseCommand):
    help = "Synchronise l'accès Django Admin selon le rôle et l'état de l'église."

    def handle(self, *args, **options):
        comptes_nationaux = Utilisateur.objects.filter(role__in=ROLES_NATIONAUX).exclude(role=Role.COORDINATEUR).update(is_staff=True)
        comptes_coord = Utilisateur.objects.filter(role=Role.COORDINATEUR).update(is_staff=True)

        locaux = Utilisateur.objects.filter(role__in=[Role.ADMIN_LOCAL, Role.PASTEUR]).select_related("eglise")
        actifs = 0
        bloques = 0
        for user in locaux.iterator():
            autorise = bool(user.eglise_id and user.eglise.plateforme_active and user.actif)
            if user.is_staff != autorise:
                user.is_staff = autorise
                user.save(update_fields=["is_staff"])
            if autorise:
                actifs += 1
            else:
                bloques += 1

        membres = Utilisateur.objects.filter(role__in=[Role.MEMBRE, Role.RESPONSABLE_DEPARTEMENT]).update(is_staff=False)

        self.stdout.write(self.style.SUCCESS(
            f"Accès Admin synchronisé : {comptes_coord} Coordinateur(s), "
            f"{comptes_nationaux} compte(s) nationaux, {actifs} compte(s) locaux actifs, "
            f"{bloques} compte(s) locaux bloqués, {membres} membre(s) sans accès Admin."
        ))
