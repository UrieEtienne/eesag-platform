from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from .models import Religion, Eglise, Departement, RoleEglise, Annexe
from apps.accounts.models import Utilisateur, Role


class EgliseAdminForm(forms.ModelForm):
    """Formulaire admin pour la création/modification d'une église.

    Le responsable existant est optionnel : le responsable peut simplement
    être saisi comme nom tant qu'il ne possède pas encore de compte EESAG.
    """

    class Meta:
        model = Eglise
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        responsable = cleaned.get("responsable")
        responsable_nom = (cleaned.get("responsable_nom") or "").strip()
        if responsable and responsable_nom:
            # On conserve le nom libre pour l'historique, mais on évite une
            # ambiguïté visuelle : le compte existant reste prioritaire.
            cleaned["responsable_nom"] = responsable_nom
        if not responsable and not responsable_nom:
            self.add_error(
                "responsable_nom",
                "Saisissez le nom du responsable si aucun compte EESAG n'est encore lié."
            )
        return cleaned


@admin.register(Religion)
class ReligionAdmin(admin.ModelAdmin):
    list_display = ("nom",)


@admin.register(Eglise)
class EgliseAdmin(admin.ModelAdmin):
    form = EgliseAdminForm
    list_display = ("code", "nom", "religion", "region", "prefecture", "district", "responsable_affichage", "statut")
    list_filter = ("religion", "region", "prefecture", "statut")
    search_fields = ("nom", "code", "responsable_nom", "responsable__nom", "responsable__prenom")
    readonly_fields = ("code", "date_enregistrement_systeme")

    def responsable_affichage(self, obj):
        if obj.responsable:
            return f"{obj.responsable.prenom} {obj.responsable.nom}"
        return obj.responsable_nom or "— non affecté —"
    responsable_affichage.short_description = "Responsable"


@admin.register(Departement)
class DepartementAdmin(admin.ModelAdmin):
    list_display = ("nom", "nombre_membres")
    search_fields = ("nom",)
    ordering = ("nom",)


@admin.register(RoleEglise)
class RoleEgliseAdmin(admin.ModelAdmin):
    list_display = ("nom", "actif")
    list_filter = ("actif",)
    search_fields = ("nom",)
    ordering = ("nom",)

@admin.register(Annexe)
class AnnexeAdmin(admin.ModelAdmin):
    list_display = ("code", "nom", "eglise", "responsable", "active")
    list_filter = ("active", "eglise")
    search_fields = ("nom", "code", "adresse")
    readonly_fields = ("code",)
