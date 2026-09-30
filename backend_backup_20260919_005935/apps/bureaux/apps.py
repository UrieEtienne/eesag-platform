from django.apps import AppConfig


class BureauxConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.bureaux"
    verbose_name = "Bureaux nationaux et locaux"

    def ready(self):
        from . import signals  # noqa: F401
