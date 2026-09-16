from django.contrib import admin
from .models import Document, DocumentDestinataire


class DocumentDestinataireInline(admin.TabularInline):
    model = DocumentDestinataire
    extra = 0


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("titre", "categorie", "expediteur", "eglise_expediteur", "date_envoi", "actif")
    list_filter = ("categorie", "actif")
    search_fields = ("titre", "description")
    readonly_fields = ("date_envoi",)
    inlines = [DocumentDestinataireInline]


@admin.register(DocumentDestinataire)
class DocumentDestinataireAdmin(admin.ModelAdmin):
    list_display = ("document", "eglise", "lu", "date_reception")
    list_filter = ("lu", "eglise")
