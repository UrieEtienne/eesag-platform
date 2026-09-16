from datetime import date
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.accounts.models import Utilisateur, Role, PermissionEglise
from apps.geo.models import Region, Prefecture, District, Commune
from apps.churches.models import Religion, Eglise, Departement

PERMISSIONS = [
("GESTION_MEMBRES","Gestion des membres","Créer, modifier et rechercher les membres de l'église."),
("GESTION_DEPARTEMENTS","Gestion des départements","Créer les départements et leurs responsables."),
("GESTION_FINANCES","Gestion financière","Suivre les opérations et projets financiers."),
("GESTION_DOCUMENTS","Gestion des documents","Envoyer et recevoir les documents."),
("GESTION_NOTIFICATIONS","Notifications","Publier et envoyer les notifications de l'église."),
("GESTION_COURRIERS","Courriers","Préparer et envoyer les lettres/recommandations."),
("GESTION_PROJETS","Gestion des projets","Créer et suivre les projets."),
("GESTION_RAPPORTS","Rapports","Générer, exporter et imprimer les rapports."),
("GESTION_ADMINISTRATEURS","Gestion des administrateurs","Créer et déléguer des administrateurs."),
]

class Command(BaseCommand):
    help = "Amorce le système et installe les permissions fonctionnelles."
    def add_arguments(self, parser):
        parser.add_argument("--identifiant", default="COORD-001")
        parser.add_argument("--code-secret", default="admin1234")
    @transaction.atomic
    def handle(self,*args,**options):
        for code,libelle,description in PERMISSIONS:
            PermissionEglise.objects.get_or_create(code=code,defaults={"libelle":libelle,"description":description})
        self.stdout.write(self.style.SUCCESS("Permissions d'église prêtes."))
        identifiant=options["identifiant"]; code_secret=options["code_secret"]
        coordinateur=Utilisateur.objects.filter(role=Role.COORDINATEUR).first()
        if not coordinateur:
            coordinateur=Utilisateur(nom="Système",prenom="Coordinateur",role=Role.COORDINATEUR,telephone="+224600000000",is_staff=True,is_superuser=True,fonction_bureau_national="Coordinateur du système")
            coordinateur.identifiant=identifiant; coordinateur.set_password(code_secret); coordinateur.save()
            self.stdout.write(self.style.SUCCESS(f"Coordinateur créé -> {identifiant} / {code_secret}"))
        region,_=Region.objects.get_or_create(nom="Région de Conakry")
        prefecture,_=Prefecture.objects.get_or_create(nom="Conakry",region=region)
        district,_=District.objects.get_or_create(nom="Kaloum",prefecture=prefecture)
        commune,_=Commune.objects.get_or_create(nom="Centre-ville",district=district)
        religion,_=Religion.objects.get_or_create(nom="Christianisme",defaults={"description":"Ensemble des églises chrétiennes recensées par la plateforme."})
        if not Eglise.objects.exists():
            eglise=Eglise.objects.create(nom="Église de la Grâce",religion=religion,region=region,prefecture=prefecture,district=district,commune=commune,adresse_precise="Avenue de la République",telephone="+224620000000",date_creation=date(2010,1,1))
            Departement.objects.create(nom="Chorale",eglise=eglise); Departement.objects.create(nom="Jeunesse",eglise=eglise)
            self.stdout.write(self.style.SUCCESS(f"Église de démonstration créée : {eglise.nom} ({eglise.code})"))
        self.stdout.write(self.style.SUCCESS("Amorçage terminé."))
