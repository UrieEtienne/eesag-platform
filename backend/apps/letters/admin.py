from apps.core.admin_scopes import EESAGScopedAdminMixin
from django.contrib import admin
from .models import Courrier


@admin.register(Courrier)
class CourrierAdmin(EESAGScopedAdminMixin, admin.ModelAdmin):
    admin_scopes = {"COORDINATEUR", "EGLISE"}
    default_add = True
    default_change = True

    list_display = ("numero_reference", "type_courrier", "expediteur", "eglise_destinataire", "date_emission", "lu")
    list_filter = ("type_courrier", "lu")
    search_fields = ("numero_reference", "objet")
    readonly_fields = ("numero_reference", "date_emission")
