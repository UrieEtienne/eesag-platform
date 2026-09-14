from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from .models import Transaction, Projet
from .views import perimetre_financier_utilisateur, perimetre_projet_utilisateur


class PerimetreFormMixin:
    def _apply_scope(self):
        if not self.request:
            return
        scope = perimetre_financier_utilisateur(self.request.user)
        if scope["type"] == "EGLISE":
            self.fields["eglise"].queryset = self.fields["eglise"].queryset.filter(pk=scope["eglise_id"])
            self.fields["eglise"].initial = scope["eglise_id"]
            self.fields["eglise"].disabled = True
            self.fields["bureau"].queryset = self.fields["bureau"].queryset.none()
            self.fields["bureau"].required = False
        elif scope["type"] == "BUREAU":
            self.fields["bureau"].queryset = self.fields["bureau"].queryset.filter(pk=scope["bureau_id"])
            self.fields["bureau"].initial = scope["bureau_id"]
            self.fields["bureau"].disabled = True
            self.fields["eglise"].queryset = self.fields["eglise"].queryset.none()
            self.fields["eglise"].required = False
        elif scope["type"] == "NATIONAL":
            self.fields["eglise"].queryset = self.fields["eglise"].queryset.none()
            self.fields["eglise"].required = False
            self.fields["bureau"].queryset = self.fields["bureau"].queryset.none()
            self.fields["bureau"].required = False
        elif scope["type"] == "GLOBAL":
            pass
        else:
            self.fields["eglise"].queryset = self.fields["eglise"].queryset.none()
            self.fields["bureau"].queryset = self.fields["bureau"].queryset.none()


class TransactionAdminForm(PerimetreFormMixin, forms.ModelForm):
    class Meta:
        model = Transaction
        fields = "__all__"

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)
        self._apply_scope()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("eglise") and cleaned.get("bureau"):
            raise ValidationError("Choisissez soit une église, soit un bureau, pas les deux.")
        return cleaned


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    form = TransactionAdminForm
    list_display = ("date_transaction", "type_transaction", "montant_formate", "devise", "perimetre", "enregistre_par")
    list_filter = ("type_transaction", "devise", "date_transaction")
    search_fields = ("description", "eglise__nom", "eglise__code", "bureau__nom", "bureau__code", "enregistre_par__nom", "enregistre_par__prenom")
    date_hierarchy = "date_transaction"
    ordering = ("-date_transaction", "-id")
    readonly_fields = ("date_enregistrement", "enregistre_par")

    def get_form(self, request, obj=None, **kwargs):
        BaseForm = super().get_form(request, obj, **kwargs)
        class RequestAwareForm(BaseForm):
            def __init__(self, *args, **form_kwargs):
                form_kwargs["request"] = request
                super().__init__(*args, **form_kwargs)
        return RequestAwareForm

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("eglise", "bureau", "enregistre_par")
        scope = perimetre_financier_utilisateur(request.user)
        if scope["type"] == "GLOBAL":
            return qs
        if scope["type"] == "EGLISE":
            return qs.filter(eglise_id=scope["eglise_id"], bureau__isnull=True)
        if scope["type"] == "BUREAU":
            return qs.filter(bureau_id=scope["bureau_id"], eglise__isnull=True)
        if scope["type"] == "NATIONAL":
            return qs.filter(eglise__isnull=True, bureau__isnull=True)
        return qs.none()

    def has_add_permission(self, request):
        return perimetre_financier_utilisateur(request.user)["type"] != "NONE"

    def _in_scope(self, request, obj):
        scope = perimetre_financier_utilisateur(request.user)
        if scope["type"] == "GLOBAL":
            return True
        if scope["type"] == "EGLISE":
            return obj.eglise_id == scope["eglise_id"] and obj.bureau_id is None
        if scope["type"] == "BUREAU":
            return obj.bureau_id == scope["bureau_id"] and obj.eglise_id is None
        if scope["type"] == "NATIONAL":
            return obj.eglise_id is None and obj.bureau_id is None
        return False

    def has_change_permission(self, request, obj=None):
        return True if obj is None else self._in_scope(request, obj)

    def has_delete_permission(self, request, obj=None):
        return True if obj is None else self._in_scope(request, obj)

    def save_model(self, request, obj, form, change):
        scope = perimetre_financier_utilisateur(request.user)
        if scope["type"] == "EGLISE":
            obj.eglise_id, obj.bureau_id = scope["eglise_id"], None
        elif scope["type"] == "BUREAU":
            obj.eglise_id, obj.bureau_id = None, scope["bureau_id"]
        elif scope["type"] == "NATIONAL":
            obj.eglise_id = obj.bureau_id = None
        obj.enregistre_par = request.user
        obj.full_clean()
        super().save_model(request, obj, form, change)

    def montant_formate(self, obj):
        return f"{obj.montant:,.0f} {obj.devise}".replace(",", " ")
    montant_formate.short_description = "Montant"

    def perimetre(self, obj):
        return obj.bureau.nom if obj.bureau else obj.eglise.nom if obj.eglise else "Bureau national"
    perimetre.short_description = "Périmètre"


