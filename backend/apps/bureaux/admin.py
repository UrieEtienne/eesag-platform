from django.contrib import admin
from django.utils.html import format_html
from .models import Bureau, BureauAdministrateur, BureauMembreMandat, NiveauBureau
from .views import a_droit_bureau, _est_coordinateur, _est_national_general, _bureaux_administres


@admin.register(Bureau)
class BureauAdmin(admin.ModelAdmin):
    list_display = ("nom", "code", "niveau", "type_bureau", "eglise", "actif")
    list_filter = ("niveau", "type_bureau", "actif")
    search_fields = ("nom", "code", "eglise__nom")
    readonly_fields = ("code", "date_creation")

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("eglise")
        if _est_coordinateur(request.user) or _est_national_general(request.user):
            return qs
        if request.user.role in ("SUPERADMIN_INTL", "SUPERADMIN_NATIONAL"):
            return qs.filter(administrateurs__utilisateur=request.user, administrateurs__actif=True).distinct()
        if request.user.role in ("PASTEUR", "ADMIN_LOCAL"):
            return qs.filter(niveau=NiveauBureau.LOCAL, eglise_id=request.user.eglise_id)
        return qs.filter(niveau=NiveauBureau.NATIONAL)

    def has_add_permission(self, request):
        return _est_coordinateur(request.user) or _est_national_general(request.user) or request.user.role in ("PASTEUR", "ADMIN_LOCAL")

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return True
        return a_droit_bureau(request.user, obj, "peut_gerer_membres")

    def has_delete_permission(self, request, obj=None):
        return _est_coordinateur(request.user)


@admin.register(BureauMembreMandat)
class BureauMembreMandatAdmin(admin.ModelAdmin):
    list_display = ("photo_membre", "bureau", "utilisateur", "poste", "annee", "actif")
    list_filter = ("annee", "actif", "bureau__niveau", "bureau__type_bureau")
    search_fields = ("utilisateur__identifiant", "utilisateur__nom", "utilisateur__prenom", "poste", "bureau__nom")
    list_select_related = ("bureau", "utilisateur")

    def photo_membre(self, obj):
        if obj.utilisateur.photo:
            return format_html('<img src="{}" style="width:42px;height:42px;border-radius:50%;object-fit:cover;">', obj.utilisateur.photo.url)
        return "—"
    photo_membre.short_description = "Photo"

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("bureau", "utilisateur")
        if _est_coordinateur(request.user) or _est_national_general(request.user):
            return qs
        if request.user.role in ("SUPERADMIN_INTL", "SUPERADMIN_NATIONAL"):
            return qs.filter(bureau__administrateurs__utilisateur=request.user, bureau__administrateurs__actif=True).distinct()
        if request.user.role in ("PASTEUR", "ADMIN_LOCAL"):
            return qs.filter(bureau__eglise_id=request.user.eglise_id)
        return qs.filter(bureau__niveau=NiveauBureau.NATIONAL)

    def has_change_permission(self, request, obj=None):
        return True if obj is None else a_droit_bureau(request.user, obj.bureau, "peut_gerer_membres")

    def has_delete_permission(self, request, obj=None):
        return True if obj is None else a_droit_bureau(request.user, obj.bureau, "peut_gerer_membres")


@admin.register(BureauAdministrateur)
class BureauAdministrateurAdmin(admin.ModelAdmin):
    list_display = ("bureau", "utilisateur", "peut_gerer_membres", "peut_gerer_finances", "peut_gerer_projets", "actif")
    list_filter = ("actif", "peut_gerer_finances", "peut_gerer_projets", "bureau__niveau")
    search_fields = ("utilisateur__identifiant", "utilisateur__nom", "utilisateur__prenom", "bureau__nom")

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("bureau", "utilisateur")
        if _est_coordinateur(request.user):
            return qs
        if _est_national_general(request.user):
            return qs.filter(bureau__niveau=NiveauBureau.NATIONAL)
        return qs.filter(bureau__administrateurs__utilisateur=request.user, bureau__administrateurs__actif=True).distinct()

    def has_change_permission(self, request, obj=None):
        return True if obj is None else a_droit_bureau(request.user, obj.bureau, "peut_gerer_membres")

    def has_delete_permission(self, request, obj=None):
        return _est_coordinateur(request.user) or (obj is not None and a_droit_bureau(request.user, obj.bureau, "peut_gerer_membres"))

from .models import BureauMembre


@admin.register(BureauMembre)
class BureauMembreAdmin(admin.ModelAdmin):
    list_display = ("photo_admin", "nom_complet", "bureau", "poste", "annee", "actif")
    list_filter = ("annee", "actif", "bureau__niveau", "bureau__type_bureau")
    search_fields = ("nom_complet", "poste", "bureau__nom", "bureau__code")
    list_select_related = ("bureau",)
    ordering = ("bureau__nom", "annee", "ordre", "nom_complet")

    def photo_admin(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="width:72px;height:72px;border-radius:14px;object-fit:cover;">',
                obj.photo.url,
            )
        return format_html('<span style="font-size:28px;">👤</span>')
    photo_admin.short_description = "Photo"

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("bureau")
        if _est_coordinateur(request.user) or _est_national_general(request.user):
            return qs
        return qs.filter(bureau__administrateurs__utilisateur=request.user, bureau__administrateurs__actif=True).distinct()
