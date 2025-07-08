from __future__ import annotations

from datetime import timedelta, datetime
from typing import Dict, Optional
from random import random
import time

from google.cloud import firestore  # type: ignore
from google.api_core.exceptions import Aborted  # type: ignore

from .base import LabelRepo
from .bb_resolver import BackblazeResolverError

_LOCK_WINDOW_MINUTES = int(
    __import__("os").getenv("TASK_LOCK_MINUTES", "60")
)


class FirestoreRepo(LabelRepo):
    """Production Firestore backend implementation."""

    def __init__(self, client: firestore.Client, resolver):  # type: ignore[valid-type]
        self.db = client
        self._resolve = resolver
        # collections as per agreed names
        self.images = self.db.collection("REVS_images")
        self.labels = self.db.collection("REVS_labels")
        self.users = self.db.collection("REVS_users")

    # ------------------------------------------------------------------
    # Task management
    # ------------------------------------------------------------------
    def get_next_task(self, user_id: str) -> Optional[Dict]:
        """Return existing in-progress doc for *user_id*, or lock a new one.

        Enhancement: if the user has images flagged for review (qa_status=='review')
        those are prioritised *before* any normal task selection.  Confirmed images
        (qa_status=='confirmed') are never surfaced to labelers.
        """

        @firestore.transactional
        def _txn(txn):  # type: ignore[valid-type]
            # 0) priority – tasks sent back for revision ----------------------
            review_q = (
                self.images
                .where("qa_status", "==", "review")
                .where("assigned_to", "==", user_id)
                .limit(1)
            )
            docs = list(review_q.stream(transaction=txn))
            if docs:
                doc = docs[0]
                expires_at = datetime.utcnow() + timedelta(minutes=_LOCK_WINDOW_MINUTES)
                txn.update(
                    doc.reference,
                    {
                        "status": "in_progress",
                        "timestamp_assigned": firestore.SERVER_TIMESTAMP,
                        "task_expires_at": expires_at,
                    },
                )
                data = doc.to_dict()
                data.update({"status": "in_progress"})
                return data

            # 1) resume ------------------------------------------------------
            resume_q = (
                self.images.where("status", "==", "in_progress")
                .where("assigned_to", "==", user_id)
                .limit(1)
            )
            docs = list(resume_q.stream(transaction=txn))
            if docs:
                return docs[0].to_dict()

            # 2) acquire new (exclude confirmed) -----------------------------
            new_q = (
                self.images.where("status", "==", "unlabeled")
                .where("qa_status", "==", "pending")  # confirmed images are not pending
                .order_by("timestamp_uploaded")
                .limit(1)
            )
            docs = list(new_q.stream(transaction=txn))
            if not docs:
                return None
            doc = docs[0]
            expires_at = datetime.utcnow() + timedelta(minutes=_LOCK_WINDOW_MINUTES)
            txn.update(
                doc.reference,
                {
                    "status": "in_progress",
                    "assigned_to": user_id,
                    "timestamp_assigned": firestore.SERVER_TIMESTAMP,
                    "task_expires_at": expires_at,
                },
            )
            data = doc.to_dict()
            data.update({"status": "in_progress", "assigned_to": user_id})
            return data

        for attempt in range(5):
            try:
                return _txn(self.db.transaction())
            except Aborted:
                # exponential back-off with jitter
                time.sleep((2 ** attempt) * 0.1 * (1 + random()))
                continue
        # all attempts failed
        raise RuntimeError("Unable to acquire task due to repeated transaction aborts")

    def release_task(self, image_id: str, user_id: str, *, abandon: bool = False) -> None:  # noqa: D401
        if abandon:
            # Return task to the pool so that any user can pick it up again.
            self.images.document(image_id).update(
                {
                    "status": "unlabeled",
                    "assigned_to": None,
                    "task_expires_at": None,
                }
            )
        # else: keep lock intact (no-op)

    # ------------------------------------------------------------------
    # Labels I/O
    # ------------------------------------------------------------------
    def load_labels(self, image_id: str) -> Optional[Dict]:
        snap = self.labels.document(image_id).get()
        return snap.to_dict() if snap.exists else None

    def save_labels(self, image_id: str, payload: Dict, user_id: str) -> None:  # noqa: D401
        """Persist labels & mark task done.

        Added safety: labelers cannot overwrite images that have already been
        confirmed by QA (qa_status == 'confirmed').  When a labeler resubmits
        an image sent back for revision we reset qa_status to 'pending' and
        clear any previous qa_feedback.
        """
        @firestore.transactional
        def _txn(txn):  # type: ignore[valid-type]
            # Freeze check -------------------------------------------------------
            img_ref = self.images.document(image_id)
            img_snap = img_ref.get(transaction=txn)
            img_data = img_snap.to_dict() if img_snap.exists else {}
            is_confirmed = img_data.get("qa_status") == "confirmed"

            # Determine if caller is admin (role look-up is cheap and cached)
            user_snap = self.users.document(user_id).get(transaction=txn)
            is_admin_user = user_snap.exists and user_snap.to_dict().get("role") == "admin"

            if is_confirmed and not is_admin_user:
                raise PermissionError("Image has been confirmed by QA and can no longer be edited by labelers.")

            # 1) write/merge labels (original logic) ---------------------------
            labels_ref = self.labels.document(image_id)
            snap = labels_ref.get(transaction=txn)
            now = firestore.SERVER_TIMESTAMP

            to_write = {**payload, "updated_at": now}
            if not snap.exists:
                to_write["timestamp_created"] = now
            else:
                # store previous revision before overwriting
                prev_payload = snap.to_dict()
                rev_ref = labels_ref.collection("revisions").document()
                txn.set(
                    rev_ref,
                    {
                        "payload": prev_payload,
                        "edited_by": user_id,
                        "edited_at": now,
                    },
                )

            txn.set(labels_ref, to_write, merge=True)

            # 2) mark image labeled & reset QA status --------------------------
            update_fields = {
                "status": "labeled",
                "timestamp_labeled": firestore.SERVER_TIMESTAMP,
                "task_expires_at": None,
                "flagged": payload.get("flagged", False),
                "qa_status": "pending",
            }
            # We NO LONGER clear qa_feedback so reviewers can see past remarks
            txn.update(img_ref, update_fields)

            # 3) user stats (unchanged) ---------------------------------------
            user_ref = self.users.document(user_id)
            txn.set(user_ref, {}, merge=True)
            txn.update(
                user_ref,
                {
                    "last_labeled_image_id": image_id,
                    "total_images_labeled": firestore.Increment(1),
                    "timestamp_last_labeled": firestore.SERVER_TIMESTAMP,
                },
            )

        _txn(self.db.transaction())

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------
    def get_image_url(self, image_doc: Dict) -> str:  # type: ignore[override]
        bb_url = image_doc.get("bb_url")
        if not bb_url:
            raise BackblazeResolverError(
                f"Missing or empty bb_url in document. Document keys: {list(image_doc.keys())}, "
                f"bb_url value: {repr(bb_url)}"
            )
        
        # Use only the bb_url resolver, no fallback
        return self._resolve(bb_url)  # type: ignore[index]

    # ------------------------------------------------------------------
    # User history
    # ------------------------------------------------------------------
    def get_user_history(self, user_id: str, limit: int = 200) -> list[Dict]:  # noqa: D401
        q = (
            self.labels.where("labeled_by", "==", user_id)
            .order_by("timestamp_created", direction=firestore.Query.DESCENDING)
            .limit(limit)
        )
        # Include the Firestore doc ID (which is the image_id) so callers can
        # reliably reference the associated image document.
        return [
            {**doc.to_dict(), "image_id": doc.id, "status": "labeled"}
            for doc in q.stream()
        ]

    # ------------------------------------------------------------------
    # Image document lookup (helper for navigation)
    # ------------------------------------------------------------------
    def get_image_doc(self, image_id: str) -> Optional[Dict]:  # type: ignore[override]
        snap = self.images.document(image_id).get()
        if not snap.exists:
            return None
        data = snap.to_dict() or {}
        # Ensure key fields exist for downstream UI logic
        data.update({"image_id": image_id})
        return data

    # ------------------------------------------------------------------
    # QA helper methods (admin only)
    # ------------------------------------------------------------------
    def confirm_labels(self, image_id: str, admin_id: str) -> None:
        """Mark *image_id* as QA-confirmed (immutable for labelers)."""
        self.images.document(image_id).update(
            {
                "qa_status": "confirmed",
                "qa_feedback": firestore.DELETE_FIELD,
                "assigned_to": None,
                "confirmed_by": admin_id,
                "timestamp_confirmed": firestore.SERVER_TIMESTAMP,
            }
        )

    def request_revision(self, image_id: str, labeler_id: str, admin_id: str, feedback: str | None = "") -> None:  # noqa: D401
        """Send *image_id* back for revision to *labeler_id* with optional feedback."""
        self.images.document(image_id).update(
            {
                "qa_status": "review",
                "qa_feedback": feedback or "",
                "assigned_to": labeler_id,
                "review_requested_by": admin_id,
                "timestamp_review_requested": firestore.SERVER_TIMESTAMP,
            }
        )

    def get_next_review_task(self, labeler_id: str, after_image_id: str = None) -> Optional[Dict]:  # noqa: D401
        """Return the next (older) labeled image by *labeler_id* awaiting QA (qa_status == 'pending').
        If after_image_id is given, return the next older image after that one.
        """
        q = (
            self.labels.where("labeled_by", "==", labeler_id)
            .order_by("timestamp_created", direction=firestore.Query.DESCENDING)
            .limit(200)
        )
        found = after_image_id is None
        for lbl_snap in q.stream():
            img_id = lbl_snap.id
            if not found:
                if img_id == after_image_id:
                    found = True
                continue
            img_snap = self.images.document(img_id).get()
            if not img_snap.exists:
                continue
            img_doc = img_snap.to_dict() or {}
            if img_doc.get("qa_status") == "pending":
                img_doc.update({"image_id": img_id})
                return img_doc
        return None

    def get_prev_review_task(self, labeler_id: str, before_image_id: str) -> Optional[Dict]:  # noqa: D401
        """Return the previous (newer) labeled image by *labeler_id* awaiting QA (qa_status == 'pending').
        If before_image_id is given, return the next newer image before that one.
        """
        q = (
            self.labels.where("labeled_by", "==", labeler_id)
            .order_by("timestamp_created", direction=firestore.Query.DESCENDING)
            .limit(200)
        )
        prev = None
        for lbl_snap in q.stream():
            img_id = lbl_snap.id
            if img_id == before_image_id:
                return prev
            img_snap = self.images.document(img_id).get()
            if not img_snap.exists:
                continue
            img_doc = img_snap.to_dict() or {}
            if img_doc.get("qa_status") == "pending":
                prev = img_doc.copy()
                prev["image_id"] = img_id
        return None 