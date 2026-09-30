from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import Role, ROLES_NATIONAUX, ROLES_GESTION_EGLISE, ROLES_BUREAU_NATIONAL


def est_bureau_national_specifique(user):
    if not user or user.role not in ROLES_BUREAU_NATIONAL:
        return False
    try:
        from apps.bureaux.models import BureauAdministrateur
        return BureauAdministrateur.objects.filter(
            utilisateur=user, actif=True
        ).exists()
    except Exception:
        return False


def est_bureau_national_general(user):
    return bool(
        user
        and user.is_authenticated
        and user.role in ROLES_BUREAU_NATIONAL
        and not est_bureau_national_specifique(user)
    )

# ============================================================
# POSTES DU BUREAU NATIONAL
# ============================================================

POSTE_PRESIDENT = "PRESIDENT"
POSTE_VICE_PRESIDENT = "VICE_PRESIDENT"

POSTE_SECRETAIRE = "SECRETAIRE"
POSTE_SECRETAIRE_ADJOINT = "SECRETAIRE_ADJOINT"

POSTE_TRESORIER = "TRESORIER"
POSTE_CAISSIER = "CAISSIER"


def get_postes_bureau_national(user):
    """
    Retourne les postes actifs du Bureau national de l'utilisateur.

    La source principale est MandatBureauNational.
    """

    if not user or not user.is_authenticated:
        return set()

    if user.role not in ROLES_BUREAU_NATIONAL:
        return set()

    try:
        from apps.accounts.models import MandatBureauNational

        mandats = MandatBureauNational.objects.filter(
            utilisateur=user,
            actif=True,
        )

        return {
            mandat.poste.strip().upper()
            for mandat in mandats
            if mandat.poste
        }

    except Exception:
        return set()


def a_poste_bureau_national(user, *postes):
    """
    Vérifie si l'utilisateur possède au moins
    un des postes demandés.
    """

    if not user or not user.is_authenticated:
        return False

    if user.role not in ROLES_BUREAU_NATIONAL:
        return False

    postes_utilisateur = get_postes_bureau_national(user)

    postes_demandes = {
        poste.strip().upper()
        for poste in postes
    }

    return bool(
        postes_utilisateur.intersection(postes_demandes)
    )


# ============================================================
# GESTION DES ÉGLISES
# ============================================================

def peut_creer_eglise_bureau(user):
    """
    Président ou Vice-président :
    peut créer une église.
    """
    return a_poste_bureau_national(
        user,
        POSTE_PRESIDENT,
        POSTE_VICE_PRESIDENT,
    )


def peut_modifier_eglise_bureau(user):
    """
    Président ou Vice-président :
    peut modifier une église.
    """
    return a_poste_bureau_national(
        user,
        POSTE_PRESIDENT,
        POSTE_VICE_PRESIDENT,
    )


def peut_supprimer_eglise_bureau(user):
    """
    Président ou Vice-président :
    peut supprimer une église.
    """
    return a_poste_bureau_national(
        user,
        POSTE_PRESIDENT,
        POSTE_VICE_PRESIDENT,
    )


# ============================================================
# ACTIVATION / STATISTIQUES
# ============================================================

def peut_activer_eglise_bureau(user):
    """
    Secrétaire ou Secrétaire adjoint :
    peut activer/désactiver une église.
    """
    return a_poste_bureau_national(
        user,
        POSTE_SECRETAIRE,
        POSTE_SECRETAIRE_ADJOINT,
    )


def peut_voir_statistiques_bureau(user):
    """
    Secrétaire ou Secrétaire adjoint :
    peut consulter les statistiques du Bureau national.
    """
    return a_poste_bureau_national(
        user,
        POSTE_SECRETAIRE,
        POSTE_SECRETAIRE_ADJOINT,
    )


# ============================================================
# FINANCES
# ============================================================

def peut_voir_finances_bureau(user):
    """
    Trésorier :
    peut consulter les finances du Bureau national.
    """
    return a_poste_bureau_national(
        user,
        POSTE_TRESORIER,
    )


# ============================================================
# RAPPORTS
# ============================================================

