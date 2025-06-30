from __future__ import annotations

"""Lightweight helpers for username / password authentication.

This module is **server-side only** – it never transmits password hashes to the
browser.  It purposely re-implements the same credential selection logic used
in `labeler_backend.factory._make_firestore_client`, so it works both:
  • locally, when FIRESTORE_CREDENTIALS_JSON is supplied in .env, and
  • on Cloud Run / GKE, where Application-Default-Credentials are available via
    the service account attached to the revision.
"""

import json
import os
from functools import lru_cache
from typing import Any
from pathlib import Path
from dotenv import load_dotenv  # type: ignore

import bcrypt  # type: ignore
from google.cloud import firestore  # type: ignore
from google.oauth2 import service_account  # type: ignore

__all__ = [
    "get_user_doc",
    "hash_pw",
    "verify_pw",
]

# ---------------------------------------------------------------------------
# Load .env if present (no-op if file missing). This is safe because
# Streamlit already calls `load_dotenv` once, but importing here keeps the
# behaviour consistent when this module is used by standalone scripts.
# ---------------------------------------------------------------------------

load_dotenv()

# ---------------------------------------------------------------------------
# Firestore client – cached so we reuse sockets across Streamlit reruns
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _fs_client() -> firestore.Client:  # type: ignore[valid-type]
    """Return an authenticated Firestore client.

    If FIRESTORE_CREDENTIALS_JSON is provided we build explicit service-account
    credentials.  Otherwise we fall back to Application Default Credentials
    (ADC), which is the recommended approach on Cloud Run.
    """

    cred_blob = os.getenv("FIRESTORE_CREDENTIALS_JSON")
    project_id = os.getenv("GCP_PROJECT_ID")  # optional – ADC usually infers it

    # Support an alternative style where the key is stored *as a file* and the
    # path is supplied via SERVICE_ACCOUNT_JSON (our own convention) or the
    # standard GOOGLE_APPLICATION_CREDENTIALS.
    if not cred_blob:
        sa_path = os.getenv("SERVICE_ACCOUNT_JSON") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if sa_path and Path(sa_path).is_file():
            cred_blob = Path(sa_path).read_text(encoding="utf-8")

    if cred_blob:
        creds_info: Any = json.loads(cred_blob)
        creds = service_account.Credentials.from_service_account_info(creds_info)
        return firestore.Client(project=project_id, credentials=creds)

    # No explicit credentials supplied – rely on ADC (e.g. Cloud Run SA)
    return firestore.Client(project=project_id)


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def get_user_doc(username: str) -> firestore.DocumentSnapshot:  # type: ignore[valid-type]
    """Return the Firestore document snapshot for *username* (no writes)."""
    return _fs_client().collection("REVS_users").document(username).get()


def hash_pw(raw_password: str) -> str:
    """Return a bcrypt hash for *raw_password* (UTF-8)."""
    return bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()


def verify_pw(raw_password: str, stored_hash: str) -> bool:
    """Check *raw_password* against *stored_hash* (bcrypt).

    Returns ``True`` on match.
    """
    if not raw_password or not stored_hash:
        return False
    try:
        return bcrypt.checkpw(raw_password.encode(), stored_hash.encode())
    except ValueError:
        # stored_hash is not a valid bcrypt hash
        return False 