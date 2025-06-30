#!/usr/bin/env python
"""Quick admin utility: list users or inspect a single user's recent work.

Examples:
    # list all users with counters
    python -m admin_tools.user_stats

    # detailed view for one user
    python -m admin_tools.user_stats alice --history 20
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, List, Dict
import argparse
from datetime import datetime

from dotenv import load_dotenv  # type: ignore
from google.cloud import firestore  # type: ignore
from google.oauth2 import service_account  # type: ignore
from google.api_core.exceptions import FailedPrecondition  # type: ignore

load_dotenv()


# ---------------------------------------------------------------------------
# Firestore helper (shared with provision_user)
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


def _human_ts(ts):  # type: ignore
    if ts is None:
        return "–"
    if isinstance(ts, datetime):
        return ts.isoformat(sep=" ", timespec="seconds")
    return str(ts)


def list_users(db: firestore.Client):  # type: ignore[valid-type]
    users_ref = db.collection("REVS_users")
    docs = users_ref.stream()
    rows: List[Dict[str, Any]] = []
    for doc in docs:
        d = doc.to_dict() or {}
        rows.append(
            {
                "user": doc.id,
                "enabled": d.get("enabled", True),
                "role": d.get("role", "?"),
                "labeled": d.get("total_images_labeled", 0),
                "last": _human_ts(d.get("timestamp_last_labeled")),
            }
        )
    print(f"{'User':<15} {'Role':<10} {'Enabled':<7} {'Labeled':<7} Last labeled")
    print("-" * 60)
    for r in sorted(rows, key=lambda x: (-x["enabled"], x["user"])):
        print(
            f"{r['user']:<15} {r['role']:<10} {str(r['enabled']):<7} {r['labeled']:<7} {r['last']}"
        )


def show_history(db: firestore.Client, user: str, limit: int):  # type: ignore[valid-type]
    labels = db.collection("REVS_labels")
    q = (
        labels.where("labeled_by", "==", user)
        .order_by("timestamp_created", direction=firestore.Query.DESCENDING)
        .limit(limit)
    )
    print(f"Last {limit} images labeled by {user}:")
    try:
        for doc in q.stream():
            d = doc.to_dict() or {}
            ts = _human_ts(d.get("timestamp_created"))
            loc = ", ".join(d.get("spatial_labels", [])[:1])
            print(f"  {doc.id}  {ts}  {loc}")
    except FailedPrecondition as exc:
        # Firestore requires a composite index (labeled_by + timestamp_created)
        msg = str(exc)
        if "create it here" in msg:
            url_start = msg.find("https://")
            url = msg[url_start:].split()[0] if url_start != -1 else ""
            print("Firestore needs a composite index for (labeled_by, timestamp_created).\n")
            if url:
                print(f"Create it via console: {url}\n")
        else:
            raise


def main() -> None:
    parser = argparse.ArgumentParser("User statistics & history")
    parser.add_argument("user", nargs="?", help="Username to inspect (omit for table)")
    parser.add_argument("--history", type=int, default=10, help="History length when --user is given")
    args = parser.parse_args()

    db = _client()
    if args.user:
        show_history(db, args.user, args.history)
    else:
        list_users(db)


if __name__ == "__main__":
    main() 