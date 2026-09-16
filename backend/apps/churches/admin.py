from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.models import Role, Utilisateur
from apps.core.admin_scopes import EESAGScopedAdminMixin, is_coordinator, is_local, is_national_general

from .models import Annexe, Departement, Eglise, Religion, RoleEglise


def _synchroniser_acces_admin_eglise(eglise, actif):
    """Active/désactive l’accès Django admin des pasteurs et admins locaux de l’église."""
    Utilisateur.objects.filter(
        eglise=eglise,
        role__in=[Role.ADMIN_LOCAL, Role.PASTEUR],
    ).update(is_staff=bool(actif))


class EgliseAdminForm(forms.ModelForm):
    class Meta:
        model = Eglise
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        responsable = cleaned.get("responsable")
        responsable_nom = (cleaned.get("responsable_nom") or "").strip()
        if not responsable and not responsable_nom:
            self.add_error(
                "responsable_nom",
                "Saisissez le nom du responsable si aucun compte EESAG n'est encore lié.",
            )
        if responsable and responsable.role == Role.COORDINATEUR:
            self.add_error("responsable", "Le Coordinateur du système ne peut pas être responsable d'une église.")
        return cleaned


@admin.register(Religion)
class ReligionAdmin(EESAGScopedAdminMixin, admin.ModelAdmin):
    admin_scopes = {"COORDINATEUR", "BUREAU_GENERAL"}
    default_add = True
    default_change = True
    default_delete = True
    list_display = ("nom", "description")
    search_fields = ("nom", "description")


@admin.register(Eglise)
class EgliseAdmin(EESAGScopedAdminMixin, admin.ModelAdmin):
    """Gestion des églises et activation de plateforme.

    L'activation n'est JAMAIS faite depuis le frontend. Elle est disponible
    uniquement dans Django admin pour le Bureau national général.
    """

    admin_scopes = {"COORDINATEUR", "BUREAU_GENERAL"}
    default_add = True
    default_change = True
    default_delete = False

    form = EgliseAdminForm
    list_display = (
        "code",
        "nom",
        "religion",
        "region",
        "prefecture",
        "district",
        "responsable_affichage",
        "plateforme_badge",
        "statut",
    )
    list_filter = ("plateforme_active", "statut", "religion", "region", "prefecture")
    search_fields = (
        "nom",
        "code",
        "responsable_nom",
        "responsable__nom",
        "responsable__prenom",
    )
    readonly_fields = (
        "code",
        "date_enregistrement_systeme",
        "date_activation_plateforme",
        "activee_par",
    )
    actions = ("activer_plateformes", "desactiver_plateformes")

    def has_module_permission(self, request):
        return is_coordinator(request.user) or is_national_general(request.user)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return is_coordinator(request.user) or is_national_general(request.user)

    def has_change_permission(self, request, obj=None):
        return is_coordinator(request.user) or is_national_general(request.user)

    def has_delete_permission(self, request, obj=None):
        # Suppression réservée au Coordinateur. Le Bureau national ne supprime pas.
        return is_coordinator(request.user)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not is_national_general(request.user):
            actions.pop("activer_plateformes", None)
            actions.pop("desactiver_plateformes", None)
        return actions

    def get_readonly_fields(self, request, obj=None):
        fields = list(self.readonly_fields)
        if is_coordinator(request.user):
            fields.append("plateforme_active")
        return tuple(fields)

    def get_fieldsets(self, request, obj=None):
        activation_help = (
            "Lecture seule : l'activation est exclusivement réalisée par le Bureau national."
            if is_coordinator(request.user)
            else "Le Bureau national peut activer ou désactiver l'accès à la plateforme."
        )
        return (
            ("Identité de l'église", {
                "fields": (
                    "code", "nom", "religion", "region", "prefecture", "district", "commune",
                    "adresse_precise", "logo",
                )
            }),
            ("Responsable", {
                "fields": (
                    "responsable", "responsable_nom", "responsable_telephone", "responsable_email",
                )
            }),
            ("Contact & fondation", {
                "fields": ("telephone", "email", "date_creation", "date_enregistrement_systeme")
            }),
            ("Activation de la plateforme", {
                "fields": ("plateforme_active", "date_activation_plateforme", "activee_par"),
                "description": activation_help,
            }),
            ("Statut administratif", {
                "fields": ("statut",)
            }),
        )

    def responsable_affichage(self, obj):
        if obj.responsable:
            return f"{obj.responsable.prenom} {obj.responsable.nom}"
        return obj.responsable_nom or "— non affecté —"
    responsable_affichage.short_description = "Responsable"

    def plateforme_badge(self, obj):
        if obj.plateforme_active:
            return "● Active"
        return "○ À activer"
    plateforme_badge.short_description = "Plateforme"

    @admin.action(description="Activer la plateforme pour les églises sélectionnées")
    def activer_plateformes(self, request, queryset):
        if not is_national_general(request.user):
            self.message_user(
                request,
                "Seul le Bureau national peut activer une église.",
                level=messages.ERROR,
            )
            return
        count = 0
        now = timezone.now()
        for eglise in queryset:
            if not eglise.plateforme_active:
                eglise.plateforme_active = True
                eglise.date_activation_plateforme = now
                eglise.activee_par = request.user
                eglise.save(update_fields=["plateforme_active", "date_activation_plateforme", "activee_par"])
                _synchroniser_acces_admin_eglise(eglise, True)
                count += 1
        self.message_user(request, f"{count} église(s) activée(s).", level=messages.SUCCESS)

    @admin.action(description="Désactiver la plateforme pour les églises sélectionnées")
    def desactiver_plateformes(self, request, queryset):
        if not is_national_general(request.user):
            self.message_user(
                request,
                "Seul le Bureau national peut gérer l'activation de la plateforme.",
                level=messages.ERROR,
            )
            return
        count = 0
        for eglise in queryset:
            if eglise.plateforme_active:
                eglise.plateforme_active = False
                eglise.date_activation_plateforme = None
                eglise.activee_par = None
                eglise.save(update_fields=["plateforme_active", "date_activation_plateforme", "activee_par"])
                _synchroniser_acces_admin_eglise(eglise, False)
                count += 1
        self.message_user(request, f"{count} église(s) désactivée(s).", level=messages.SUCCESS)

    def save_model(self, request, obj, form, change):
        # Personne ne peut injecter plateforme_active=True en contournant l'UI.
        if not is_national_general(request.user):
            if change:
                previous = Eglise.objects.get(pk=obj.pk)
                obj.plateforme_active = previous.plateforme_active
                obj.date_activation_plateforme = previous.date_activation_plateforme
                obj.activee_par = previous.activee_par
            else:
                obj.plateforme_active = False
                obj.date_activation_plateforme = None
                obj.activee_par = None

        if is_national_general(request.user) and change and "plateforme_active" in form.changed_data:
            if obj.plateforme_active:
                obj.date_activation_plateforme = timezone.now()
                obj.activee_par = request.user
            else:
                obj.date_activation_plateforme = None
                obj.activee_par = None

        # Toute nouvelle église commence toujours inactive.
        if not change:
            obj.plateforme_active = False
            obj.date_activation_plateforme = None
            obj.activee_par = None

        super().save_model(request, obj, form, change)
        if is_national_general(request.user) and change and "plateforme_active" in form.changed_data:
            _synchroniser_acces_admin_eglise(obj, obj.plateforme_active)


