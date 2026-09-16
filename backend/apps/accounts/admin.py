from django import forms
from django.contrib import admin, messages
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.html import format_html

from .models import (
    Abonnement,
    DelegationEglise,
    JournalSMS,
    MandatBureauNational,
    PermissionEglise,
    ROLES_BUREAU_NATIONAL,
    ROLES_NATIONAUX,
    Role,
    Utilisateur,
    VerificationTelephone,
)
from .services_sms import normaliser_telephone
from apps.core.admin_scopes import (
    EESAGScopedAdminMixin,
    is_coordinator,
    is_local,
    is_national_general,
)


class UtilisateurAdminForm(forms.ModelForm):
    mot_de_passe = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(render_value=False),
        required=False,
    )
    confirmation_mot_de_passe = forms.CharField(
        label="Confirmation du mot de passe",
        widget=forms.PasswordInput(render_value=False),
        required=False,
    )

    class Meta:
        model = Utilisateur
        fields = (
            "nom", "prenom", "sexe", "date_naissance", "telephone", "email", "photo",
            "nationalite", "date_bapteme_eau", "date_bapteme_saint_esprit", "fonction_eglise",
            "role", "eglise", "departement", "role_eglise", "fonction_bureau_national",
            "actif", "is_staff", "is_superuser",
        )

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        user = getattr(request, "user", None)

        if user and user.role == Role.COORDINATEUR:
            self.fields["role"].choices = [
                (Role.SUPERADMIN_NATIONAL, "Administrateur du Bureau national"),
                (Role.ADMIN_LOCAL, "Administrateur local"),
                (Role.PASTEUR, "Pasteur"),
                (Role.MEMBRE, "Membre"),
                (Role.RESPONSABLE_DEPARTEMENT, "Responsable de département"),
            ]
        elif user and is_national_general(user):
            self.fields["role"].choices = [
                (Role.ADMIN_LOCAL, "Administrateur local"),
                (Role.PASTEUR, "Pasteur"),
            ]
        elif user and user.role == Role.PASTEUR:
            self.fields["role"].choices = [
                (Role.ADMIN_LOCAL, "Administrateur local"),
                (Role.MEMBRE, "Membre"),
                (Role.RESPONSABLE_DEPARTEMENT, "Responsable de département"),
            ]
        elif user and user.role == Role.ADMIN_LOCAL:
            self.fields["role"].choices = [
                (Role.MEMBRE, "Membre"),
                (Role.RESPONSABLE_DEPARTEMENT, "Responsable de département"),
            ]

        self.fields["role"].empty_label = None
        # L'église locale peut gérer les informations de ses comptes,
        # mais ne peut jamais modifier l'état d'activation.
        if user and is_local(user):
            self.fields["actif"].disabled = True


    def clean(self):
        cleaned = super().clean()
        user = getattr(getattr(self, "request", None), "user", None)
        role = cleaned.get("role")
        eglise = cleaned.get("eglise")
        password = cleaned.get("mot_de_passe")
        confirmation = cleaned.get("confirmation_mot_de_passe")

        if user:
            if role == Role.COORDINATEUR:
                self.add_error("role", "Le rôle Coordinateur est réservé au propriétaire existant du système.")

            if role in ROLES_NATIONAUX and eglise:
                self.add_error("eglise", "Un compte national ne doit pas être rattaché à une église.")

            if user.role in (Role.ADMIN_LOCAL, Role.PASTEUR) and eglise and eglise.id != user.eglise_id:
                self.add_error("eglise", "Vous ne pouvez gérer que votre propre église.")

            if user.role in (Role.ADMIN_LOCAL, Role.PASTEUR) and not eglise:
                self.add_error("eglise", "Une église est obligatoire pour ce compte.")

            if user.role in ROLES_BUREAU_NATIONAL and not is_national_general(user):
                self.add_error("role", "Un administrateur de bureau national spécialisé ne peut pas gérer les comptes utilisateurs.")

        telephone = cleaned.get("telephone")
        if telephone:
            try:
                cleaned["telephone"] = normaliser_telephone(telephone)
            except ValueError as exc:
                self.add_error("telephone", str(exc))

        if password or confirmation:
            if password != confirmation:
                self.add_error("confirmation_mot_de_passe", "Les deux mots de passe sont différents.")
            else:
                try:
                    password_validation.validate_password(password, self.instance)
                except ValidationError as exc:
                    self.add_error("mot_de_passe", exc)
        elif not self.instance.pk:
            self.add_error("mot_de_passe", "Le mot de passe est obligatoire à la création du compte.")

        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        password = self.cleaned_data.get("mot_de_passe")
        role = self.cleaned_data.get("role")
        requester = getattr(self, "request", None)

        if role in ROLES_NATIONAUX:
            obj.eglise = None
            obj.departement = None
            obj.is_staff = True
            obj.is_superuser = False
            obj.fonction_eglise = "MEMBRE"
        elif role in (Role.ADMIN_LOCAL, Role.PASTEUR):
            obj.is_staff = True
            obj.is_superuser = False
            if requester and requester.user.role in (Role.ADMIN_LOCAL, Role.PASTEUR):
                obj.eglise = requester.user.eglise
        else:
            obj.is_staff = False
            obj.is_superuser = False

        if password:
            obj.set_password(password)

        if commit:
            obj.save()
            self.save_m2m()
        return obj


