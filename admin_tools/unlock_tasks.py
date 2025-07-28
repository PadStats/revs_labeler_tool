# 14" screen

#!/usr/bin/env python
"""Unlock tasks stuck in `in_progress` state.

Default behaviour: show a table of *all* images whose `status == "in_progress"`.
Each row shows the user holding the lock and the `task_expires_at` timestamp –
the moment after which Cloud-Scheduler or a manual unlock may reclaim it.

`--stale` means *task_expires_at < now()* (i.e. the lock window has already
elapsed).

To actually unlock:
    python -m admin_tools.unlock_tasks --execute            # unlock *all*
    python -m admin_tools.unlock_tasks --stale --execute    # only stale
    python -m admin_tools.unlock_tasks IMG123 --execute     # specific image
    
    # See everything Bob currently has locked
    python -m admin_tools.unlock_tasks --user bob

Flags:
  --stale    Only unlock tasks whose `task_expires_at` is earlier than now.
  --execute  Perform the update; otherwise the script is read-only.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Dict
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


def _human(ts):
    if ts is None:
        return "–"
    if hasattr(ts, 'isoformat'):
        return ts.isoformat(sep=" ", timespec="seconds")
    return str(ts)


def main() -> None:
    parser = argparse.ArgumentParser("Unlock in-progress tasks")
    parser.add_argument("image_id", nargs="?", help="Specific image to unlock")
    parser.add_argument("--user", help="Unlock tasks assigned to this user", default=None)
    parser.add_argument("--stale", action="store_true", help="Only unlock tasks past expiry")
    parser.add_argument("--execute", action="store_true", help="Actually perform the unlock – otherwise dry-run")
    args = parser.parse_args()

    db = _client()
    images = db.collection("REVS_images")

    now = datetime.utcnow().replace(tzinfo=timezone.utc)

    docs: List[Any] = []
    if args.image_id:
        snap = images.document(args.image_id).get()
        if snap.exists:
            docs = [snap]
        else:
            print("Image not found")
            return
    else:
        q = images.where("status", "==", "in_progress")
        if args.user:
            q = q.where("assigned_to", "==", args.user)
        if args.stale:
            q = q.where("task_expires_at", "<", now)
        docs = list(q.stream())

    if not docs:
        print("No tasks matched criteria.")
        return

    print(f"{'Image':<20} {'User':<15} Expires")
    print("-" * 50)
    for d in docs:
        data = d.to_dict() or {}
        print(f"{d.id:<20} {data.get('assigned_to', ''):<15} {_human(data.get('task_expires_at'))}")

    if not args.execute:
        print("\n-- Dry-run complete. Use --execute to unlock.")
        return

    # Collect affected users to clear their property assignments
    affected_users = set()
    for d in docs:
        data = d.to_dict() or {}
        user_id = data.get("assigned_to")
        if user_id:
            affected_users.add(user_id)

    batch = db.batch()
    
    # Update image documents
    for d in docs:
        ref = d.reference
        batch.update(
            ref,
            {
                "status": "unlabeled",
                "assigned_to": None,
                "timestamp_assigned": None,  # Clear assignment timestamp when unlocking
                "task_expires_at": None,
                "qa_status": "pending",
                "qa_feedback": firestore.DELETE_FIELD,
                "review_requested_by": firestore.DELETE_FIELD,
                "timestamp_review_requested": firestore.DELETE_FIELD,
                "confirmed_by": firestore.DELETE_FIELD,
                "timestamp_confirmed": firestore.DELETE_FIELD,
            },
        )
    
    # Clear property assignments for affected users
    users = db.collection("REVS_users")
    for user_id in affected_users:
        user_ref = users.document(user_id)
        batch.update(user_ref, {"current_property_id": None})
    
    batch.commit()
    print(f"\n✓ Unlocked {len(docs)} task(s) and cleared property assignments for {len(affected_users)} user(s).")


if __name__ == "__main__":
    main() 