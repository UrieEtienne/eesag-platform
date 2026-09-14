from django.contrib import admin
from .models import Courrier


@admin.register(Courrier)
class CourrierAdmin(admin.ModelAdmin):
    list_display = ("numero_reference", "type_courrier", "expediteur", "eglise_destinataire", "date_emission", "lu")
    list_filter = ("type_courrier", "lu")
    search_fields = ("numero_reference", "objet")
    readonly_fields = ("numero_reference", "date_emission")