def peut_voir_rapports_bureau(user):
    """
    Trésorier :
    peut consulter les rapports financiers/comptables
    du Bureau national.
    """
    return a_poste_bureau_national(
        user,
        POSTE_TRESORIER,
    )


class EstCoordinateur(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.role == Role.COORDINATEUR or request.user.is_superuser)
        )


class EstCoordinateurOuGestionEglise(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (
                user.role == Role.COORDINATEUR
                or user.is_superuser
                or user.role in ROLES_GESTION_EGLISE
            )
        )


class EstCoordinateurOuBureauNationalGeneral(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (
                user.role == Role.COORDINATEUR
                or user.is_superuser
                or est_bureau_national_general(user)
            )
        )


class EstSuperAdminInternational(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in [Role.COORDINATEUR, Role.SUPERADMIN_INTL]
        )


class EstSuperAdminNationalOuPlus(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ROLES_NATIONAUX
        )


class EstBureauNational(EstSuperAdminNationalOuPlus):
    pass


class EstAdminLocalOuPlus(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.role in (Role.COORDINATEUR,) or user.is_superuser:
            return True
        return user.role in ROLES_GESTION_EGLISE

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role == Role.COORDINATEUR or user.is_superuser:
            return True
        eglise = getattr(obj, "eglise", None)
        if obj.__class__.__name__ == "Eglise":
            eglise = obj
        return bool(
            user.role in ROLES_GESTION_EGLISE
            and user.eglise_id == getattr(eglise, "id", None)
        )


class EstMembreDeLEgliseOuNational(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role in ROLES_NATIONAUX:
            if est_bureau_national_specifique(user):
                return request.method in SAFE_METHODS
            return True
        eglise = getattr(obj, "eglise", None)
        if obj.__class__.__name__ == "Eglise":
            eglise = obj
        meme_eglise = user.eglise_id == getattr(eglise, "id", None)
        if request.method in SAFE_METHODS:
            return meme_eglise
        return meme_eglise and user.role in ROLES_GESTION_EGLISE


class PeutGererFinances(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.role == Role.COORDINATEUR or user.is_superuser:
            return True
        if user.role in [Role.ADMIN_LOCAL, Role.PASTEUR] and user.eglise_id:
            return True
        from apps.bureaux.models import BureauAdministrateur
        if BureauAdministrateur.objects.filter(
            utilisateur=user, actif=True, peut_gerer_finances=True
        ).exists():
            return True
        return est_bureau_national_general(user)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role == Role.COORDINATEUR or user.is_superuser:
            return True
        if user.role in [Role.ADMIN_LOCAL, Role.PASTEUR]:
            return getattr(obj, "eglise_id", None) == user.eglise_id
        from apps.bureaux.models import BureauAdministrateur
        return BureauAdministrateur.objects.filter(
            utilisateur=user,
            bureau_id=getattr(obj, "bureau_id", None),
            actif=True,
            peut_gerer_finances=True,
        ).exists() or (
            est_bureau_national_general(user)
            and getattr(obj, "bureau_id", None) is None
            and getattr(obj, "eglise_id", None) is None
        )


class PeutGererProjets(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.role == Role.COORDINATEUR or user.is_superuser:
            return True
        if user.role in [Role.ADMIN_LOCAL, Role.PASTEUR] and user.eglise_id:
            return True
        from apps.bureaux.models import BureauAdministrateur
        if BureauAdministrateur.objects.filter(
            utilisateur=user, actif=True, peut_gerer_projets=True
        ).exists():
            return True
        return est_bureau_national_general(user)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role == Role.COORDINATEUR or user.is_superuser:
            return True
        if user.role in [Role.ADMIN_LOCAL, Role.PASTEUR]:
            return getattr(obj, "eglise_id", None) == user.eglise_id
        from apps.bureaux.models import BureauAdministrateur
        return BureauAdministrateur.objects.filter(
            utilisateur=user,
            bureau_id=getattr(obj, "bureau_id", None),
            actif=True,
            peut_gerer_projets=True,
        ).exists() or (
            est_bureau_national_general(user)
            and getattr(obj, "bureau_id", None) is None
            and getattr(obj, "eglise_id", None) is None
        )
