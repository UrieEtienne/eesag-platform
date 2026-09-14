from django import forms
from django.contrib import admin
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    Abonnement,
    DelegationEglise,
    MandatBureauNational,
    JournalSMS,
    PermissionEglise,
    ROLES_NATIONAUX,
    ROLES_BUREAU_NATIONAL,
    Role,
    Utilisateur,
    VerificationTelephone,
)


class UtilisateurAdminForm(forms.ModelForm):
    mot_de_passe = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text="Laisser vide lors de la modification pour conserver le mot de passe actuel.",
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
            "role", "eglise", "departement", "role_eglise", "fonction_bureau_national", "actif", "is_staff", "is_superuser",
        )

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        # Le coordinateur est le seul à créer/gérer les comptes du Bureau national.
        if request and request.user.role == Role.COORDINATEUR:
            self.fields["role"].choices = [
                (Role.SUPERADMIN_NATIONAL, "Administrateur du Bureau national"),
                (Role.MEMBRE, "Membre"),
            ]
        elif request and request.user.role in ROLES_NATIONAUX:
            # Le Bureau national crée uniquement les comptes rattachés à une église.
            self.fields["role"].choices = [
                (Role.ADMIN_LOCAL, "Administrateur Local (église)"),
                (Role.PASTEUR, "Pasteur"),
                (Role.RESPONSABLE_DEPARTEMENT, "Responsable de département"),
                (Role.MEMBRE, "Membre"),
            ]
        # Le rôle coordinateur ne doit jamais être créé depuis ce formulaire.
        self.fields["role"].empty_label = None

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get("role")
        eglise = cleaned.get("eglise")
        password = cleaned.get("mot_de_passe")
        confirmation = cleaned.get("confirmation_mot_de_passe")
        requester = getattr(self, "request", None)
        requester_role = getattr(getattr(requester, "user", None), "role", None)

        if requester_role == Role.COORDINATEUR:
            if role in ROLES_NATIONAUX and eglise:
                self.add_error("eglise", "Un compte du Bureau national ne doit pas être lié à une église.")
            if role not in ROLES_NATIONAUX and not eglise and role != Role.MEMBRE:
                self.add_error("eglise", "Une église doit être sélectionnée pour ce rôle.")
            if role == Role.MEMBRE and not eglise and not self.instance.pk:
                # Le coordinateur peut aussi créer un compte national simple pour le bureau.
                pass
        elif requester_role in ROLES_NATIONAUX:
            if role in ROLES_NATIONAUX:
                self.add_error("role", "Seul le Coordinateur peut créer un compte du Bureau national.")
            if not eglise:
                self.add_error("eglise", "Une église doit être sélectionnée pour un compte local.")

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
        requester_role = getattr(getattr(self.request, "user", None), "role", None)

        if role in ROLES_NATIONAUX:
            obj.eglise = None
            obj.departement = None
            obj.is_staff = True
            # Le Coordinateur est le seul propriétaire/superuser.
            # Le Bureau national est staff sans devenir propriétaire du système.
            obj.is_superuser = False
            obj.fonction_eglise = "MEMBRE"
        else:
            obj.is_superuser = False
            # Les comptes locaux utilisent l'application métier, pas l'administration globale.
            obj.is_staff = False

        if password:
            obj.set_password(password)
        if commit:
            obj.save()
            self.save_m2m()
        return obj


class PerimetreUtilisateurFilter(admin.SimpleListFilter):
    title = "Périmètre"
    parameter_name = "perimetre"

    def lookups(self, request, model_admin):
        return (("national", "Bureau national"), ("eglise", "Églises locales"))

    def queryset(self, request, queryset):
        if self.value() == "national":
            return queryset.filter(eglise__isnull=True).exclude(role=Role.COORDINATEUR)
        if self.value() == "eglise":
            return queryset.filter(eglise__isnull=False)
        return queryset


