from .base import *  # noqa: F401,F403
from .base import env, env_bool, env_list

DEBUG = env_bool("DEBUG", True)
SECRET_KEY = env("SECRET_KEY") or "dev-only-insecure-key-do-not-use-in-production"
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]")
CORS_ALLOW_ALL_ORIGINS = env_bool("CORS_ALLOW_ALL_ORIGINS", True)  # dev convenience only
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Render injects the service hostname; allow it without manual config.
import os  # noqa: E402
_render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if _render_host and _render_host not in ALLOWED_HOSTS and "*" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS = [*ALLOWED_HOSTS, _render_host]
if _render_host and "DEBUG" not in os.environ:
    DEBUG = False
