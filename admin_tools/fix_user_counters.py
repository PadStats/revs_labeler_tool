#!/usr/bin/env python
"""Re-sync per-user image counters (confirmed / to-review / processed).

Run once after bulk resets or any operation that may have desynchronised the
counters.  Uses Firestore aggregate `count()` queries when available, falling
back to naive iteration otherwise.

Examples:
    python -m admin_tools.fix_user_counters       # process *all* users
    python -m admin_tools.fix_user_counters bob   # just one user
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

# Optional – load .env if python-dotenv is present
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except ModuleNotFoundError:
    load_dotenv = lambda *_, **__: None  # type: ignore

# ensure env vars are at least attempted
load_dotenv()

from google.cloud import firestore  # type: ignore
from google.oauth2 import service_account  # type: ignore


# ---------------------------------------------------------------------------
# Firestore helper (copied from other admin tools)
# ---------------------------------------------------------------------------

def _client() -> firestore.Client:  # type: ignore[valid-type]
    cred_blob = os.getenv("FIRESTORE_CREDENTIALS_JSON")
    project_id = os.getenv("GCP_PROJECT_ID")

    if not cred_blob:
        sa_path = os.getenv("SERVICE_ACCOUNT_JSON") or os.getenv(
            "GOOGLE_APPLICATION_CREDENTIALS"
        )
        if sa_path and Path(sa_path).is_file():
            cred_blob = Path(sa_path).read_text(encoding="utf-8")

    if cred_blob:
        info: Any = json.loads(cred_blob)
        creds = service_account.Credentials.from_service_account_info(info)
        return firestore.Client(project=project_id, credentials=creds)

    return firestore.Client(project=project_id)


def _count_images(q):  # helper that tries aggregate count first
    try:
        return q.count().get()[0].value  # type: ignore[attr-defined]
    except AttributeError:
        # SDK < 2.11 without AggregateQuery
        return sum(1 for _ in q.stream())


def _process_user(db: firestore.Client, uid: str):  # type: ignore[valid-type]
    labels_col = db.collection("REVS_labels")
    images_col = db.collection("REVS_images")

    confirmed = 0
    to_review = 0

    for lbl_snap in labels_col.where("labeled_by", "==", uid).stream():
        img_id = lbl_snap.id
        img_snap = images_col.document(img_id).get()
        if not img_snap.exists:
            continue
        qa = (img_snap.to_dict() or {}).get("qa_status")
        if qa == "confirmed":
            confirmed += 1
        elif qa in ("pending", "review"):
            to_review += 1

    processed = confirmed + to_review

    db.collection("REVS_users").document(uid).update(
        {
            "images_confirmed": confirmed,
            "images_to_review": to_review,
            "images_processed": processed,
            "total_images_labeled": firestore.DELETE_FIELD,
        }
    )
    print(f"{uid:<15} ✔︎ confirmed={confirmed}  review={to_review}  processed={processed}")


def main():
    parser = argparse.ArgumentParser("Fix user counters")
    parser.add_argument("user", nargs="?", help="Process only this user")
    args = parser.parse_args()

    db = _client()

    if args.user:
        _process_user(db, args.user)
    else:
        for snap in db.collection("REVS_users").stream():
            _process_user(db, snap.id)


if __name__ == "__main__":
    main() 