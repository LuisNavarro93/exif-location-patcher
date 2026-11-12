"""Django settings for the EXIF location patcher.

A small, single-user local tool: start the dev server, pick a folder of
pictures/videos, see where each was taken on a map, and write a new GPS
location into the files. See CHANGELOG.md for release history and
patcher/__init__.py for the current __version__.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "dev-only-secret-key-change-me-before-any-real-deployment",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() == "true"

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "patcher",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "epl_config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "epl_config.wsgi.application"

# The app keeps no records of its own, so no database is configured.
DATABASES = {}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = False
USE_TZ = True

# OpenStreetMap blocks tile requests that carry no Referer header, and
# Django's default "same-origin" policy strips it from cross-site requests.
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Where generated thumbnails are cached (keyed by file path + mtime). Kept
# in the user's cache folder so it also works when installed as a package.
OBJ_PATCHER_THUMBNAIL_CACHE_DIR = Path(
    os.environ.get(
        "PATCHER_THUMBNAIL_CACHE_DIR",
        Path.home() / ".cache" / "exif-location-patcher" / "thumbnails",
    )
)

# Thumbnail longest side, in pixels.
INT_PATCHER_THUMBNAIL_SIZE_PX = int(os.environ.get("PATCHER_THUMBNAIL_SIZE_PX", "320"))

# Folder the landing page's folder browser opens at.
OBJ_PATCHER_START_DIR = Path(os.environ.get("PATCHER_START_DIR", Path.home()))
