from .base import *  # noqa

DEBUG = True

INSTALLED_APPS += ["django_extensions"]  # noqa

# En desarrollo permite cualquier origen
CORS_ALLOW_ALL_ORIGINS = True
