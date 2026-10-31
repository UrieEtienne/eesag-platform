from rest_framework import serializers
from apps.accounts.models import Role
from .models import (
    Bureau,
    BureauZone,
    BureauMembre,
    BureauMembreMandat,
    BureauAdministrateur,
)

class BureauSerializer(serializers.ModelSerializer):
    eglise_nom = serializers.CharField(
        source="eglise.nom",
        read_only=True,
        default=None,
    )
    type_bureau_libelle = serializers.CharField(
        source="get_type_bureau_display",
        read_only=True,
    )
    niveau_libelle = serializers.CharField(
        source="get_niveau_display",
        read_only=True,
    )
    membres_actifs = serializers.IntegerField(read_only=True)
    mes_droits = serializers.SerializerMethodField()

    class Meta:
        model = Bureau
        fields = [
            "id",
            "nom",
            "code",
            "niveau",
            "niveau_libelle",
            "type_bureau",
            "type_bureau_libelle",
            "eglise",
            "eglise_nom",
            "zone",
            "bureau_parent",
            "description",
            "actif",
            "membres_actifs",
            "date_creation",
            "mes_droits",
        ]
        read_only_fields = [
            "id",
            "code",
            "date_creation",
            "membres_actifs",
            "mes_droits",
        ]

    def get_mes_droits(self, obj):
        from .access import _est_coordinateur, a_droit_bureau

        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return {}

        user = request.user

        droits = [
            "peut_gerer_membres",
            "peut_gerer_finances",
            "peut_gerer_projets",
            "peut_envoyer_notifications",
            "peut_gerer_rapports",
            "peut_gerer_utilisateurs",
            "peut_creer_bureaux",
            "peut_gerer_eglises",
            "peut_gerer_bureaux_zonaux",
        ]

        if _est_coordinateur(user):
            return {droit: True for droit in droits}

        return {
            droit: a_droit_bureau(user, obj, droit)
            for droit in droits
        }
class BureauZoneSerializer(serializers.ModelSerializer):
    region_nom = serializers.CharField(
        source="region.nom",
        read_only=True,
    )
    bureaux_count = serializers.IntegerField(
        read_only=True,
        required=False,
    )

    class Meta:
        model = BureauZone
        fields = [
            "id",
            "nom",
            "code",
            "region",
            "region_nom",
            "description",
            "actif",
            "date_creation",
            "bureaux_count",
        ]
        read_only_fields = [
            "id",
            "code",
            "date_creation",
            "region_nom",
            "bureaux_count",
        ]

    # Les droits doivent venir du bureau auquel le compte est réellement administrateur.
    def get_mes_droits(self, obj):
        from .access import _est_coordinateur, a_droit_bureau

        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return {}

        user = request.user
        droits = [
            "peut_gerer_membres",
            "peut_gerer_finances",
            "peut_gerer_projets",
            "peut_envoyer_notifications",
            "peut_gerer_rapports",
            "peut_gerer_utilisateurs",
            "peut_creer_bureaux",
            "peut_gerer_eglises",
            "peut_gerer_bureaux_zonaux",
        ]

        if _est_coordinateur(user):
            return {droit: True for droit in droits}

        return {
            droit: a_droit_bureau(user, obj, droit)
            for droit in droits
        }

        # ============================================================
        # COORDINATEUR
        # ============================================================
        # Le Coordinateur possède les droits système complets.
        # Il n'est cependant pas enregistré comme administrateur
        # du bureau.
        if user.role == "COORDINATEUR" or user.is_superuser:
            return {droit: True for droit in DROITS}

        # ============================================================
        # ADMINISTRATEUR DU BUREAU
        # ============================================================
        # Tous les autres utilisateurs obtiennent leurs droits
        # exclusivement depuis BureauAdministrateur.
        admin = BureauAdministrateur.objects.filter(
            bureau=obj,
            utilisateur=user,
            actif=True,
        ).first()

        # Aucun administrateur actif pour ce bureau
        if not admin:
            return {droit: False for droit in DROITS}

        # ============================================================
        # DROITS ATTRIBUÉS À CET ADMINISTRATEUR
        # ============================================================
        return {
            "peut_gerer_membres": admin.peut_gerer_membres,
            "peut_gerer_finances": admin.peut_gerer_finances,
            "peut_gerer_projets": admin.peut_gerer_projets,
            "peut_envoyer_notifications": admin.peut_envoyer_notifications,
            "peut_gerer_rapports": admin.peut_gerer_rapports,
        }


