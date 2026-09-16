from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def creer_bureaux_nationaux_par_defaut(sender, **kwargs):
    if sender.name != "apps.bureaux":
        return
    from .models import Bureau, NiveauBureau, TypeBureau
    defaults = {
        TypeBureau.AUTRE: "Bureau National",
        TypeBureau.FEMMES: "Bureau National des Femmes",
        TypeBureau.JEUNESSE: "Bureau National de la Jeunesse",
        TypeBureau.ENFANTS: "Bureau National des Enfants",
        TypeBureau.EVANGELISATION: "Équipe Nationale d'Évangélisation",
        TypeBureau.HOMMES: "Bureau National des Hommes",
        TypeBureau.FAMILLES: "Bureau National des Familles",
        TypeBureau.COMMUNICATION: "Bureau National de la Communication",
        TypeBureau.MUSIQUE: "Bureau National de la Musique",
        TypeBureau.MISSIONS: "Bureau National des Missions",
    }
    for type_bureau, nom in defaults.items():
        Bureau.objects.get_or_create(
            niveau=NiveauBureau.NATIONAL,
            type_bureau=type_bureau,
            eglise=None,
            defaults={"nom": nom, "actif": True},
        )
