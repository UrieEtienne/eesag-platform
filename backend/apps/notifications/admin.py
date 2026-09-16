from apps.core.admin_scopes import EESAGScopedAdminMixin
from django.contrib import admin
from .models import Notification, Publication, DiffusionNotification


@admin.register(Notification)
class NotificationAdmin(EESAGScopedAdminMixin, admin.ModelAdmin):
    admin_scopes = {"COORDINATEUR", "BUREAU_GENERAL", "BUREAU_SPECIAL", "EGLISE"}
    default_add = False
    default_change = True

    list_display = ("titre", "destinataire", "type_notification", "lu", "date_creation")
    list_filter = ("type_notification", "lu")


@admin.register(Publication)
class PublicationAdmin(EESAGScopedAdminMixin, admin.ModelAdmin):
    admin_scopes = {"COORDINATEUR", "BUREAU_GENERAL", "BUREAU_SPECIAL", "EGLISE"}
    default_add = True
    default_change = True

    list_display = ("titre", "eglise", "auteur", "date_publication")


@admin.register(DiffusionNotification)
class DiffusionNotificationAdmin(EESAGScopedAdminMixin, admin.ModelAdmin):
    admin_scopes = {"COORDINATEUR", "BUREAU_GENERAL", "BUREAU_SPECIAL", "EGLISE"}
    default_add = True
    default_change = True
    list_display = ("titre", "portee", "eglise", "departement", "bureau", "nombre_destinataires", "date_creation")
    list_filter = ("portee", "date_creation")
    search_fields = ("titre", "message")
    readonly_fields = ("date_creation", "nombre_destinataires", "auteur")