class UtilisateurAdmin(EESAGScopedAdminMixin, admin.ModelAdmin):
    admin_scopes = {"COORDINATEUR", "BUREAU_GENERAL", "EGLISE"}
    default_add = True
    default_change = True
    default_delete = False

    form = UtilisateurAdminForm
    list_display = ("miniature", "identifiant", "nom_complet", "role", "eglise", "fonction_bureau_national", "telephone", "actif")
    list_filter = ("role", "eglise", "sexe", "nationalite", "actif", "is_staff")
    search_fields = ("identifiant", "nom", "prenom", "telephone", "email")
    ordering = ("nom", "prenom")
    readonly_fields = ("identifiant", "last_login", "date_enregistrement")

    def has_module_permission(self, request):
        if not request.user.is_authenticated:
            return False
        return is_coordinator(request.user) or is_national_general(request.user) or is_local(request.user)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def get_form(self, request, obj=None, **kwargs):
        BaseForm = super().get_form(request, obj, **kwargs)

        class RequestAwareForm(BaseForm):
            def __init__(self, *args, **form_kwargs):
                form_kwargs["request"] = request
                super().__init__(*args, **form_kwargs)

        return RequestAwareForm

    @admin.action(description="Activer les comptes en attente")
    def activer_comptes_en_attente(self, request, queryset):
        if not (is_coordinator(request.user) or is_national_general(request.user)):
            self.message_user(
                request,
                "Seul le Coordinateur ou le Bureau national peut activer un compte.",
                level=messages.ERROR,
            )
            return
        qs = queryset.filter(actif=False).exclude(role=Role.COORDINATEUR)
        count = qs.update(actif=True)
        self.message_user(
            request,
            f"{count} compte(s) activé(s).",
            level=messages.SUCCESS,
        )

    @admin.action(description="Désactiver les comptes sélectionnés")
    def desactiver_comptes(self, request, queryset):
        if not (is_coordinator(request.user) or is_national_general(request.user)):
            self.message_user(
                request,
                "Seul le Coordinateur ou le Bureau national peut désactiver un compte.",
                level=messages.ERROR,
            )
            return
        qs = queryset.exclude(role=Role.COORDINATEUR)
        count = qs.update(actif=False)
        self.message_user(
            request,
            f"{count} compte(s) désactivé(s).",
            level=messages.SUCCESS,
        )

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not (is_coordinator(request.user) or is_national_general(request.user)):
            actions.pop("activer_comptes_en_attente", None)
            actions.pop("desactiver_comptes", None)
        return actions

    def get_list_display(self, request):
        base = (
            "miniature", "identifiant", "nom_complet", "role",
            "eglise", "telephone", "actif"
        )
        if is_coordinator(request.user):
            return base + ("fonction_bureau_national", "is_staff")
        return base

    def get_fieldsets(self, request, obj=None):
        fields_status = ("actif", "is_staff", "is_superuser") if is_coordinator(request.user) else ("actif", "is_staff")
        if is_national_general(request.user):
            fields_status = ("actif", "is_staff")
        return (
            ("Identité", {"fields": ("identifiant", "nom", "prenom", "sexe", "date_naissance", "nationalite", "photo")} ),
            ("Contact", {"fields": ("telephone", "email")} ),
            ("Vie de l'église", {"fields": ("date_bapteme_eau", "date_bapteme_saint_esprit", "fonction_eglise", "eglise", "departement", "role_eglise")} ),
            ("Rôle", {"fields": ("role", "fonction_bureau_national")} ),
            ("Mot de passe", {"fields": ("mot_de_passe", "confirmation_mot_de_passe")} ),
            ("Statut technique", {"fields": fields_status} ),
            ("Historique", {"fields": ("last_login", "date_enregistrement")} ),
        )

    def get_readonly_fields(self, request, obj=None):
        fields = list(self.readonly_fields)
        if is_local(request.user) and "actif" not in fields:
            fields.append("actif")
        if not is_coordinator(request.user) and "is_superuser" in fields:
            fields.remove("is_superuser")
        return tuple(fields)

    def miniature(self, obj):
        if not obj.photo:
            return "—"
        return format_html(
            '<img src="{}" alt="" style="width:38px;height:38px;object-fit:cover;border-radius:50%;">',
            obj.photo.url,
        )
    miniature.short_description = "Photo"

    def nom_complet(self, obj):
        return f"{obj.prenom} {obj.nom}"
    nom_complet.short_description = "Nom complet"

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related(
            "eglise", "departement", "role_eglise"
        )

        if is_coordinator(request.user):
            return qs.exclude(role=Role.COORDINATEUR)

        if is_national_general(request.user):
            # Le Bureau national général ne voit ici que les comptes de gestion
            # des églises. Les membres ordinaires restent dans le périmètre local.
            return qs.filter(role__in=[Role.ADMIN_LOCAL, Role.PASTEUR]).exclude(role=Role.COORDINATEUR)

        if is_local(request.user):
            return qs.filter(
                eglise_id=request.user.eglise_id
            ).exclude(role=Role.COORDINATEUR)

        return qs.none()

    def has_add_permission(self, request):
        return is_coordinator(request.user) or is_national_general(request.user) or is_local(request.user)

    def has_delete_permission(self, request, obj=None):
        return is_coordinator(request.user)

    def has_change_permission(self, request, obj=None):
        if not self.has_module_permission(request):
            return False
        if obj is None:
            return True
        if is_coordinator(request.user):
            return obj.role != Role.COORDINATEUR
        if is_national_general(request.user):
            return obj.role in (Role.ADMIN_LOCAL, Role.PASTEUR)
        # L'église locale ne peut jamais modifier l'état actif directement.
        return (
            obj.eglise_id == request.user.eglise_id
            and obj.role not in ROLES_NATIONAUX
        )

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            if is_local(request.user):
                if change:
                    previous = Utilisateur.objects.get(pk=obj.pk)
                    obj.actif = previous.actif
                else:
                    obj.actif = False
            elif is_national_general(request.user):
                # Le Bureau national peut activer/désactiver, mais pas créer
                # un compte déjà actif par défaut pour une nouvelle création.
                if not change:
                    obj.actif = False
            super().save_model(request, obj, form, change)


