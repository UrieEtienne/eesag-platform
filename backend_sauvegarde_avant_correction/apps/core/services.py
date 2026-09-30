from django.db import transaction
from .models import ActivationFonctionnalite, FonctionnaliteSysteme

DEFAULT_FEATURES = [
    ("membres", "Gestion des membres", "Église locale", 10),
    ("departements", "Départements", "Église locale", 20),
    ("bureaux", "Bureaux et mandats", "Gouvernance", 30),
    ("eglises", "Gestion des églises", "National", 40),
    ("administrateurs_eglises", "Administrateurs des églises", "National", 50),
    ("finances", "Comptabilité et finances", "Finance", 60),
    ("projets", "Projets", "Pilotage", 70),
    ("documents", "Documents", "Documents", 80),
    ("rapports", "Rapports", "Pilotage", 90),
    ("reunions", "Réunions vidéo", "Communication", 100),
    ("assistant_ia", "Assistant IA", "Intelligence", 110),
    ("notifications", "Notifications", "Communication", 120),
    ("courriers", "Courriers et recommandations", "Communication", 130),
]

@transaction.atomic
def ensure_default_features():
    for code, nom, groupe, ordre in DEFAULT_FEATURES:
        FonctionnaliteSysteme.objects.get_or_create(code=code, defaults={"nom": nom, "groupe": groupe, "ordre": ordre, "actif_global": True})


def feature_active(code, *, user=None, eglise=None, bureau=None):
    try:
        feature = FonctionnaliteSysteme.objects.get(code=code)
    except FonctionnaliteSysteme.DoesNotExist:
        return False
    if not feature.actif_global:
        return False
    if eglise is None and user is not None:
        eglise = getattr(user, "eglise", None)
    if bureau is None and user is not None:
        bureau = user.bureaux_administres.filter(actif=True).values_list("bureau_id", flat=True).first()
    if eglise is not None:
        override = ActivationFonctionnalite.objects.filter(fonctionnalite=feature, eglise=eglise).values_list("actif", flat=True).first()
        return feature.actif_global if override is None else override
    if bureau:
        override = ActivationFonctionnalite.objects.filter(fonctionnalite=feature, bureau_id=bureau).values_list("actif", flat=True).first()
        return feature.actif_global if override is None else override
    return feature.actif_global
