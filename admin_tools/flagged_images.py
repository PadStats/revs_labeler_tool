#!/usr/bin/env python
"""List flagged images for QA follow-up.

Examples:
    python -m admin_tools.flagged_images           # all flagged
    python -m admin_tools.flagged_images --user alice
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
    parser = argparse.ArgumentParser("List / unflag images marked as 'flagged'")
    parser.add_argument("--user", help="Filter by labeled_by user", default=None)
    parser.add_argument("--limit", type=int, default=50, help="Max docs to show")
    parser.add_argument("--unflag", action="store_true", help="Remove flag field from the listed images")
    parser.add_argument("--execute", action="store_true", help="Actually perform --unflag (otherwise dry-run)")
    args = parser.parse_args()

    db = _client()

    images = db.collection("REVS_images").where("flagged", "==", True)
    if args.user:
        images = images.where("assigned_to", "==", args.user)
    images = images.limit(args.limit)

    docs = list(images.stream())
    if not docs:
        print("No flagged images found.")
        return

    print(f"Found {len(docs)} flagged images:\n")
    for d in docs:
        data = d.to_dict() or {}
        print(f"{d.id}  status={data.get('status')}  assigned_to={data.get('assigned_to')}  flagged={data.get('flagged')}")

    if args.unflag:
        if not args.execute:
            print("\n-- Dry-run (--unflag requested). Use --execute to apply changes.")
            return
        batch = db.batch()
        for d in docs:
            batch.update(d.reference, {"flagged": False})
        batch.commit()
        print(f"\n✓ Cleared flag on {len(docs)} image(s).")


if __name__ == "__main__":
    main() 