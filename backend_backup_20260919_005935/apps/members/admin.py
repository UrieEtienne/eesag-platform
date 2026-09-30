from apps.core.admin_scopes import EESAGScopedAdminMixin
from django.contrib import admin
from .models import Affectation


@admin.register(Affectation)
class AffectationAdmin(EESAGScopedAdminMixin, admin.ModelAdmin):
    admin_scopes = {"COORDINATEUR", "EGLISE"}
    default_add = True
    default_change = True

    list_display = ("utilisateur", "eglise", "type_affectation", "date_affectation", "actif")
    list_filter = ("type_affectation", "actif")
