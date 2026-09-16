from django.contrib import admin


def _assigned_bureau(user):
    try:
        from apps.bureaux.models import BureauAdministrateur
        return (
            BureauAdministrateur.objects
            .filter(utilisateur=user, actif=True)
            .select_related("bureau")
            .first()
        )
    except Exception:
        return None


def is_coordinator(user):
    return bool(user and user.is_authenticated and (user.role == "COORDINATEUR" or user.is_superuser))


def is_national_role(user):
    return bool(user and user.is_authenticated and user.role in {"SUPERADMIN_INTL", "SUPERADMIN_NATIONAL"})


def is_national_general(user):
    return is_national_role(user) and _assigned_bureau(user) is None


def is_national_special(user):
    return is_national_role(user) and _assigned_bureau(user) is not None


def is_local(user):
    return bool(user and user.is_authenticated and user.role in {"ADMIN_LOCAL", "PASTEUR"} and user.eglise_id)


def can_scope(user, scopes):
    scopes = set(scopes or ())
    return (
        ("COORDINATEUR" in scopes and is_coordinator(user))
        or ("BUREAU_GENERAL" in scopes and is_national_general(user))
        or ("BUREAU_SPECIAL" in scopes and is_national_special(user))
        or ("EGLISE" in scopes and is_local(user))
    )


class EESAGScopedAdminMixin:
    """Masque réellement les modèles Django admin selon le périmètre connecté."""

    admin_scopes = {"COORDINATEUR"}
    default_add = False
    default_change = False
    default_delete = False

    def _allowed(self, request):
        return can_scope(request.user, self.admin_scopes)

    def has_module_permission(self, request):
        return self._allowed(request)

    def has_view_permission(self, request, obj=None):
        if not self._allowed(request):
            return False
        return True

    def has_add_permission(self, request):
        if not self._allowed(request):
            return False
        return bool(self.default_add)

    def has_change_permission(self, request, obj=None):
        if not self._allowed(request):
            return False
        return bool(self.default_change)

    def has_delete_permission(self, request, obj=None):
        if not self._allowed(request):
            return False
        return bool(self.default_delete)


class EESAGReadOnlyAdmin(EESAGScopedAdminMixin, admin.ModelAdmin):
    default_add = False
    default_change = False
    default_delete = False
