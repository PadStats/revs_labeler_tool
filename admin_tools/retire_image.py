#!/usr/bin/env python
"""Retire (remove) an image from the labeling pool.

Marks the image `status = removed`, clears assignment, and optionally deletes
its label document. Use when a file is corrupt or should never be labeled.

Usage:
    python -m admin_tools.retire_image IMG123 --yes            # mark removed
    python -m admin_tools.retire_image IMG123 --wipe --yes      # also delete label doc
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
import argparse

from dotenv import load_dotenv  # type: ignore
from google.cloud import firestore  # type: ignore
from google.oauth2 import service_account  # type: ignore

load_dotenv()


def _client() -> firestore.Client:  # type: ignore[valid-type]
    cred_blob = os.getenv("FIRESTORE_CREDENTIALS_JSON")
    project_id = os.getenv("GCP_PROJECT_ID")
    if not cred_blob:
        sa_path = os.getenv("SERVICE_ACCOUNT_JSON") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if sa_path and Path(sa_path).is_file():
            cred_blob = Path(sa_path).read_text(encoding="utf-8")
    if cred_blob:
        info: Any = json.loads(cred_blob)
        creds = service_account.Credentials.from_service_account_info(info)
        return firestore.Client(project=project_id, credentials=creds)
    return firestore.Client(project=project_id)


def main() -> None:
    parser = argparse.ArgumentParser("Retire or delete an image")
    parser.add_argument("image_id", help="Image ID to retire")
    parser.add_argument("--wipe", action="store_true", help="Also delete REVS_labels doc")
    parser.add_argument("--yes", action="store_true", help="Confirm action")
    args = parser.parse_args()

    if not args.yes:
        parser.error("Add --yes to confirm")

    db = _client()
    img_ref = db.collection("REVS_images").document(args.image_id)
    if not img_ref.get().exists:
        print("Image doc not found")
        return

    updates = {"status": "removed", "assigned_to": None, "task_expires_at": None}
    img_ref.update(updates)
    print("✓ image status set to 'removed'.")

    if args.wipe:
        db.collection("REVS_labels").document(args.image_id).delete()
        print("✓ label document deleted.")


if __name__ == "__main__":
    main() 