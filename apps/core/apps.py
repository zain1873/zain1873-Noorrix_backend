from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Project-level home for maintenance commands that span apps."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
