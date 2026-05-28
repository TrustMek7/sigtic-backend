from django.apps import AppConfig


class SiggoReadonlyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.siggo_readonly"
    label = "siggo_readonly"
    verbose_name = "Siggo (solo lectura)"
