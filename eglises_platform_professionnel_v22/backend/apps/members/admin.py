from django.contrib import admin
from .models import Affectation


@admin.register(Affectation)
class AffectationAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "eglise", "type_affectation", "date_affectation", "actif")
    list_filter = ("type_affectation", "actif")
