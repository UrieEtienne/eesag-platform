from django.contrib import admin

from apps.core.admin_scopes import EESAGScopedAdminMixin, is_coordinator, is_national_general
from .models import Region, Prefecture, District, Commune


class GeoReadOnlyAdmin(EESAGScopedAdminMixin, admin.ModelAdmin):
    admin_scopes = {"COORDINATEUR", "BUREAU_GENERAL"}
    default_add = False
    default_change = False
    default_delete = False

    def has_module_permission(self, request):
        return is_coordinator(request.user) or is_national_general(request.user)


class GeoAdmin(GeoReadOnlyAdmin):
    default_add = True
    default_change = True
    default_delete = True


class GeoRegionAdmin(GeoAdmin):
    pass


class GeoRegionNationalAdmin(GeoReadOnlyAdmin):
    pass


# La navigation Django est filtrée par rôle via has_module_permission.
# Les objets géographiques restent modifiables uniquement par le Coordinateur.
@admin.register(Region)
class RegionAdmin(GeoAdmin):
    def has_add_permission(self, request):
        return is_coordinator(request.user)
    def has_change_permission(self, request, obj=None):
        return is_coordinator(request.user)
    def has_delete_permission(self, request, obj=None):
        return is_coordinator(request.user)


@admin.register(Prefecture)
class PrefectureAdmin(GeoAdmin):
    def has_add_permission(self, request): return is_coordinator(request.user)
    def has_change_permission(self, request, obj=None): return is_coordinator(request.user)
    def has_delete_permission(self, request, obj=None): return is_coordinator(request.user)


@admin.register(District)
class DistrictAdmin(GeoAdmin):
    def has_add_permission(self, request): return is_coordinator(request.user)
    def has_change_permission(self, request, obj=None): return is_coordinator(request.user)
    def has_delete_permission(self, request, obj=None): return is_coordinator(request.user)


@admin.register(Commune)
class CommuneAdmin(GeoAdmin):
    def has_add_permission(self, request): return is_coordinator(request.user)
    def has_change_permission(self, request, obj=None): return is_coordinator(request.user)
    def has_delete_permission(self, request, obj=None): return is_coordinator(request.user)
