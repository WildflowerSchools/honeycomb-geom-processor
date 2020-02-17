import os

from dotenv import load_dotenv

load_dotenv()

HONEYCOMB_URI = os.getenv("HONEYCOMB_URI", "https://honeycomb.api.wildflower-tech.org/graphql")
HONEYCOMB_TOKEN_URI = os.getenv("HONEYCOMB_TOKEN_URI", "https://wildflowerschools.auth0.com/oauth/token")
HONEYCOMB_AUDIENCE = os.getenv("HONEYCOMB_AUDIENCE", "https://honeycomb.api.wildflowerschools.org")
HONEYCOMB_CLIENT_ID = os.getenv("HONEYCOMB_CLIENT_ID")
HONEYCOMB_CLIENT_SECRET = os.getenv("HONEYCOMB_CLIENT_SECRET")

PG_USER = os.getenv("PGUSER", "geom-processor-user")
PG_PASSWORD = os.getenv("PGPASSWORD", "iamaninsecurepassword")
PG_DATABASE = os.getenv("PGDATABASE", "geom-processor")
PG_PORT = os.getenv("PGPORT", "5432")
PG_HOST = os.getenv("PGHOST", "localhost")

MAX_WORKERS = int(os.getenv("MAX_WORKERS", 5))
