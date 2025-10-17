"""Reassign labels from multiple users to a single primary user.

Usage:
    python -m admin_tools.merge_labels --primary qurat --from qurat2 qurat_review [--preserve-original]

Environment discovery for Firestore credentials matches other admin tools:
    1) FIRESTORE_CREDENTIALS_JSON (raw JSON)
    2) SERVICE_ACCOUNT_JSON or GOOGLE_APPLICATION_CREDENTIALS (path to file)
    3) Application Default Credentials (Cloud Run / gcloud)
"""

from __future__ import annotations

import argparse
from typing import List

from google.cloud import firestore  # type: ignore
from auth import _fs_client  # reuse existing cached client


def _reassign_labels(primary: str, sources: List[str], preserve_original: bool = False) -> int:
    db: firestore.Client = _fs_client()  # type: ignore[valid-type]
    labels = db.collection("REVS_labels")

    batch = db.batch()
    ops = 0

    for src in sources:
        for doc in labels.where("labeled_by", "==", src).stream():
            update = {"labeled_by": primary}
            if preserve_original:
                # Keep provenance of the original labeler
                update["original_labeler"] = src
            batch.update(doc.reference, update)
            ops += 1
            if ops % 400 == 0:
                batch.commit()
                batch = db.batch()

    if ops % 400 != 0:
        batch.commit()

    return ops


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Merge labels into a single user")
    p.add_argument("--primary", required=True, help="Target username to own labels after merge")
    p.add_argument("--from", dest="sources", nargs="+", required=True, help="Usernames to migrate from")
    p.add_argument("--preserve-original", action="store_true", help="Store original labeler in 'original_labeler'")
    return p


def main(argv: List[str] | None = None) -> None:  # pragma: no cover
    parser = _build_parser()
    args = parser.parse_args(argv)

    total = _reassign_labels(args.primary, args.sources, args.preserve_original)
    print(f"Reassigned {total} labels to '{args.primary}' from {args.sources}")
    print("Next: recompute counters -> python -m admin_tools.fix_user_counters")


if __name__ == "__main__":  # pragma: no cover
    main()


