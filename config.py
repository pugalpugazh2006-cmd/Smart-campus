import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-me'

    DATABASE_URL = os.environ.get('DATABASE_URL')
    VERCEL = os.environ.get('VERCEL') == '1'

    # SQLAlchemy Configuration
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///smartcampus.db'

    # Fix legacy postgres:// URLs
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PREFERRED_URL_SCHEME = 'https' if VERCEL else 'http'
    SESSION_COOKIE_SECURE = VERCEL

    # TinyDB fallback (legacy diagnostic tooling only)
    DB_FILE = 'db.json'

    # Vercel serverless instances do not have persistent local storage.
    # Force hosted deployments onto an external database instead of silently
    # creating a throwaway SQLite file per cold start.
    if VERCEL and not DATABASE_URL:
        raise RuntimeError('DATABASE_URL must be set for Vercel deployments.')
