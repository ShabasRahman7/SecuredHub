# test settings - excludes daphne/channels to avoid Twisted/OpenSSL issue
from .settings import *

# remove daphne and channels to avoid OpenSSL compatibility issues during testing
INSTALLED_APPS = [app for app in INSTALLED_APPS if 'daphne' not in app.lower() and 'channels' not in app.lower()]

# use in-memory database for faster tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# use console email backend for tests
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# use simple hasher for faster tests
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
