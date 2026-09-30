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