class BureauMembreMandatSerializer(serializers.ModelSerializer):
    nom_complet = serializers.SerializerMethodField(read_only=True)

    photo = serializers.ImageField(
        source="utilisateur.photo",
        read_only=True,
    )

    identifiant = serializers.CharField(
        source="utilisateur.identifiant",
        read_only=True,
    )

    bureau_nom = serializers.CharField(
        source="bureau.nom",
        read_only=True,
    )

    class Meta:
        model = BureauMembreMandat
        fields = [
            "id",
            "bureau",
            "bureau_nom",
            "utilisateur",
            "identifiant",
            "nom_complet",
            "photo",
            "annee",
            "poste",
            "objectif_annuel",
            "actif",
            "date_nomination",
        ]
        read_only_fields = ["id", "date_nomination"]

    def validate(self, attrs):
        bureau = attrs.get(
            "bureau",
            getattr(self.instance, "bureau", None),
        )
        utilisateur = attrs.get(
            "utilisateur",
            getattr(self.instance, "utilisateur", None),
        )

        if bureau and utilisateur:
            if utilisateur.role == "COORDINATEUR":
                raise serializers.ValidationError({
                    "utilisateur": (
                        "Le Coordinateur est propriétaire du système "
                        "et ne peut pas être membre d'un bureau."
                    )
                })

            if bureau.niveau == "NATIONAL" and utilisateur.eglise_id:
                raise serializers.ValidationError({
                    "utilisateur": (
                        "Un membre d'un bureau national ne doit pas "
                        "être rattaché à une église."
                    )
                })

            if (
                bureau.niveau == "LOCAL"
                and utilisateur.eglise_id != bureau.eglise_id
            ):
                raise serializers.ValidationError({
                    "utilisateur": (
                        "Le membre doit appartenir à la même église "
                        "que le bureau local."
                    )
                })

        return attrs

    def validate_annee(self, value):
        if value < 2000 or value > 2100:
            raise serializers.ValidationError(
                "Année de mandat invalide."
            )
        return value

    def get_nom_complet(self, obj):
        return (
            f"{obj.utilisateur.prenom} "
            f"{obj.utilisateur.nom}"
        ).strip()


    
class BureauMembreSerializer(serializers.ModelSerializer):
    nom_complet = serializers.SerializerMethodField(read_only=True)
    identifiant = serializers.CharField(
        source="utilisateur.identifiant",
        read_only=True,
    )
    photo = serializers.ImageField(
        source="utilisateur.photo",
        read_only=True,
    )
    bureau_nom = serializers.CharField(
        source="bureau.nom",
        read_only=True,
    )

    class Meta:
        model = BureauMembre
        fields = [
            "id",
            "bureau",
            "bureau_nom",
            "utilisateur",
            "identifiant",
            "nom_complet",
            "photo",
            "poste",
            "actif",
        ]

    def get_nom_complet(self, obj):
        return (
            f"{obj.utilisateur.prenom} "
            f"{obj.utilisateur.nom}"
        ).strip()

class BureauAdministrateurSerializer(serializers.ModelSerializer):
    nom_complet = serializers.SerializerMethodField(read_only=True)
    bureau_nom = serializers.CharField(source="bureau.nom", read_only=True)

    class Meta:
        model = BureauAdministrateur
        fields = [
            "id",
            "bureau",
            "bureau_nom",
            "utilisateur",
            "nom_complet",
            "peut_gerer_membres",
            "peut_gerer_finances",
            "peut_gerer_projets",
            "peut_envoyer_notifications",
            "peut_gerer_rapports",
            "actif",
            "date_attribution",
        ]
        read_only_fields = ["date_attribution"]

    def validate(self, attrs):
        bureau = attrs.get(
            "bureau",
            getattr(self.instance, "bureau", None),
        )
        utilisateur = attrs.get(
            "utilisateur",
            getattr(self.instance, "utilisateur", None),
        )

        if not bureau or not utilisateur:
            return attrs

        if utilisateur.role == Role.COORDINATEUR:
            raise serializers.ValidationError(
                "Le Coordinateur ne peut pas être administrateur d'un bureau."
            )

        if not utilisateur.actif:
            raise serializers.ValidationError(
                "Un compte inactif ne peut pas recevoir une affectation."
            )

        if bureau.niveau == NiveauBureau.NATIONAL:
            if utilisateur.eglise_id:
                raise serializers.ValidationError(
                    "Un administrateur national ne doit pas être rattaché à une église."
                )

        elif bureau.niveau == NiveauBureau.LOCAL:
            if utilisateur.eglise_id != bureau.eglise_id:
                raise serializers.ValidationError(
                    "L'administrateur local doit appartenir à la même église."
                )

        if attrs.get(
            "peut_gerer_finances",
            getattr(self.instance, "peut_gerer_finances", False),
        ):
            if utilisateur.role not in {
                Role.SUPERADMIN_INTL,
                Role.SUPERADMIN_NATIONAL,
                Role.ADMIN_LOCAL,
                Role.PASTEUR,
                Role.RESPONSABLE_DEPARTEMENT,
            }:
                raise serializers.ValidationError({
                    "utilisateur": (
                        "Ce compte n'a pas un rôle administratif "
                        "ou de responsabilité autorisé pour la gestion financière."
                    )
                })

        return attrs

    def get_nom_complet(self, obj):
        return f"{obj.utilisateur.prenom} {obj.utilisateur.nom}".strip()