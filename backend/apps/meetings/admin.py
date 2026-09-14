from django.contrib import admin
from .models import Reunion

@admin.register(Reunion)
class ReunionAdmin(admin.ModelAdmin):
    list_display = ("titre","eglise","plateforme","date_debut","active","organisateur")
    list_filter = ("plateforme","active","eglise")
    search_fields = ("titre","description","eglise__nom")
    date_hierarchy = "date_debut"
    ordering = ("-date_debut",)
