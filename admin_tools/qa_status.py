"""Admin CLI for QA status management.

Usage examples:
    python -m admin_tools.qa_status confirm <image_id>
    python -m admin_tools.qa_status review  <image_id> --labeler bob --feedback "Wrong location"
    python -m admin_tools.qa_status show    <image_id>
"""

from __future__ import annotations

import argparse
from typing import Optional

from google.cloud import firestore  # type: ignore
from auth import _fs_client  # reuse existing cached client

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def _update_status(img_id: str, updates: dict) -> None:
    db: firestore.Client = _fs_client()  # type: ignore[valid-type]
    db.collection("REVS_images").document(img_id).update(updates)


def confirm(img_id: str, admin: str) -> None:
    _update_status(
        img_id,
        {
            "qa_status": "confirmed",
            "qa_feedback": firestore.DELETE_FIELD,
            "confirmed_by": admin,
            "timestamp_confirmed": firestore.SERVER_TIMESTAMP,
            "assigned_to": None,
        },
    )
    print(f"{img_id}: qa_status -> confirmed")


def review(img_id: str, labeler: str, admin: str, feedback: str = "") -> None:
    _update_status(
        img_id,
        {
            "qa_status": "review",
            "qa_feedback": feedback,
            "assigned_to": labeler,
            "review_requested_by": admin,
            "timestamp_review_requested": firestore.SERVER_TIMESTAMP,
        },
    )
    print(f"{img_id}: qa_status -> review (feedback len={len(feedback)})")


def show(img_id: str) -> None:
    db: firestore.Client = _fs_client()  # type: ignore[valid-type]
    snap = db.collection("REVS_images").document(img_id).get()
    if not snap.exists:
        print("Document not found")
        return
    data = snap.to_dict() or {}
    print("--- REVS_images ---")
    for k in sorted(data.keys()):
        print(f"{k}: {data[k]}")

# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="QA status administration tool")
    p.add_argument("--admin", required=True, help="Username of the admin performing the action")
    sub = p.add_subparsers(dest="cmd", required=True)

    # confirm
    c = sub.add_parser("confirm", help="Mark image as confirmed")
    c.add_argument("image_id")

    # review
    r = sub.add_parser("review", help="Request revision for an image")
    r.add_argument("image_id")
    r.add_argument("--labeler", required=True, help="Original labeler username")
    r.add_argument("--feedback", default="", help="Optional feedback text")

    # show
    s = sub.add_parser("show", help="Show image QA fields")
    s.add_argument("image_id")

    return p


def main(argv: Optional[list[str]] = None) -> None:  # pragma: no cover
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "confirm":
        confirm(args.image_id, args.admin)
    elif args.cmd == "review":
        review(args.image_id, args.labeler, args.admin, args.feedback)
    elif args.cmd == "show":
        show(args.image_id)
    else:
        parser.error("Unknown command")


if __name__ == "__main__":  # pragma: no cover
    main() 