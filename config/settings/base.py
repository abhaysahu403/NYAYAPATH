"""Shared settings. Environment-specific modules import * from here."""
import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import unquote, urlparse

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


def env(name: str, default=None):
    return os.environ.get(name, default)


def env_bool(name: str, default: bool = False) -> bool:
    return str(os.environ.get(name, str(default))).strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def env_list(name: str, default: str = "") -> list:
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


# --------------------------------------------------------------------------- core
SECRET_KEY = env("SECRET_KEY", "")
DEBUG = False
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    # third party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
    # NyayaPath apps
    "core",
    "users",
    "courts",
    "sources",
    "cases",
    "judgments",
    "documents",
    "legal_research",
    "ai",
    "action_plans",
    "drafts",
    "audit",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "core.middleware.RequestContextMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]


# --------------------------------------------------------------------------- database
def _database_from_env() -> dict:
    """PostgreSQL only. Accepts DATABASE_URL or discrete DB_* variables."""
    url = env("DATABASE_URL")
    if url:
        parsed = urlparse(url)
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": parsed.path.lstrip("/"),
            "USER": unquote(parsed.username or ""),
            "PASSWORD": unquote(parsed.password or ""),
            "HOST": parsed.hostname or "localhost",
            "PORT": str(parsed.port or 5432),
        }
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", "nyayapath"),
        "USER": env("DB_USER", "postgres"),
        "PASSWORD": env("DB_PASSWORD", ""),
        "HOST": env("DB_HOST", "localhost"),
        "PORT": env("DB_PORT", "5432"),
    }


DATABASES = {"default": {**_database_from_env(), "CONN_MAX_AGE": env_int("DB_CONN_MAX_AGE", 60)}}

# --------------------------------------------------------------------------- cache
REDIS_URL = env("REDIS_URL")
if REDIS_URL:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": REDIS_URL}}
else:
    # NOTE: locmem is per-process; throttling/caching are only approximate with several workers.
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "nyayapath"}}

# --------------------------------------------------------------------------- auth
AUTH_USER_MODEL = "users.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
PASSWORD_RESET_TIMEOUT = env_int("PASSWORD_RESET_TIMEOUT_SECONDS", 3600)
FRONTEND_PASSWORD_RESET_URL = env(
    "FRONTEND_PASSWORD_RESET_URL", "http://localhost:3000/reset-password?uid={uid}&token={token}"
)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "NyayaPath <no-reply@nyayapath.local>")

# --------------------------------------------------------------------------- DRF
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["core.renderers.EnvelopeJSONRenderer"],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
    "DEFAULT_PAGINATION_CLASS": "core.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": env("THROTTLE_ANON", "120/hour"),
        "user": env("THROTTLE_USER", "2000/hour"),
        "auth": env("THROTTLE_AUTH", "20/hour"),
        "ai_chat": env("THROTTLE_AI_CHAT", "60/hour"),
        "ai_guest": env("THROTTLE_AI_GUEST", "10/hour"),
        "ai_documents": env("THROTTLE_AI_DOCUMENTS", "30/hour"),
        "judgment_search": env("THROTTLE_JUDGMENT_SEARCH", "120/hour"),
    },
    "EXCEPTION_HANDLER": "core.exceptions.api_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "NyayaPath API",
    "DESCRIPTION": "Legal information and case-navigation API. Not legal advice.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env_int("JWT_ACCESS_MINUTES", 60)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env_int("JWT_REFRESH_DAYS", 14)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# --------------------------------------------------------------------------- CORS
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:5500,http://localhost:5500")
CORS_ALLOW_ALL_ORIGINS = False
CORS_EXPOSE_HEADERS = ["X-Request-ID"]

# --------------------------------------------------------------------------- uploads / private storage
# Uploaded legal documents are NEVER under MEDIA_URL / static. They are served only through
# authenticated, ownership-checked API views (or expiring signed links).
PRIVATE_MEDIA_ROOT = Path(env("PRIVATE_MEDIA_ROOT", str(BASE_DIR / "private_media")))
MAX_UPLOAD_SIZE_MB = env_int("MAX_UPLOAD_SIZE_MB", 20)
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
ALLOWED_UPLOAD_EXTENSIONS = env_list("ALLOWED_UPLOAD_EXTENSIONS", "pdf,png,jpg,jpeg,docx")
DOCUMENT_PROCESSING_MODE = env("DOCUMENT_PROCESSING_MODE", "sync")  # sync | manual (a worker can replace sync later)
DOCUMENT_LINK_TTL_SECONDS = env_int("DOCUMENT_LINK_TTL_SECONDS", 300)
OCR_LANGUAGES = env("OCR_LANGUAGES", "hin+eng")

# Optional S3-compatible object storage (requires django-storages + boto3).
STORAGE_BUCKET = env("STORAGE_BUCKET")
STORAGE_ACCESS_KEY = env("STORAGE_ACCESS_KEY")
STORAGE_SECRET_KEY = env("STORAGE_SECRET_KEY")
STORAGE_ENDPOINT_URL = env("STORAGE_ENDPOINT_URL")
STORAGE_REGION = env("STORAGE_REGION")

# --------------------------------------------------------------------------- i18n
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------------------- AI
AI_PROVIDER = env("AI_PROVIDER", "mock")  # mock | gemini
GEMINI_API_KEY = env("GEMINI_API_KEY") or env("GOOGLE_API_KEY") or ""
GEMINI_MODEL = env("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_EMBEDDING_MODEL = env("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
EMBEDDING_DIM = env_int("EMBEDDING_DIM", 768)  # changing this requires a migration + re-embedding
AI_MAX_INPUT_CHARS = env_int("AI_MAX_INPUT_CHARS", 3000)
AI_MAX_PROMPT_CHARS = env_int("AI_MAX_PROMPT_CHARS", 24000)
AI_MAX_OUTPUT_TOKENS = env_int("AI_MAX_OUTPUT_TOKENS", 2048)
AI_TIMEOUT_SECONDS = env_int("AI_TIMEOUT_SECONDS", 60)
AI_CACHE_TTL_SECONDS = env_int("AI_CACHE_TTL_SECONDS", 3600)
RETRIEVAL_TOP_K = env_int("RETRIEVAL_TOP_K", 5)
RETRIEVAL_MAX_TOP_K = env_int("RETRIEVAL_MAX_TOP_K", 10)
RETRIEVAL_PASSAGE_CHARS = env_int("RETRIEVAL_PASSAGE_CHARS", 1200)
DOCUMENT_ANALYSIS_MAX_CHARS = env_int("DOCUMENT_ANALYSIS_MAX_CHARS", 12000)

# --------------------------------------------------------------------------- logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"request_context": {"()": "core.logging.RequestContextFilter"}},
    "formatters": {"json": {"()": "core.logging.JsonFormatter"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json", "filters": ["request_context"]}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", "INFO")},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
    },
}
