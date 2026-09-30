from django.core.management.base import BaseCommand
from django.db import connection
from apps.churches.models import Departement, RoleEglise

class Command(BaseCommand):
    help = "Ajoute au schéma existant les rattachements église des départements et postes."
    def _has_column(self, table, column):
        with connection.cursor() as cursor:
            cols = {c.name for c in connection.introspection.get_table_description(cursor, table)}
        return column in cols
    def _add_field_if_missing(self, model, field_name):
        field = model._meta.get_field(field_name)
        if self._has_column(model._meta.db_table, field.column):
            return False
        with connection.schema_editor() as schema_editor:
            schema_editor.add_field(model, field)
        return True
    def handle(self, *args, **options):
        changed=[]
        for model, field in ((Departement,"eglise"),(RoleEglise,"eglise"),(RoleEglise,"departement")):
            if self._add_field_if_missing(model, field): changed.append(f"{model.__name__}.{field}")
        self.stdout.write(self.style.SUCCESS("Structure église installée. " + ("Colonnes ajoutées: "+", ".join(changed) if changed else "Aucune colonne à ajouter.")))
        self.stdout.write("Les anciens référentiels sans église sont conservés mais masqués aux espaces locaux.")
