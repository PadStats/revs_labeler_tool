"""Admin CLI for QA status management.

Usage examples:
    python -m admin_tools.qa_status confirm <image_id>
    python -m admin_tools.qa_status review  <image_id> --labeler bob --feedback "Wrong location"
    python -m admin_tools.qa_status reset   <image_id> --labeler bob
    python -m admin_tools.qa_status show    <image_id>
    python -m admin_tools.qa_status list    --status confirmed
    python -m admin_tools.qa_status list    --status review --labeler bob
    python -m admin_tools.qa_status list    --status pending --limit 20
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


def reset_to_pending(img_id: str, labeler: str, admin: str) -> None:
    """Reset image QA status to pending (clears all QA fields)."""
    _update_status(
        img_id,
        {
            "qa_status": "pending",
            "qa_feedback": firestore.DELETE_FIELD,
            "assigned_to": labeler,
            "review_requested_by": firestore.DELETE_FIELD,
            "timestamp_review_requested": firestore.DELETE_FIELD,
            "confirmed_by": firestore.DELETE_FIELD,
            "timestamp_confirmed": firestore.DELETE_FIELD,
        },
    )
    print(f"{img_id}: qa_status -> pending (all QA fields cleared, assigned to {labeler})")


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


def list_by_status(qa_status: str, labeler: Optional[str] = None, limit: int = 50) -> None:
    """List images by QA status, optionally filtered by labeler."""
    db: firestore.Client = _fs_client()  # type: ignore[valid-type]
    
    # Build query
    query = db.collection("REVS_images").where("qa_status", "==", qa_status)
    
    # Add labeler filter if specified
    if labeler:
        if qa_status == "pending":
            # For pending images, filter by assigned_to (current labeler)
            query = query.where("assigned_to", "==", labeler)
        elif qa_status == "review":
            # For review images, filter by assigned_to (labeler who needs to fix)
            query = query.where("assigned_to", "==", labeler)
        elif qa_status == "confirmed":
            # For confirmed images, we need to check labels collection to find who labeled it
            # This is more complex, so we'll fetch all confirmed and filter client-side
            pass
    
    # Add limit and execute query
    query = query.limit(limit)
    docs = list(query.stream())
    
    # For confirmed status with labeler filter, we need to cross-reference with labels
    if qa_status == "confirmed" and labeler:
        print(f"Filtering confirmed images by labeler '{labeler}' (checking labels collection)...")
        filtered_docs = []
        labels_col = db.collection("REVS_labels")
        
        for doc in docs:
            # Check if this image was labeled by the specified user
            label_snap = labels_col.document(doc.id).get()
            if label_snap.exists:
                label_data = label_snap.to_dict() or {}
                if label_data.get("labeled_by") == labeler:
                    filtered_docs.append(doc)
        docs = filtered_docs
    
    if not docs:
        filter_msg = f" for labeler '{labeler}'" if labeler else ""
        print(f"No images found with qa_status='{qa_status}'{filter_msg}")
        return
    
    # Display results
    filter_msg = f" (labeler: {labeler})" if labeler else ""
    print(f"Found {len(docs)} images with qa_status='{qa_status}'{filter_msg}:\n")
    
    # Show relevant fields based on status
    for doc in docs:
        data = doc.to_dict() or {}
        image_id = doc.id
        status = data.get("status", "unknown")
        assigned_to = data.get("assigned_to", "none")
        
        if qa_status == "confirmed":
            confirmed_by = data.get("confirmed_by", "unknown")
            timestamp = data.get("timestamp_confirmed", "unknown")
            print(f"{image_id}  status={status}  confirmed_by={confirmed_by}  timestamp={timestamp}")
        
        elif qa_status == "review":
            feedback = data.get("qa_feedback", "")
            requested_by = data.get("review_requested_by", "unknown")
            timestamp = data.get("timestamp_review_requested", "unknown")
            feedback_preview = feedback[:50] + "..." if len(feedback) > 50 else feedback
            print(f"{image_id}  assigned_to={assigned_to}  requested_by={requested_by}  feedback='{feedback_preview}'")
        
        elif qa_status == "pending":
            print(f"{image_id}  status={status}  assigned_to={assigned_to}")
        
        else:
            print(f"{image_id}  status={status}  assigned_to={assigned_to}  qa_status={qa_status}")

# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="QA status administration tool")
    
    sub = p.add_subparsers(dest="cmd", required=True)

    # confirm
    c = sub.add_parser("confirm", help="Mark image as confirmed")
    c.add_argument("image_id")
    c.add_argument("--admin", required=True, help="Username of the admin performing the action")

    # review
    r = sub.add_parser("review", help="Request revision for an image")
    r.add_argument("image_id")
    r.add_argument("--labeler", required=True, help="Original labeler username")
    r.add_argument("--admin", required=True, help="Username of the admin performing the action")
    r.add_argument("--feedback", default="", help="Optional feedback text")

    # reset (new command)
    reset = sub.add_parser("reset", help="Reset image QA status to pending")
    reset.add_argument("image_id")
    reset.add_argument("--labeler", required=True, help="Labeler to assign the image to")
    reset.add_argument("--admin", required=True, help="Username of the admin performing the action")

    # show
    s = sub.add_parser("show", help="Show image QA fields")
    s.add_argument("image_id")

    # list (new command)
    l = sub.add_parser("list", help="List images by QA status")
    l.add_argument("--status", required=True, choices=["pending", "review", "confirmed"], 
                   help="QA status to filter by")
    l.add_argument("--labeler", help="Filter by labeler username")
    l.add_argument("--limit", type=int, default=50, help="Maximum number of results")

    return p


def main(argv: Optional[list[str]] = None) -> None:  # pragma: no cover
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "confirm":
        confirm(args.image_id, args.admin)
    elif args.cmd == "review":
        review(args.image_id, args.labeler, args.admin, args.feedback)
    elif args.cmd == "reset":
        reset_to_pending(args.image_id, args.labeler, args.admin)
    elif args.cmd == "show":
        show(args.image_id)
    elif args.cmd == "list":
        list_by_status(args.status, args.labeler, args.limit)
    else:
        parser.error("Unknown command")


if __name__ == "__main__":  # pragma: no cover
    main() 