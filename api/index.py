from app import app


# Vercel Python runtime expects an application object exported from the
# serverless entrypoint.
handler = app