@admin.register(Utilisateur)
class RegisteredUtilisateurAdmin(UtilisateurAdmin):
    pass


@admin.register(PermissionEglise)
class PermissionEgliseAdmin(EESAGScopedAdminMixin, admin.ModelAdmin):
    admin_scopes = {"COORDINATEUR", "EGLISE"}
    default_add = True
    default_change = True
    list_display = ("code", "libelle", "description")
    search_fields = ("code", "libelle", "description")


@admin.register(DelegationEglise)
class DelegationEgliseAdmin(EESAGScopedAdminMixin, admin.ModelAdmin):
    admin_scopes = {"COORDINATEUR", "EGLISE"}
    default_add = True
    default_change = True
    list_display = ("utilisateur", "eglise_utilisateur", "actif", "date_creation", "cree_par")
    list_filter = ("actif",)
    search_fields = ("utilisateur__nom", "utilisateur__prenom", "utilisateur__identifiant")
    filter_horizontal = ("permissions",)
    readonly_fields = ("date_creation", "cree_par")

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("utilisateur", "utilisateur__eglise")
        if is_coordinator(request.user):
            return qs
        if is_local(request.user):
            return qs.filter(utilisateur__eglise_id=request.user.eglise_id)
        return qs.none()

    def eglise_utilisateur(self, obj):
        return obj.utilisateur.eglise or "Bureau national"
    eglise_utilisateur.short_description = "Périmètre"

    def save_model(self, request, obj, form, change):
        if not change:
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)