@admin.register(Departement)
class DepartementAdmin(EESAGScopedAdminMixin, admin.ModelAdmin):
    admin_scopes = {"COORDINATEUR", "EGLISE"}
    default_add = True
    default_change = True
    default_delete = True
    list_display = ("nom", "nombre_membres")
    search_fields = ("nom",)
    ordering = ("nom",)

    def has_module_permission(self, request):
        return is_coordinator(request.user) or is_local(request.user)

    def get_queryset(self, request):
        return super().get_queryset(request).all().order_by("nom")


@admin.register(RoleEglise)
class RoleEgliseAdmin(EESAGScopedAdminMixin, admin.ModelAdmin):
    admin_scopes = {"COORDINATEUR", "EGLISE"}
    default_add = True
    default_change = True
    default_delete = True
    list_display = ("nom", "actif")
    list_filter = ("actif",)
    search_fields = ("nom",)
    ordering = ("nom",)

    def has_module_permission(self, request):
        return is_coordinator(request.user) or is_local(request.user)


@admin.register(Annexe)
class AnnexeAdmin(EESAGScopedAdminMixin, admin.ModelAdmin):
    admin_scopes = {"COORDINATEUR", "EGLISE"}
    default_add = True
    default_change = True
    default_delete = True
    list_display = ("code", "nom", "eglise", "responsable", "active")
    list_filter = ("active", "eglise")
    search_fields = ("nom", "code", "adresse")
    readonly_fields = ("code",)

    def has_module_permission(self, request):
        return is_coordinator(request.user) or is_local(request.user)

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("eglise", "responsable")
        if is_local(request.user):
            return qs.filter(eglise_id=request.user.eglise_id)
        if is_coordinator(request.user):
            return qs
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "eglise" and is_local(request.user):
            kwargs["queryset"] = Eglise.objects.filter(pk=request.user.eglise_id)
        if db_field.name == "responsable" and is_local(request.user):
            kwargs["queryset"] = Utilisateur.objects.filter(eglise_id=request.user.eglise_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
