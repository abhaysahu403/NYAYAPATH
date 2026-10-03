from .base import *  # noqa: F401,F403
from . import base

DEBUG = False
SECRET_KEY = "test-secret-key-not-for-production"
ALLOWED_HOSTS = ["*"]
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "nyayapath-tests"}}
AI_PROVIDER = "mock"  # tests never call a real LLM
PRIVATE_MEDIA_ROOT = base.BASE_DIR / "private_media_test"
STORAGE_BUCKET = None
REST_FRAMEWORK = {
    **base.REST_FRAMEWORK,
    "DEFAULT_THROTTLE_RATES": {k: "100000/hour" for k in base.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]},
}
LOGGING = {"version": 1, "disable_existing_loggers": True, "handlers": {"null": {"class": "logging.NullHandler"}},
           "root": {"handlers": ["null"], "level": "CRITICAL"}}