@admin.register(MandatBureauNational)
class MandatBureauNationalAdmin(EESAGScopedAdminMixin, admin.ModelAdmin):
    admin_scopes = {"COORDINATEUR", "BUREAU_GENERAL"}
    default_add = True
    default_change = True
    list_display = ("annee", "utilisateur", "poste", "actif", "date_nomination")
    list_filter = ("annee", "actif", "poste")
    search_fields = ("utilisateur__nom", "utilisateur__prenom", "poste")
    readonly_fields = ("date_nomination",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "utilisateur":
            kwargs["queryset"] = Utilisateur.objects.filter(
                role__in=ROLES_NATIONAUX,
                eglise__isnull=True,
            ).order_by("nom", "prenom")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if obj.utilisateur.role not in ROLES_NATIONAUX or obj.utilisateur.eglise_id:
            raise ValidationError("Un mandat national doit appartenir à un compte national sans église.")
        super().save_model(request, obj, form, change)


@admin.register(Abonnement)
class AbonnementAdmin(EESAGScopedAdminMixin, admin.ModelAdmin):
    admin_scopes = {"COORDINATEUR", "BUREAU_GENERAL", "BUREAU_SPECIAL", "EGLISE"}
    default_add = False
    default_change = False
    list_display = ("utilisateur", "eglise", "date_abonnement")
    list_filter = ("eglise",)
    search_fields = ("utilisateur__nom", "utilisateur__prenom", "eglise__nom")


@admin.register(JournalSMS)
class JournalSMSAdmin(EESAGScopedAdminMixin, admin.ModelAdmin):
    admin_scopes = {"COORDINATEUR"}
    default_add = False
    default_change = False
    list_display = ("cree_le", "telephone", "type_message", "fournisseur", "statut", "provider_sid")
    list_filter = ("statut", "fournisseur", "type_message", "cree_le")
    search_fields = ("telephone", "provider_sid", "erreur", "utilisateur__nom", "utilisateur__prenom")
    readonly_fields = ("cree_le", "telephone", "type_message", "fournisseur", "statut", "message", "provider_sid", "erreur", "utilisateur")
    ordering = ("-cree_le",)


@admin.register(VerificationTelephone)
class VerificationTelephoneAdmin(EESAGScopedAdminMixin, admin.ModelAdmin):
    admin_scopes = {"COORDINATEUR"}
    default_add = False
    default_change = False
    list_display = ("utilisateur", "code", "cree_le", "expire_le", "utilise", "tentatives")
    readonly_fields = ("utilisateur", "code", "cree_le", "expire_le", "utilise", "tentatives")