@admin.register(Utilisateur)
class UtilisateurAdmin(admin.ModelAdmin):
    form = UtilisateurAdminForm
    list_display = ("miniature", "identifiant", "nom_complet", "role", "eglise", "fonction_bureau_national", "telephone", "actif")
    list_filter = (PerimetreUtilisateurFilter, "role", "eglise", "sexe", "nationalite", "actif", "is_staff")
    search_fields = ("identifiant", "nom", "prenom", "telephone", "email")
    ordering = ("nom", "prenom")
    readonly_fields = ("identifiant", "last_login", "date_enregistrement")

    def get_form(self, request, obj=None, **kwargs):
        BaseForm = super().get_form(request, obj, **kwargs)
        class RequestAwareForm(BaseForm):
            def __init__(self, *args, **form_kwargs):
                form_kwargs["request"] = request
                super().__init__(*args, **form_kwargs)
        return RequestAwareForm

    def get_fieldsets(self, request, obj=None):
        permissions = ("actif", "is_staff", "is_superuser") if request.user.role == Role.COORDINATEUR else ("actif",)
        return (
            ("Identité", {"fields": ("identifiant", "nom", "prenom", "sexe", "date_naissance", "nationalite", "photo")} ),
            ("Contact & vie de l’église", {"fields": (
                "telephone", "email", "date_bapteme_eau", "date_bapteme_saint_esprit", "fonction_eglise",
            )}),
            ("Rôle et rattachement", {"fields": ("role", "eglise", "departement", "role_eglise", "fonction_bureau_national")}),
            ("Mot de passe", {"fields": ("mot_de_passe", "confirmation_mot_de_passe")} ),
            ("Statut technique", {"fields": permissions}),
            ("Historique", {"fields": ("last_login", "date_enregistrement")} ),
        )

    def miniature(self, obj):
        if not obj.photo:
            return "—"
        return format_html('<img src="{}" alt="" style="width:38px;height:38px;object-fit:cover;border-radius:50%;">', obj.photo.url)
    miniature.short_description = "Photo"

    def nom_complet(self, obj):
        return f"{obj.prenom} {obj.nom}"
    nom_complet.short_description = "Nom complet"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == Role.COORDINATEUR:
            # Le propriétaire du système ne doit jamais apparaître dans la liste des utilisateurs.
            # Il reste modifiable depuis le lien « Mon compte ».
            object_id = str(getattr(getattr(request, "resolver_match", None), "kwargs", {}).get("object_id", ""))
            if object_id == str(request.user.pk):
                return qs.filter(pk=request.user.pk)
            return qs.exclude(role=Role.COORDINATEUR)
        if request.user.role in ROLES_NATIONAUX:
            from apps.bureaux.models import BureauAdministrateur
            assigned = BureauAdministrateur.objects.filter(utilisateur=request.user, actif=True).values_list("bureau_id", flat=True)
            if assigned.exists() and request.user.role != Role.COORDINATEUR:
                return qs.filter(mandats_bureaux__bureau_id__in=assigned, mandats_bureaux__actif=True).exclude(role=Role.COORDINATEUR).distinct()
            return qs.exclude(role=Role.COORDINATEUR)
        if request.user.eglise_id:
            return qs.filter(eglise_id=request.user.eglise_id)
        return qs.none()

    def has_add_permission(self, request):
        if request.user.role == Role.COORDINATEUR:
            return True
        if request.user.role in ROLES_BUREAU_NATIONAL:
            from apps.bureaux.models import BureauAdministrateur
            return not BureauAdministrateur.objects.filter(utilisateur=request.user, actif=True).exists()
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.role == Role.COORDINATEUR

    def has_change_permission(self, request, obj=None):
        if obj is not None and request.user.role != Role.COORDINATEUR and obj.role in ROLES_NATIONAUX:
            return False
        if obj is not None and request.user.role not in ROLES_NATIONAUX:
            return obj.eglise_id == request.user.eglise_id
        return super().has_change_permission(request, obj)

    def save_model(self, request, obj, form, change):
        # Les règles de rattachement et du mot de passe sont dans le formulaire.
        # Toute nouvelle création déclenche une vérification téléphonique par OTP.
        with transaction.atomic():
            super().save_model(request, obj, form, change)
            if not change:
                from datetime import timedelta
                VerificationTelephone.objects.filter(utilisateur=obj, utilise=False).update(utilise=True)
                VerificationTelephone.objects.create(
                    utilisateur=obj, code="000000", expire_le=timezone.now() + timedelta(minutes=10)
                )
                from .services_sms import notifier_nouvel_identifiant
                origine = obj.eglise.nom if obj.eglise else "Bureau national EESAG"
                mot_de_passe = form.cleaned_data.get("mot_de_passe") or "le code secret défini par votre administrateur"
                resultats = notifier_nouvel_identifiant(obj, mot_de_passe, origine=origine)
                if not all(item.get("ok") for item in resultats):
                    raise ValidationError("Le compte est refusé : le SMS de confirmation n'a pas pu être envoyé. Consultez le Journal SMS.")
                obj.actif = False
                obj.save(update_fields=["actif"])


@admin.register(PermissionEglise)
class PermissionEgliseAdmin(admin.ModelAdmin):
    list_display = ("code", "libelle", "description")
    search_fields = ("code", "libelle", "description")


@admin.register(DelegationEglise)
class DelegationEgliseAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "eglise_utilisateur", "actif", "date_creation", "cree_par")
    list_filter = ("actif",)
    search_fields = ("utilisateur__nom", "utilisateur__prenom", "utilisateur__identifiant")
    filter_horizontal = ("permissions",)
    readonly_fields = ("date_creation", "cree_par")

    def eglise_utilisateur(self, obj):
        return obj.utilisateur.eglise or "Bureau national"
    eglise_utilisateur.short_description = "Périmètre"

    def save_model(self, request, obj, form, change):
        if not change:
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)


@admin.register(MandatBureauNational)
class MandatBureauNationalAdmin(admin.ModelAdmin):
    list_display = ("annee", "utilisateur", "poste", "actif", "date_nomination")
    list_filter = ("annee", "actif", "poste")
    search_fields = ("utilisateur__nom", "utilisateur__prenom", "poste")
    readonly_fields = ("date_nomination",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "utilisateur":
            kwargs["queryset"] = Utilisateur.objects.filter(role__in=ROLES_NATIONAUX, eglise__isnull=True).order_by("nom", "prenom")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if obj.utilisateur.role not in ROLES_NATIONAUX:
            raise ValidationError("Un mandat du Bureau national doit être attribué à un compte national.")
        if obj.utilisateur.eglise_id:
            raise ValidationError("Un membre du Bureau national ne doit pas être rattaché à une église.")
        super().save_model(request, obj, form, change)


@admin.register(Abonnement)
class AbonnementAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "eglise", "date_abonnement")
    list_filter = ("eglise",)
    search_fields = ("utilisateur__nom", "utilisateur__prenom", "eglise__nom")


@admin.register(JournalSMS)
class JournalSMSAdmin(admin.ModelAdmin):
    list_display = ("cree_le", "telephone", "type_message", "fournisseur", "statut", "provider_sid")
    list_filter = ("statut", "fournisseur", "type_message", "cree_le")
    search_fields = ("telephone", "provider_sid", "erreur", "utilisateur__nom", "utilisateur__prenom")
    readonly_fields = ("cree_le", "telephone", "type_message", "fournisseur", "statut", "message", "provider_sid", "erreur", "utilisateur")
    ordering = ("-cree_le",)
