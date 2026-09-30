from apps.core.admin_scopes import EESAGScopedAdminMixin
from django.contrib import admin
from .models import Reunion

@admin.register(Reunion)
class ReunionAdmin(EESAGScopedAdminMixin, admin.ModelAdmin):
    admin_scopes = {"COORDINATEUR", "BUREAU_GENERAL", "BUREAU_SPECIAL", "EGLISE"}
    default_add = True
    default_change = True

    list_display = ("titre","eglise","plateforme","date_debut","active","organisateur")
    list_filter = ("plateforme","active","eglise")
    search_fields = ("titre","description","eglise__nom")
    date_hierarchy = "date_debut"
    ordering = ("-date_debut",)
