from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"

    def ready(self):
        from django.db.models.signals import post_migrate
        from .services import ensure_default_features

        def seed(sender, **kwargs):
            try:
                ensure_default_features()
            except Exception:
                pass

        post_migrate.connect(seed, sender=self, weak=False)
