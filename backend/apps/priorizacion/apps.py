from django.apps import AppConfig


class PriorizacionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.priorizacion'
    verbose_name = 'Priorización POA'

    def ready(self):
        import apps.priorizacion.signals  # noqa: F401
