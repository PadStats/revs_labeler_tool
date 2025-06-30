#!/usr/bin/env python
"""Provision or update a user account in REVS_users.

Moved under admin_tools for organisational clarity.

Usage examples:
    python -m admin_tools.provision_user alice S3cretPass!
    python -m admin_tools.provision_user bob MyPass --role reviewer
    python -m admin_tools.provision_user carol --disable
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
import argparse

from dotenv import load_dotenv  # type: ignore
import bcrypt  # type: ignore
from google.cloud import firestore  # type: ignore
from google.oauth2 import service_account  # type: ignore

load_dotenv()


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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Provision or update a REVS user account",
        prog="python -m admin_tools.provision_user",
    )
    parser.add_argument("username", help="Firestore document ID (username)")
    parser.add_argument(
        "password", nargs="?", help="Raw password (omit when --disable)")
    parser.add_argument("--role", default="labeler", help="Role string (default: labeler)")
    parser.add_argument(
        "--disable",
        action="store_true",
        help="Disable the account instead of (re)enabling it",
    )
    args = parser.parse_args()
    if not args.disable and not args.password:
        parser.error("password is required unless --disable is given")
    return args


def main() -> None:
    args = _parse_args()
    db = _client()

    payload: dict[str, Any] = {
        "enabled": not args.disable,
        "role": args.role,
    }
    if args.password:
        payload["password_hash"] = bcrypt.hashpw(
            args.password.encode(), bcrypt.gensalt()
        ).decode()

    db.collection("REVS_users").document(args.username).set(payload, merge=True)

    action = "disabled" if args.disable else "provisioned / updated"
    print(f"✓ user '{args.username}' {action}")


if __name__ == "__main__":
    main() 