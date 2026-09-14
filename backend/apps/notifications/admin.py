from django.contrib import admin
from .models import Notification, Publication, DiffusionNotification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("titre", "destinataire", "type_notification", "lu", "date_creation")
    list_filter = ("type_notification", "lu")


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ("titre", "eglise", "auteur", "date_publication")


@admin.register(DiffusionNotification)
class DiffusionNotificationAdmin(admin.ModelAdmin):
    list_display = ("titre", "portee", "eglise", "departement", "bureau", "nombre_destinataires", "date_creation")
    list_filter = ("portee", "date_creation")
    search_fields = ("titre", "message")
    readonly_fields = ("date_creation", "nombre_destinataires", "auteur")
