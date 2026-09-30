from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import serializers

from apps.accounts.models import Utilisateur, Role
from .models import Religion, Eglise, Departement, RoleEglise, Annexe
from apps.accounts.services_sms import normaliser_telephone


class ReligionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Religion
        fields = ["id", "nom", "description"]


class DepartementSerializer(serializers.ModelSerializer):
    nombre_membres = serializers.IntegerField(read_only=True)

    class Meta:
        model = Departement
        fields = ["id", "nom", "nombre_membres"]
        read_only_fields = ["id", "nombre_membres"]


class RoleEgliseSerializer(serializers.ModelSerializer):
    nombre_membres = serializers.IntegerField(source="membres.count", read_only=True)

    class Meta:
        model = RoleEglise
        fields = ["id", "nom", "actif", "nombre_membres"]
        read_only_fields = ["id", "nombre_membres"]


class AnnexeSerializer(serializers.ModelSerializer):
    eglise_nom = serializers.CharField(source="eglise.nom", read_only=True)
    responsable_nom = serializers.SerializerMethodField()

    class Meta:
        model = Annexe
        fields = ["id", "eglise", "eglise_nom", "nom", "code", "adresse", "telephone", "responsable", "responsable_nom", "active", "date_creation"]
        read_only_fields = ["code", "eglise"]

    def get_responsable_nom(self, obj):
        return f"{obj.responsable.prenom} {obj.responsable.nom}" if obj.responsable else None


class EgliseListSerializer(serializers.ModelSerializer):
    religion_nom = serializers.CharField(source="religion.nom", read_only=True)
    region_nom = serializers.CharField(source="region.nom", read_only=True)
    prefecture_nom = serializers.CharField(source="prefecture.nom", read_only=True)
    district_nom = serializers.CharField(source="district.nom", read_only=True)
    commune_nom = serializers.CharField(source="commune.nom", read_only=True, default=None)
    responsable_nom = serializers.SerializerMethodField()
    responsable_source = serializers.SerializerMethodField()
    nombre_membres = serializers.IntegerField(read_only=True)

    class Meta:
        model = Eglise
        fields = [
            "id", "code", "nom",
            "region", "region_nom", "prefecture", "prefecture_nom",
            "district", "district_nom", "commune", "commune_nom",
            "statut", "plateforme_active", "responsable", "responsable_nom", "responsable_source", "nombre_membres", "logo",
        ]
        read_only_fields = ["code", "responsable", "nombre_membres"]

    def get_responsable_nom(self, obj):
        if obj.responsable:
            return f"{obj.responsable.prenom} {obj.responsable.nom}"
        return obj.responsable_nom or None

    def get_responsable_source(self, obj):
        if obj.responsable:
            return "compte_eesag"
        if obj.responsable_nom:
            return "nom_saisi"
        return None


class EgliseAnnuaireSerializer(serializers.ModelSerializer):
    """Fiche d'annuaire volontairement minimale pour les utilisateurs locaux."""
    region_nom = serializers.CharField(source="region.nom", read_only=True)
    prefecture_nom = serializers.CharField(source="prefecture.nom", read_only=True)
    district_nom = serializers.CharField(source="district.nom", read_only=True)
    commune_nom = serializers.CharField(source="commune.nom", read_only=True, default=None)

    class Meta:
        model = Eglise
        fields = ["id", "code", "nom",  "region_nom", "prefecture_nom", "district_nom", "commune_nom", "statut", "plateforme_active"]
        read_only_fields = fields


class EgliseDetailSerializer(EgliseListSerializer):
    departements = serializers.SerializerMethodField()

    def get_departements(self, obj):
        # Departement est un référentiel partagé dans la version actuelle du
        # modèle. On expose ici uniquement les départements utilisés par les
        # membres de l'église consultée.
        ids = (
            Utilisateur.objects
            .filter(eglise_id=obj.id, departement_id__isnull=False)
            .values_list("departement_id", flat=True)
            .distinct()
        )
        return DepartementSerializer(
            Departement.objects.filter(id__in=ids).annotate(
                nb_membres=Count("membres_departement", filter=Q(membres_departement__actif=True, membres_departement__eglise_id=obj.id))
            ).order_by("nom"),
            many=True,
        ).data
    annexes = AnnexeSerializer(many=True, read_only=True)

    class Meta(EgliseListSerializer.Meta):
        fields = EgliseListSerializer.Meta.fields + [
            "adresse_precise", "telephone", "email", "date_creation",
            "date_enregistrement_systeme", "departements", "annexes",
        ]


class EgliseCreateSerializer(serializers.ModelSerializer):
    """Création d'une église uniquement.

    La création d'un compte administrateur local est volontairement séparée
    et se fait exclusivement dans Django Admin par le Coordinateur ou le
    Bureau national général. Une église créée par l'API/frontend reste
    désactivée et ne crée aucun compte de connexion.
    """

    responsable_utilisateur = serializers.PrimaryKeyRelatedField(
        source="responsable",
        queryset=Utilisateur.objects.exclude(role=Role.COORDINATEUR),
        write_only=True,
        required=False,
        allow_null=True,
    )
    responsable_nom = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=200)
    responsable_telephone = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=20)
    responsable_email = serializers.EmailField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Eglise
        fields = [
            "id", "code", "nom", "region", "prefecture", "district", "commune",
            "adresse_precise", "telephone", "email", "date_creation", "statut", "plateforme_active", "logo",
            "responsable_utilisateur", "responsable_nom", "responsable_telephone", "responsable_email",
        ]
        read_only_fields = ["id", "code", "statut", "plateforme_active"]

    def validate(self, attrs):
        responsable = attrs.get("responsable")
        responsable_nom = (attrs.get("responsable_nom") or "").strip()
        responsable_telephone = attrs.get("responsable_telephone") or ""

        if responsable and responsable.role == Role.COORDINATEUR:
            raise serializers.ValidationError({
                "responsable_utilisateur": "Le Coordinateur du système ne peut pas être responsable d'une église."
            })

        if responsable_telephone:
            try:
                attrs["responsable_telephone"] = normaliser_telephone(responsable_telephone)
            except ValueError as exc:
                raise serializers.ValidationError({"responsable_telephone": str(exc)})

        if not responsable and not responsable_nom:
            raise serializers.ValidationError({
                "responsable_nom": "Saisissez le nom du responsable ou sélectionnez un responsable déjà enregistré."
            })
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        eglise = Eglise.objects.create(**validated_data)
        # Une création depuis le frontend ne peut jamais ouvrir l'accès.
        eglise.plateforme_active = False
        eglise.date_activation_plateforme = None
        eglise.activee_par = None
        eglise.save(update_fields=["plateforme_active", "date_activation_plateforme", "activee_par"])
        return eglise
