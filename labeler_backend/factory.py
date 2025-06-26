from __future__ import annotations

import json
import os
from typing import Any

# NOTE: we *lazy-import* google cloud libs so that running in dev mode doesn't
# require the heavy dependency.

from .bb_resolver import resolve_bb_path
from .dev_repo import DevRepo
from .base import LabelRepo

# FireRepo will be imported lazily so Phase-1 can compile before we write it.


def _make_firestore_client():  # type: ignore
    """Return an authenticated Firestore client using either ADC or a blob in env."""

    # Local import keeps the dependency optional when dev mode is used.
    from google.cloud import firestore  # type: ignore
    from google.oauth2 import service_account  # type: ignore

    cred_blob = os.getenv("FIRESTORE_CREDENTIALS_JSON")
    project_id = os.getenv("GCP_PROJECT_ID")  # optional – falls back to creds
    if cred_blob:
        creds_info: Any = json.loads(cred_blob)
        creds = service_account.Credentials.from_service_account_info(creds_info)
        return firestore.Client(project=project_id, credentials=creds)

    # Fallback to Application Default Credentials (e.g., GOOGLE_APPLICATION_CREDENTIALS path).
    return firestore.Client(project=project_id)


def get_repo(mode: str = "dev", **kwargs) -> LabelRepo:  # noqa: ANN001
    """Factory returning a concrete LabelRepo.

    *mode* can be:
      • "dev" – local CSV or mock (pass kind="mock" in kwargs)
      • "firestore" – production Firestore back-end
    """

    mode = mode.lower()
    if mode == "dev":
        return DevRepo(kwargs.get("kind", "csv"))

    if mode == "firestore":
        # Lazy import to avoid heavy deps when running dev mode.
        from .fire_repo import FirestoreRepo  # noqa: WPS433

        client = _make_firestore_client()
        resolver = kwargs.get("resolver", resolve_bb_path)
        return FirestoreRepo(client, resolver)

    raise ValueError(f"Unknown repo mode {mode}") 