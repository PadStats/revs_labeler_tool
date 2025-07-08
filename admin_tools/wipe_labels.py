#!/usr/bin/env python
"""Delete label documents.

Dangerous! Requires explicit confirmation via --yes.

Usage:
    # single image
    python -m admin_tools.wipe_labels IMG123 --yes

    # wipe ALL labels (requires --all AND --yes)
    python -m admin_tools.wipe_labels --all --yes

    # wipe all labels by a specific user
    python -m admin_tools.wipe_labels --user USERNAME --yes

    # preview what would be deleted (dry run)
    python -m admin_tools.wipe_labels --user USERNAME
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
    parser = argparse.ArgumentParser("Wipe labels")
    parser.add_argument("image_id", nargs="?", help="Image ID to wipe")
    parser.add_argument("--all", action="store_true", help="Wipe ALL labels (danger)")
    parser.add_argument("--user", help="Wipe all labels by specific user")
    parser.add_argument("--yes", action="store_true", help="Confirm action")
    args = parser.parse_args()

    if not args.image_id and not args.all and not args.user:
        parser.error("provide IMAGE_ID, --all, or --user")
    if not args.yes:
        parser.error("--yes flag required to proceed")

    db = _client()
    labels = db.collection("REVS_labels")
    images = db.collection("REVS_images")

    if args.user:
        # Query for all labels created by this user
        query = labels.where("labeled_by", "==", args.user)
        docs = list(query.stream())
        
        if not docs:
            print(f"No labels found for user '{args.user}'")
            return

        print(f"Found {len(docs)} labels created by user '{args.user}':")
        for doc in docs:
            d = doc.to_dict() or {}
            spatial_labels = d.get("spatial_labels", [])
            location = spatial_labels[0] if spatial_labels else "Unknown"
            print(f"  {doc.id} - {location}")

        if not args.yes:
            print(f"\nTo actually delete these {len(docs)} labels, run:")
            print(f"python -m admin_tools.wipe_labels --user {args.user} --yes")
            return

        print(f"\nDeleting {len(docs)} label documents...")

        batch = db.batch()
        for doc in docs:
            # also delete revision sub-documents (if any)
            for rev in doc.reference.collection("revisions").list_documents():
                batch.delete(rev)
            batch.delete(doc.reference)
            # Reset image status & QA fields if the image exists
            batch.update(
                images.document(doc.id),
                {
                    "status": "unlabeled",
                    "flagged": False,
                    "qa_status": "pending",
                    "qa_feedback": firestore.DELETE_FIELD,
                    "assigned_to": None,
                    "review_requested_by": firestore.DELETE_FIELD,
                    "timestamp_review_requested": firestore.DELETE_FIELD,
                    "confirmed_by": firestore.DELETE_FIELD,
                    "timestamp_confirmed": firestore.DELETE_FIELD,
                },
            )
        
        batch.commit()
        print("✓ Labels wiped successfully")
        return

    # Original functionality for image_id or --all
    if args.image_id:
        targets = [args.image_id]
    else:
        docs = labels.list_documents()
        targets = [d.id for d in docs]

    if not targets:
        print("No label docs found.")
        return

    print(f"About to delete {len(targets)} label documents …")

    batch = db.batch()
    for img_id in targets:
        label_ref = labels.document(img_id)
        # delete revisions subcollection docs first
        for rev in label_ref.collection("revisions").list_documents():
            batch.delete(rev)
        batch.delete(label_ref)
        # reset image status & QA fields if exists
        batch.update(
            images.document(img_id),
            {
                "status": "unlabeled",
                "flagged": False,
                "qa_status": "pending",
                "qa_feedback": firestore.DELETE_FIELD,
                "assigned_to": None,
                "review_requested_by": firestore.DELETE_FIELD,
                "timestamp_review_requested": firestore.DELETE_FIELD,
                "confirmed_by": firestore.DELETE_FIELD,
                "timestamp_confirmed": firestore.DELETE_FIELD,
            },
        )
    batch.commit()
    print("✓ wipe complete")


if __name__ == "__main__":
    main() 