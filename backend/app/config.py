"""Central configuration. Secrets come from environment variables / .env, never from source code."""
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _load_secret_key() -> str:
    """Use SECRET_KEY from the environment; otherwise generate one once and persist it
    in backend/.secret_key (git-ignored) so tokens survive restarts."""
    env_key = os.getenv("SECRET_KEY")
    if env_key:
        return env_key
    key_file = BASE_DIR / ".secret_key"
    if key_file.exists():
        return key_file.read_text().strip()
    key = secrets.token_urlsafe(48)
    key_file.write_text(key)
    return key


SECRET_KEY = _load_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(BASE_DIR / 'voting.db').as_posix()}")
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if o.strip()
]
# PDF lets any user create proposals; set to "false" to restrict creation to ADMIN.
ALLOW_USER_PROPOSALS = os.getenv("ALLOW_USER_PROPOSALS", "true").lower() == "true"
DEFAULT_PROPOSAL_DAYS = 2
