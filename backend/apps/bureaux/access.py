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
    Le Coordinateur du système possède les droits globaux.
    """
    return bool(
        user
        and user.is_authenticated
        and (
            user.role == Role.COORDINATEUR
            or user.is_superuser
        )
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
    Un utilisateur national sans affectation active à un bureau
    spécialisé est considéré comme relevant du périmètre
    national général.

    IMPORTANT :
    Le Bureau national général n'est PAS un cinquième bureau.

    Les seuls bureaux nationaux fonctionnels sont :
        - HOMMES
        - FEMMES
        - JEUNESSE
        - ENFANTS
    """
    if not user or not user.is_authenticated:
        return False

    if _est_coordinateur(user):
        return False

    if user.role not in ROLES_BUREAU_NATIONAL:
        return False

    return not (
        BureauAdministrateur.objects
        .filter(
            utilisateur=user,
            actif=True,
            bureau__niveau=NiveauBureau.NATIONAL,
            bureau__type_bureau__in={
                TypeBureau.HOMMES,
                TypeBureau.FEMMES,
                TypeBureau.JEUNESSE,
                TypeBureau.ENFANTS,
            },
        )
        .exists()
    )


# ============================================================
# BUREAU NATIONAL PRINCIPAL
# ============================================================

def est_bureau_national_principal(bureau):
    """
    Le Bureau national des Hommes est le bureau national principal.

    Il est le bureau qui peut créer/gérer la structure des
    trois autres bureaux nationaux :
        - Femmes
        - Jeunesse
        - Enfants
    """
    if not bureau:
        return False

    return bool(
        bureau.niveau == NiveauBureau.NATIONAL
        and bureau.type_bureau == TypeBureau.HOMMES
        and not bureau.eglise_id
    )


def _bureau_national_hommes():
    """
    Retourne le Bureau national des Hommes.

    Il s'agit du bureau national principal.
    """
    return (
        Bureau.objects
        .filter(
            niveau=NiveauBureau.NATIONAL,
            type_bureau=TypeBureau.HOMMES,
            eglise__isnull=True,
        )
        .first()
    )


# Alias explicite pour les endroits du code qui parlent
# du bureau national principal.
def _bureau_national_general():
    """
    Compatibilité avec l'ancien code.

    Dans la nouvelle architecture, le Bureau national général
    administratif ne constitue pas un bureau supplémentaire.

    Le bureau structurel principal est le Bureau national
    des Hommes.
    """
    return _bureau_national_hommes()


# ============================================================
# BUREAUX NATIONAUX SECONDAIRES
# ============================================================

BUREAUX_NATIONAUX_SECONDAIRES = {
    TypeBureau.FEMMES,
    TypeBureau.JEUNESSE,
    TypeBureau.ENFANTS,
}


def est_bureau_national_secondaire(bureau):
    """
    Vérifie qu'un bureau est l'un des trois bureaux nationaux
    secondaires autorisés.
    """
    if not bureau:
        return False

    return bool(
        bureau.niveau == NiveauBureau.NATIONAL
        and bureau.type_bureau in BUREAUX_NATIONAUX_SECONDAIRES
        and not bureau.eglise_id
    )


# ============================================================
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
    Vérifie si un utilisateur possède un droit précis sur un bureau.
    """
    if not user or not user.is_authenticated:
        return False

    if _est_coordinateur(user):
        return True

    if not bureau:
        return False

    # Le périmètre national général peut consulter les bureaux
    # nationaux, mais la création/modification spécialisée doit
    # rester contrôlée par les droits du bureau.
    if (
        _est_national_general(user)
        and bureau.niveau == NiveauBureau.NATIONAL
    ):
        return True

    # Gestion locale d'une église.
    if user.role in (
        Role.ADMIN_LOCAL,
        Role.PASTEUR,
    ):
        if (
            bureau.niveau == NiveauBureau.LOCAL
            and bureau.eglise_id == user.eglise_id
        ):
            return True

        return False

    return (
        BureauAdministrateur.objects
        .filter(
            bureau=bureau,
            utilisateur=user,
            actif=True,
            **{droit: True},
        )
        .exists()
    )