from apps.core.admin_scopes import EESAGScopedAdminMixin
from django.contrib import admin
from .models import JournalIA


@admin.register(JournalIA)
class JournalIAAdmin(EESAGScopedAdminMixin, admin.ModelAdmin):
    admin_scopes = {"COORDINATEUR"}
    default_add = False
    default_change = False

    list_display = ("cree_le", "action", "fournisseur", "utilisateur", "eglise", "succes")
    list_filter = ("action", "fournisseur", "succes", "eglise")
    search_fields = ("utilisateur__nom", "utilisateur__prenom", "resultat")
    readonly_fields = ("cree_le",)
