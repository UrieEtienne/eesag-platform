from apps.accounts.models import (
    Role,
    ROLES_BUREAU_NATIONAL,
)

from .models import (
    Bureau,
    BureauAdministrateur,
    NiveauBureau,
    TypeBureau,
)


# ============================================================
# UTILISATEURS / RÔLES
# ============================================================

def _est_coordinateur(user):
    """
    Seul le rôle métier COORDINATEUR donne les droits de Coordinateur.
    is_superuser ne donne aucun privilège métier supplémentaire.
    """
    return bool(
        user
        and user.is_authenticated
        and user.role == Role.COORDINATEUR
    )


def _bureaux_administres(user):
    """
    Retourne les bureaux pour lesquels l'utilisateur possède
    une affectation d'administrateur active.
    """
    if not user or not user.is_authenticated:
        return Bureau.objects.none()

    return (
        Bureau.objects
        .filter(
            administrateurs__utilisateur=user,
            administrateurs__actif=True,
        )
        .distinct()
    )


# ============================================================
# BUREAU NATIONAL GÉNÉRAL
# ============================================================

def _est_national_general(user):
    """
    Un compte national sans affectation active à un bureau
    national est considéré comme relevant du périmètre général.
    """
    if not user or not user.is_authenticated:
        return False

    if _est_coordinateur(user):
        return False

    if user.role not in ROLES_BUREAU_NATIONAL:
        return False

    return not BureauAdministrateur.objects.filter(
        utilisateur=user,
        actif=True,
        bureau__niveau=NiveauBureau.NATIONAL,
        bureau__eglise__isnull=True,
    ).exists()


# ============================================================
# BUREAU NATIONAL PRINCIPAL
# ============================================================

def est_bureau_national_principal(bureau):
    """Le bureau national principal est l'unique bureau GENERAL."""
    return bool(
        bureau
        and bureau.niveau == NiveauBureau.NATIONAL
        and bureau.type_bureau == TypeBureau.GENERAL
        and not bureau.eglise_id
    )


def _bureau_national_general():
    """Retourne le bureau national général, s'il existe."""
    return (
        Bureau.objects.filter(
            niveau=NiveauBureau.NATIONAL,
            type_bureau=TypeBureau.GENERAL,
            eglise__isnull=True,
        ).first()
    )


def _bureau_national_hommes():
    """
    Alias de compatibilité pour les anciens appels.
    Le bureau principal est désormais de type GENERAL.
    """
    return _bureau_national_general()


# ============================================================
# BUREAUX NATIONAUX SPÉCIALISÉS
# ============================================================

BUREAUX_NATIONAUX_SECONDAIRES = {
    TypeBureau.FEMMES,
    TypeBureau.JEUNESSE,
    TypeBureau.ENFANTS,
}


def est_bureau_national_secondaire(bureau):
    """Vérifie qu'un bureau appartient aux trois types spécialisés."""
    return bool(
        bureau
        and bureau.niveau == NiveauBureau.NATIONAL
        and bureau.type_bureau in BUREAUX_NATIONAUX_SECONDAIRES
        and not bureau.eglise_id
    )


# CRÉATION DES BUREAUX NATIONAUX
# ============================================================

def peut_creer_bureau_national(user):
    """
    Autorisation de créer un bureau national.

    Règle métier :

        Coordinateur
              │
              └── peut créer les bureaux nationaux

        Bureau national des Hommes
              │
              ├── Femmes
              ├── Jeunesse
              └── Enfants

    Un simple compte national général ne peut pas créer
    directement un bureau national.

    Un administrateur d'un bureau national spécialisé ne peut
    pas non plus créer un autre bureau national, sauf s'il
    possède explicitement le droit peut_creer_bureaux.
    """
    if not user or not user.is_authenticated:
        return False

    if _est_coordinateur(user):
        return True

    bureau_hommes = _bureau_national_hommes()

    if not bureau_hommes:
        return False

    # Un administrateur du Bureau national des Hommes
    # peut créer les trois autres bureaux.
    return BureauAdministrateur.objects.filter(
        bureau=bureau_hommes,
        utilisateur=user,
        actif=True,
        peut_creer_bureaux=True,
    ).exists()


# ============================================================
# DROITS SUR UN BUREAU
# ============================================================

def a_droit_bureau(user, bureau, droit):
    """
    Vérifie une autorisation explicite sur un bureau.

    Aucun droit financier n'est accordé automatiquement
    en fonction du rôle technique.
    """
    if not user or not user.is_authenticated or not bureau:
        return False

    # Le Coordinateur ne reçoit pas de droits financiers
    # ni de droits internes par simple privilège global.
    if _est_coordinateur(user):
        return False

    # Les droits des comptes nationaux sont exclusivement
    # ceux de leur affectation active dans ce bureau.
    if user.role in ROLES_BUREAU_NATIONAL:
        attribution = BureauAdministrateur.objects.filter(
            bureau=bureau,
            utilisateur=user,
            actif=True,
            bureau__actif=True,
        ).first()

        return bool(
            attribution
            and getattr(attribution, droit, False)
        )

    # Les administrateurs locaux et pasteurs ne reçoivent
    # plus automatiquement le droit financier.
    attribution = BureauAdministrateur.objects.filter(
        bureau=bureau,
        utilisateur=user,
        actif=True,
        bureau__actif=True,
    ).first()

    return bool(
        attribution
        and getattr(attribution, droit, False)
    )