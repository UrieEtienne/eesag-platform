from apps.core.admin_scopes import EESAGScopedAdminMixin
from django.contrib import admin
from .models import Document, DocumentDestinataire


class DocumentDestinataireInline(admin.TabularInline):
    model = DocumentDestinataire
    extra = 0


@admin.register(Document)
class DocumentAdmin(EESAGScopedAdminMixin, admin.ModelAdmin):
    admin_scopes = {"COORDINATEUR", "BUREAU_GENERAL", "BUREAU_SPECIAL", "EGLISE"}
    default_add = True
    default_change = True

    list_display = ("titre", "categorie", "expediteur", "eglise_expediteur", "date_envoi", "actif")
    list_filter = ("categorie", "actif")
    search_fields = ("titre", "description")
    readonly_fields = ("date_envoi",)
    inlines = [DocumentDestinataireInline]


@admin.register(DocumentDestinataire)
class DocumentDestinataireAdmin(EESAGScopedAdminMixin, admin.ModelAdmin):
    admin_scopes = {"COORDINATEUR", "BUREAU_GENERAL", "BUREAU_SPECIAL", "EGLISE"}
    default_add = False
    default_change = False

    list_display = ("document", "eglise", "lu", "date_reception")
    list_filter = ("lu", "eglise")
