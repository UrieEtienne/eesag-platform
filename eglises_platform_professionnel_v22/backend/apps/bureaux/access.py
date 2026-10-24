from apps.accounts.models import Role, ROLES_BUREAU_NATIONAL
from .models import Bureau, BureauAdministrateur, NiveauBureau


def _est_coordinateur(user):
    return bool(
        user
        and user.is_authenticated
        and (
            user.role == Role.COORDINATEUR
            or user.is_superuser
        )
    )


def _est_national_general(user):
    if not user or not user.is_authenticated:
        return False

    if _est_coordinateur(user):
        return True

    if user.role not in ROLES_BUREAU_NATIONAL:
        return False

    return not BureauAdministrateur.objects.filter(
        utilisateur=user,
        actif=True,
    ).exists()


def _bureaux_administres(user):
    if not user or not user.is_authenticated:
        return Bureau.objects.none()

    return Bureau.objects.filter(
        administrateurs__utilisateur=user,
        administrateurs__actif=True,
        actif=True,
    ).distinct()


def a_droit_bureau(user, bureau, droit):
    if not user or not user.is_authenticated:
        return False

    if _est_coordinateur(user):
        return True

    attribution = BureauAdministrateur.objects.filter(
        bureau=bureau,
        utilisateur=user,
        actif=True,
        bureau__actif=True,
    ).first()

    if attribution:
        return bool(getattr(attribution, droit, False))

    if (
        user.role in (Role.ADMIN_LOCAL, Role.PASTEUR)
        and bureau.niveau == NiveauBureau.LOCAL
        and bureau.eglise_id == user.eglise_id
    ):
        return droit in {
            "peut_gerer_membres",
            "peut_gerer_finances",
            "peut_gerer_projets",
            "peut_envoyer_notifications",
            "peut_gerer_rapports",
        }

    return False


def _bureau_national_hommes():
    return Bureau.objects.filter(
        niveau=NiveauBureau.NATIONAL,
        type_bureau="HOMMES",
        eglise__isnull=True,
    ).first()
