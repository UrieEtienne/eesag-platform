from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Role, Utilisateur
from apps.core.admin_scopes import EESAGScopedAdminMixin, is_coordinator, is_local, is_national_general

from .models import Annexe, Departement, Eglise, Religion, RoleEglise


def _synchroniser_acces_admin_eglise(eglise, actif):
    """
    Synchronise les comptes de gestion de l'église avec son activation.

    L'activation de la plateforme par le Bureau national ouvre le compte
    de gestion local (Django + plateforme) pour les ADMIN_LOCAL/PASTEUR.
    La désactivation referme leurs accès.
    """
    Utilisateur.objects.filter(
        eglise=eglise,
        role__in=[Role.ADMIN_LOCAL, Role.PASTEUR],
    ).update(
        is_staff=bool(actif),
        actif=bool(actif),
    )


class EgliseAdminForm(forms.ModelForm):
    """
    Formulaire simplifié de création d'une église.

    Le Bureau national peut créer l'église et, dans le même écran,
    créer son premier administrateur local.
    """

    creer_compte_admin = forms.BooleanField(
        label="Créer immédiatement le compte administrateur local",
        required=False,
        initial=True,
        help_text="Le compte sera rattaché automatiquement à cette église.",
    )
    admin_nom = forms.CharField(label="Nom de l'administrateur", max_length=100, required=False)
    admin_prenom = forms.CharField(label="Prénom de l'administrateur", max_length=100, required=False)
    admin_telephone = forms.CharField(label="Téléphone", max_length=20, required=False)
    admin_email = forms.EmailField(label="Email", required=False)
    admin_mot_de_passe = forms.CharField(
        label="Code secret / mot de passe",
        widget=forms.PasswordInput(render_value=False),
        required=False,
        min_length=6,
    )
    admin_confirmation = forms.CharField(
        label="Confirmation",
        widget=forms.PasswordInput(render_value=False),
        required=False,
        min_length=6,
    )

    class Meta:
        model = Eglise
        fields = "__all__"

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self._can_create_admin = bool(
            request and (is_coordinator(request.user) or is_national_general(request.user))
        )

        # Ces champs supplémentaires ne sont affichés qu'à la création et
        # uniquement au Coordinateur/Bureau national général.
        if self.instance and self.instance.pk:
            for name in (
                "creer_compte_admin", "admin_nom", "admin_prenom",
                "admin_telephone", "admin_email", "admin_mot_de_passe",
                "admin_confirmation",
            ):
                self.fields.pop(name, None)
        elif not self._can_create_admin:
            for name in (
                "creer_compte_admin", "admin_nom", "admin_prenom",
                "admin_telephone", "admin_email", "admin_mot_de_passe",
                "admin_confirmation",
            ):
                self.fields.pop(name, None)

    def clean(self):
        cleaned = super().clean()
        responsable = cleaned.get("responsable")
        responsable_nom = (cleaned.get("responsable_nom") or "").strip()

        creer = cleaned.get("creer_compte_admin", False)
        admin_nom = (cleaned.get("admin_nom") or "").strip()
        admin_prenom = (cleaned.get("admin_prenom") or "").strip()
        admin_telephone = cleaned.get("admin_telephone")
        admin_password = cleaned.get("admin_mot_de_passe")
        admin_confirmation = cleaned.get("admin_confirmation")

        if not responsable and not responsable_nom:
            if creer and admin_nom and admin_prenom:
                cleaned["responsable_nom"] = f"{admin_prenom} {admin_nom}".strip()
                cleaned["responsable_telephone"] = admin_telephone or ""
                cleaned["responsable_email"] = cleaned.get("admin_email") or ""
            else:
                self.add_error(
                    "responsable_nom",
                    "Saisissez le nom du responsable ou créez son compte ci-dessous.",
                )

        if responsable and responsable.role == Role.COORDINATEUR:
            self.add_error(
                "responsable",
                "Le Coordinateur du système ne peut pas être responsable d'une église.",
            )

        if creer:
            required = {
                "admin_nom": admin_nom,
                "admin_prenom": admin_prenom,
                "admin_telephone": admin_telephone,
                "admin_mot_de_passe": admin_password,
                "admin_confirmation": admin_confirmation,
            }
            for field, value in required.items():
                if not value:
                    self.add_error(field, "Ce champ est obligatoire.")

            if admin_password and admin_confirmation and admin_password != admin_confirmation:
                self.add_error("admin_confirmation", "Les deux mots de passe sont différents.")

            if admin_password and admin_confirmation and admin_password == admin_confirmation:
                try:
                    password_validation.validate_password(admin_password)
                except Exception as exc:
                    self.add_error("admin_mot_de_passe", exc)

            if admin_telephone:
                try:
                    cleaned["admin_telephone"] = normaliser_telephone(admin_telephone)
                except ValueError as exc:
                    self.add_error("admin_telephone", str(exc))

            if cleaned.get("admin_telephone") and Utilisateur.objects.filter(
                telephone=cleaned["admin_telephone"]
            ).exists():
                self.add_error(
                    "admin_telephone",
                    "Ce numéro est déjà associé à un compte EESAG.",
                )

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
            "Lecture seule : seule l'activation faite par le Bureau national est autorisée."
            if is_coordinator(request.user)
            else "Le Bureau national général peut activer ou désactiver l'accès à la plateforme."
        )
        fieldsets = [
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
        ]

        if obj is None and (is_coordinator(request.user) or is_national_general(request.user)):
            fieldsets.append((
                "Compte administrateur local",
                {
                    "fields": (
                        "creer_compte_admin",
                        "admin_nom", "admin_prenom",
                        "admin_telephone", "admin_email",
                        "admin_mot_de_passe", "admin_confirmation",
                    ),
                    "description": (
                        "Ce compte sera automatiquement rattaché à cette église. "
                        "Conservez l'identifiant et le code secret affichés après l'enregistrement. "
                        "L'église reste inactive jusqu'à son activation par le Bureau national."
                    ),
                },
            ))

        fieldsets.extend([
            ("Activation de la plateforme", {
                "fields": ("plateforme_active", "date_activation_plateforme", "activee_par"),
                "description": activation_help,
            }),
            ("Statut administratif", {"fields": ("statut",)}),
        ])

        return tuple(fieldsets)

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
        # L'activation de plateforme n'est jamais faite à la création.
        if not change:
            obj.plateforme_active = False
            obj.date_activation_plateforme = None
            obj.activee_par = None

        # Le Coordinateur peut consulter mais ne peut pas activer l'église.
        if not is_national_general(request.user):
            if change:
                previous = Eglise.objects.get(pk=obj.pk)
                obj.plateforme_active = previous.plateforme_active
                obj.date_activation_plateforme = previous.date_activation_plateforme
                obj.activee_par = previous.activee_par

        if is_national_general(request.user) and change and "plateforme_active" in form.changed_data:
            if obj.plateforme_active:
                obj.date_activation_plateforme = timezone.now()
                obj.activee_par = request.user
            else:
                obj.date_activation_plateforme = None
                obj.activee_par = None

        with transaction.atomic():
            super().save_model(request, obj, form, change)

            # À la création, le premier administrateur local est créé dans
            # le même écran et immédiatement rattaché à l'église.
            if not change and (is_coordinator(request.user) or is_national_general(request.user)):
                creer = form.cleaned_data.get("creer_compte_admin", False)
                if creer:
                    password = form.cleaned_data.get("admin_mot_de_passe")
                    compte = Utilisateur(
                        nom=form.cleaned_data.get("admin_nom", "").strip(),
                        prenom=form.cleaned_data.get("admin_prenom", "").strip(),
                        telephone=form.cleaned_data.get("admin_telephone", ""),
                        email=form.cleaned_data.get("admin_email", ""),
                        role=Role.ADMIN_LOCAL,
                        eglise=obj,
                        actif=False,
                        is_staff=False,
                    )
                    compte.set_password(password)
                    compte.code_secret_clair = ""
                    compte.save()
                    self._created_admin_credentials = (
                        compte.identifiant,
                        password,
                        compte,
                    )
                    if not obj.responsable:
                        obj.responsable = compte
                        obj.responsable_nom = f"{compte.prenom} {compte.nom}".strip()
                        obj.responsable_telephone = compte.telephone
                        obj.responsable_email = compte.email or ""
                        obj.save(update_fields=[
                            "responsable", "responsable_nom",
                            "responsable_telephone", "responsable_email",
                        ])

            # Si une activation a été faite par le Bureau national,
            # synchroniser les comptes locaux concernés.
            if is_national_general(request.user) and change and "plateforme_active" in form.changed_data:
                _synchroniser_acces_admin_eglise(obj, obj.plateforme_active)

    def response_add(self, request, obj, post_url_continue=None):
        creds = getattr(self, "_created_admin_credentials", None)
        if creds:
            identifiant, password, compte = creds
            self.message_user(
                request,
                format_html(
                    "<strong>Église créée.</strong> Compte administrateur local : "
                    "<strong>{}</strong> · Code secret : <strong>{}</strong>. "
                    "L'église reste inactive jusqu'à son activation par le Bureau national.",
                    identifiant, password,
                ),
                level=messages.SUCCESS,
            )
        return super().response_add(request, obj, post_url_continue)


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
