import os

from dotenv import load_dotenv

load_dotenv()

class Config:
    ENV = os.environ.get('FLASK_ENV', 'production')
    SECRET_KEY = (
        os.environ.get('SECRET_KEY')
        or os.environ.get('smart_campus_SECRET_KEY')
        or 'dev-secret-key-change-me'
    )

    DATABASE_URL = (
        os.environ.get('DATABASE_URL')
        or os.environ.get('smart_campus_DATABASE_URL')
        or os.environ.get('smart_campus_POSTGRES_URL')
    )
    VERCEL = os.environ.get('VERCEL') == '1'
    IS_PRODUCTION = ENV == 'production' or VERCEL

    # SQLAlchemy Configuration
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///smartcampus.db'

    # Fix legacy postgres:// URLs
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}
    PREFERRED_URL_SCHEME = 'https' if IS_PRODUCTION else 'http'
    SESSION_COOKIE_SECURE = IS_PRODUCTION
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_HTTPONLY = True
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024

    # TinyDB fallback (legacy diagnostic tooling only)
    DB_FILE = 'db.json'

    # Vercel serverless instances do not have persistent local storage.
    # Force hosted deployments onto an external database instead of silently
    # creating a throwaway SQLite file per cold start.
    if VERCEL and not DATABASE_URL:
        raise RuntimeError('DATABASE_URL must be set for Vercel deployments.')
