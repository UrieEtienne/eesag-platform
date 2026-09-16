from django.contrib import admin
from django.utils import timezone

from apps.core.admin_scopes import EESAGScopedAdminMixin
from .models import (
    ActivationFonctionnalite,
    AnnonceSysteme,
    ConfigurationMonetisation,
    FonctionnaliteSysteme,
    OffreMiseAJourSysteme,
    ProfilDeveloppeur,
)


class CoordinatorOnlyAdmin(EESAGScopedAdminMixin, admin.ModelAdmin):
    admin_scopes = {"COORDINATEUR"}
    default_add = True
    default_change = True
    default_delete = True


@admin.register(FonctionnaliteSysteme)
class FonctionnaliteSystemeAdmin(CoordinatorOnlyAdmin):
    list_display = ("nom", "code", "groupe", "actif_global", "reservable", "ordre")
    list_filter = ("actif_global", "reservable", "groupe")
    search_fields = ("nom", "code", "description")


@admin.register(ActivationFonctionnalite)
class ActivationFonctionnaliteAdmin(CoordinatorOnlyAdmin):
    list_display = ("fonctionnalite", "eglise", "bureau", "actif", "active_par", "date_activation")
    list_filter = ("actif", "fonctionnalite")
    readonly_fields = ("date_activation", "active_par")


@admin.register(AnnonceSysteme)
class AnnonceSystemeAdmin(CoordinatorOnlyAdmin):
    list_display = ("titre", "niveau", "fonctionnalite", "actif", "publie_le", "cree_par")
    list_filter = ("niveau", "actif", "fonctionnalite")
    search_fields = ("titre", "message")
    readonly_fields = ("date_creation", "publie_le", "cree_par")

    def save_model(self, request, obj, form, change):
        obj.cree_par = request.user
        if obj.actif and not obj.publie_le:
            obj.publie_le = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(ProfilDeveloppeur)
class ProfilDeveloppeurAdmin(CoordinatorOnlyAdmin):
    list_display = ("nom", "titre", "actif", "ordre")
    list_filter = ("actif",)
    search_fields = ("nom", "titre", "biographie", "experiences", "parcours", "competences")


@admin.register(ConfigurationMonetisation)
class ConfigurationMonetisationAdmin(CoordinatorOnlyAdmin):
    list_display = ("actif", "fournisseur", "devise", "derniere_modification", "modifie_par")
    readonly_fields = ("derniere_modification", "modifie_par")

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        obj.modifie_par = request.user
        super().save_model(request, obj, form, change)


@admin.register(OffreMiseAJourSysteme)
class OffreMiseAJourSystemeAdmin(CoordinatorOnlyAdmin):
    list_display = ("version", "titre", "fonctionnalite", "prix", "devise", "gratuite", "active", "publie_le")
    list_filter = ("active", "gratuite", "devise")
    search_fields = ("version", "titre", "description")
    readonly_fields = ("date_creation", "publie_le", "cree_par")

    def save_model(self, request, obj, form, change):
        obj.cree_par = request.user
        if obj.active and not obj.publie_le:
            obj.publie_le = timezone.now()
        super().save_model(request, obj, form, change)
