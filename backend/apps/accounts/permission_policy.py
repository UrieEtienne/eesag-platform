"""Politique EESAG : séparation stricte Coordinateur / National / Local."""

from .models import Role

NATIONAL = {Role.SUPERADMIN_INTL, Role.SUPERADMIN_NATIONAL}
LOCAL = {Role.ADMIN_LOCAL, Role.PASTEUR}


def is_coordinateur(user):
    return bool(user and (user.role == Role.COORDINATEUR or user.is_superuser))


def is_bureau_national(user):
    return bool(user and user.role in NATIONAL)


def is_local(user):
    return bool(user and user.role in LOCAL and user.eglise_id)


def is_admin_local(user):
    return bool(user and user.role == Role.ADMIN_LOCAL and user.eglise_id)


def peut_voir_administration_eglise(user):
    # Seul ADMIN_LOCAL peut voir/utiliser cette page.
    return is_admin_local(user)


def peut_gerer_utilisateur(demandeur, cible):
    if not demandeur or not demandeur.is_authenticated:
        return False
    if is_coordinateur(demandeur):
        return True
    if cible and cible.role == Role.COORDINATEUR:
        return False
    if is_bureau_national(demandeur):
        return True
    if is_admin_local(demandeur):
        return bool(cible and cible.eglise_id == demandeur.eglise_id and cible.role == Role.ADMIN_LOCAL)
    if demandeur.role == Role.PASTEUR:
        return False
    return False


def peut_creer_role(demandeur, role):
    if is_coordinateur(demandeur):
        return True
    if is_bureau_national(demandeur):
        return role in {Role.SUPERADMIN_INTL, Role.SUPERADMIN_NATIONAL, Role.ADMIN_LOCAL, Role.PASTEUR}
    if is_admin_local(demandeur):
        return role in {
            Role.ADMIN_LOCAL,
            Role.PASTEUR,
            Role.RESPONSABLE_DEPARTEMENT,
            Role.MEMBRE,
        }
    return False


def peut_gerer_eglise(demandeur):
    return is_coordinateur(demandeur) or is_bureau_national(demandeur)


def peut_gerer_donnees_locales(demandeur, eglise_id):
    return is_coordinateur(demandeur) or (
        is_local(demandeur) and demandeur.eglise_id == eglise_id
    )
