"""Recompute per-user counters with pagination and time-bounded streams.

Usage:
    python -m admin_tools.recount_counters                # all users
    python -m admin_tools.recount_counters qurat          # single user

Safer than fix_user_counters for large datasets: iterates labels in pages.
"""

from __future__ import annotations

import argparse
import time
from typing import Optional

from google.cloud import firestore  # type: ignore
from auth import _fs_client
import time


PAGE_SIZE = 500
USER_PAGE_SIZE = 100
STREAM_PAUSE_SECS = 0.2


def _recount_user(db: firestore.Client, uid: str) -> None:  # type: ignore[valid-type]
    labels = db.collection("REVS_labels")
    images = db.collection("REVS_images")

    confirmed = 0
    to_review = 0

    # Paginate by timestamp_created if available, else by document ID lexicographically
    # We order descending to match existing queries but pagination works either way.
    q = labels.where("labeled_by", "==", uid).order_by("timestamp_created", direction=firestore.Query.DESCENDING)  # type: ignore[attr-defined]

    last_doc: Optional[firestore.DocumentSnapshot] = None  # type: ignore[name-defined]

    while True:
        page = (q.start_after(last_doc) if last_doc else q).limit(PAGE_SIZE).stream()
        page_docs = list(page)
        if not page_docs:
            break

        for lbl_snap in page_docs:
            img_id = lbl_snap.id
            img_snap = images.document(img_id).get()
            if not img_snap.exists:
                continue
            qa = (img_snap.to_dict() or {}).get("qa_status")
            if qa == "confirmed":
                confirmed += 1
            elif qa in ("pending", "review"):
                to_review += 1

        last_doc = page_docs[-1]
        time.sleep(STREAM_PAUSE_SECS)  # brief pause to reduce RPC pressure

    processed = confirmed + to_review

    db.collection("REVS_users").document(uid).update(
        {
            "images_confirmed": confirmed,
            "images_to_review": to_review,
            "images_processed": processed,
        }
    )
    print(f"{uid:<15} ✔︎ confirmed={confirmed}  review={to_review}  processed={processed}")


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(description="Recount per-user counters (paginated)")
    parser.add_argument("user", nargs="?", help="Process only this user")
    args = parser.parse_args()

    db: firestore.Client = _fs_client()  # type: ignore[valid-type]

    if args.user:
        _recount_user(db, args.user)
    else:
        # Paginate users by document ID to avoid long-running streams
        users = db.collection("REVS_users")
        q = users.order_by("__name__")
        last_doc = None
        while True:
            page = (q.start_after(last_doc) if last_doc else q).limit(USER_PAGE_SIZE).stream()
            docs = list(page)
            if not docs:
                break
            for snap in docs:
                _recount_user(db, snap.id)
            last_doc = docs[-1]
            time.sleep(STREAM_PAUSE_SECS)


if __name__ == "__main__":  # pragma: no cover
    main()


