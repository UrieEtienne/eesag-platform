
from apps.accounts.models import Role, ROLES_BUREAU_NATIONAL

from .models import (
    Bureau,
    BureauAdministrateur,
    NiveauBureau,
    TypeBureau,
)


# ============================================================
# RÔLES ET IDENTIFICATION
# ============================================================

def _est_coordinateur(user):
    """
    Seul le rôle COORDINATEUR donne les droits globaux.
    is_superuser ne suffit jamais à devenir Coordinateur.
    """
    return bool(
        user
        and user.is_authenticated
        and user.role == Role.COORDINATEUR
    )


def _bureaux_administres(user):
    """
    Bureaux pour lesquels le compte possède une affectation active.
    """
    if not user or not user.is_authenticated:
        return Bureau.objects.none()

    return (
        Bureau.objects.filter(
            administrateurs__utilisateur=user,
            administrateurs__actif=True,
            actif=True,
        )
        .distinct()
    )


def _administration_bureau(user, bureau):
    """
    Retourne l'affectation active exacte d'un utilisateur
    sur un bureau donné.
    """
    if not user or not user.is_authenticated or not bureau:
        return None

    return (
        BureauAdministrateur.objects.filter(
            bureau=bureau,
            utilisateur=user,
            actif=True,
            bureau__actif=True,
        )
        .first()
    )


# ============================================================
# BUREAU NATIONAL GÉNÉRAL
# ============================================================

def _bureau_national_general():
    return (
        Bureau.objects.filter(
            niveau=NiveauBureau.NATIONAL,
            type_bureau=TypeBureau.GENERAL,
            eglise__isnull=True,
            actif=True,
        )
        .first()
    )


def _est_national_general(user):
    """
    Un compte est responsable du Bureau national général
    uniquement s'il est explicitement affecté à ce bureau.
    """
    if not user or not user.is_authenticated:
        return False

    if _est_coordinateur(user):
        return False

    if user.role not in ROLES_BUREAU_NATIONAL:
        return False

    bureau_general = _bureau_national_general()

    if not bureau_general:
        return False

    return _administration_bureau(
        user,
        bureau_general,
    ) is not None


def est_bureau_national_principal(bureau):
    """
    Compatibilité avec les anciens appels.
    Le bureau principal est désormais le bureau GENERAL.
    """
    return bool(
        bureau
        and bureau.niveau == NiveauBureau.NATIONAL
        and bureau.type_bureau == TypeBureau.GENERAL
        and not bureau.eglise_id
    )


# Ancien nom conservé pour éviter de casser les imports existants.
def _bureau_national_hommes():
    return _bureau_national_general()


# ============================================================
# BUREAUX NATIONAUX SPÉCIALISÉS
# ============================================================

BUREAUX_NATIONAUX_SECONDAIRES = {
    TypeBureau.FEMMES,
    TypeBureau.JEUNESSE,
    TypeBureau.ENFANTS,
    TypeBureau.EVANGELISATION,
    TypeBureau.COMMUNICATION,
    TypeBureau.MUSIQUE,
}

BUREAUX_NATIONAUX_ZONAUX = {
    TypeBureau.FEMMES,
    TypeBureau.JEUNESSE,
    TypeBureau.ENFANTS,
}


def est_bureau_national_secondaire(bureau):
    return bool(
        bureau
        and bureau.niveau == NiveauBureau.NATIONAL
        and bureau.type_bureau in BUREAUX_NATIONAUX_SECONDAIRES
        and not bureau.eglise_id
    )


# ============================================================
# CRÉATION DES BUREAUX NATIONAUX
# ============================================================

def peut_creer_bureau_national(user):
    """
    Coordinateur :
        peut créer les bureaux nationaux.

    Bureau national général :
        peut créer les bureaux spécialisés uniquement si
        son affectation active possède peut_creer_bureaux=True.

    Bureau spécialisé :
        ne peut pas créer un autre bureau national.
    """
    if not user or not user.is_authenticated:
        return False

    if _est_coordinateur(user):
        return True

    bureau_general = _bureau_national_general()

    if not bureau_general:
        return False

    attribution = _administration_bureau(
        user,
        bureau_general,
    )

    return bool(
        attribution
        and attribution.peut_creer_bureaux
    )


# ============================================================
# DROITS SUR UN BUREAU
# ============================================================

def a_droit_bureau(user, bureau, droit):
    """
    Les droits sont accordés par affectation explicite.

    Exception :
        le Coordinateur possède les droits globaux.

    Un administrateur local ou un pasteur ne reçoit pas
    automatiquement des droits sur tous les bureaux de son église.
    """
    if not user or not user.is_authenticated or not bureau:
        return False

    if _est_coordinateur(user):
        return True

    attribution = _administration_bureau(
        user,
        bureau,
    )

    if not attribution:
        return False

    return bool(
        getattr(attribution, droit, False)
    )