class ProjetAdminForm(PerimetreFormMixin, forms.ModelForm):
    class Meta:
        model = Projet
        fields = "__all__"

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)
        self._apply_scope()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("eglise") and cleaned.get("bureau"):
            raise ValidationError("Choisissez soit une église, soit un bureau, pas les deux.")
        return cleaned


@admin.register(Projet)
class ProjetAdmin(admin.ModelAdmin):
    form = ProjetAdminForm
    list_display = ("nom", "type_projet", "annee", "perimetre", "statut", "budget_prevu", "budget_utilise", "solde_disponible")
    list_filter = ("statut", "annee", "type_projet")
    search_fields = ("nom", "description", "objectif", "eglise__nom", "bureau__nom")
    readonly_fields = ("solde_disponible",)

    def get_form(self, request, obj=None, **kwargs):
        BaseForm = super().get_form(request, obj, **kwargs)
        class RequestAwareForm(BaseForm):
            def __init__(self, *args, **form_kwargs):
                form_kwargs["request"] = request
                super().__init__(*args, **form_kwargs)
        return RequestAwareForm

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("eglise", "bureau", "responsable")
        scope = perimetre_projet_utilisateur(request.user)
        if scope["type"] == "GLOBAL":
            return qs
        if scope["type"] == "EGLISE":
            return qs.filter(eglise_id=scope["eglise_id"], bureau__isnull=True)
        if scope["type"] == "BUREAU":
            return qs.filter(bureau_id=scope["bureau_id"], eglise__isnull=True)
        if scope["type"] == "NATIONAL":
            return qs.filter(eglise__isnull=True, bureau__isnull=True)
        return qs.none()

    def has_add_permission(self, request):
        return perimetre_projet_utilisateur(request.user)["type"] != "NONE"

    def _in_scope(self, request, obj):
        scope = perimetre_projet_utilisateur(request.user)
        if scope["type"] == "GLOBAL":
            return True
        if scope["type"] == "EGLISE":
            return obj.eglise_id == scope["eglise_id"] and obj.bureau_id is None
        if scope["type"] == "BUREAU":
            return obj.bureau_id == scope["bureau_id"] and obj.eglise_id is None
        if scope["type"] == "NATIONAL":
            return obj.eglise_id is None and obj.bureau_id is None
        return False

    def has_change_permission(self, request, obj=None):
        return True if obj is None else self._in_scope(request, obj)

    def has_delete_permission(self, request, obj=None):
        return True if obj is None else self._in_scope(request, obj)

    def save_model(self, request, obj, form, change):
        scope = perimetre_projet_utilisateur(request.user)
        if scope["type"] == "EGLISE":
            obj.eglise_id, obj.bureau_id = scope["eglise_id"], None
        elif scope["type"] == "BUREAU":
            obj.eglise_id, obj.bureau_id = None, scope["bureau_id"]
        elif scope["type"] == "NATIONAL":
            obj.eglise_id = obj.bureau_id = None
        obj.full_clean()
        super().save_model(request, obj, form, change)

    def perimetre(self, obj):
        return obj.bureau.nom if obj.bureau else obj.eglise.nom if obj.eglise else "Bureau national"
    perimetre.short_description = "Périmètre"
