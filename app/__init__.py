"""Load a local .env before anything reads the environment (no-op in prod)."""

from dotenv import load_dotenv

load_dotenv()
