from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from .base import LabelRepo

LABEL_CSV_PATH = "labeled_data.csv"
IMAGE_FOLDER = "images/"


class DevRepo(LabelRepo):
    """CSV-backed (or in-memory) implementation for local dev/testing."""

    def __init__(self, kind: str = "csv") -> None:
        assert kind in {"csv", "mock"}
        self.kind = kind
        self._df: pd.DataFrame | None = None
        self._mock: Dict[str, Dict] = {}
        self._images = self._discover()
        self._cursor: Dict[str, int] = {}

    # ---------------- task management ----------------
    def get_next_task(self, user_id: str) -> Optional[Dict]:
        idx = self._cursor.get(user_id, 0)
        if idx >= len(self._images):
            return None
        path = self._images[idx]
        self._cursor[user_id] = idx + 1
        return {
            "image_id": Path(path).name,
            "local_path": path,
            "bb_url": path,
            "status": "in_progress",
        }

    def release_task(self, image_id: str, user_id: str, *, abandon: bool = False) -> None:  # noqa: D401
        # no-op for local mode
        return None

    # ---------------- label I/O ----------------
    def load_labels(self, image_id: str) -> Optional[Dict]:
        if self.kind == "mock":
            return self._mock.get(image_id)
        df = self._csv()
        row = df[df["image_path"] == image_id]
        return row.to_dict("records")[0] if not row.empty else None

    def save_labels(self, image_id: str, payload: Dict, user_id: str) -> None:
        if self.kind == "mock":
            self._mock[image_id] = payload
            return
        df = self._csv()
        df = pd.concat([df[df["image_path"] != image_id], pd.DataFrame([payload])], ignore_index=True)
        df.to_csv(LABEL_CSV_PATH, index=False)
        self._df = df

    # ---------------- helper ----------------
    def get_image_url(self, image_doc: Dict) -> str:  # type: ignore[override]
        return image_doc.get("local_path", "")

    # ---------------- history ----------------
    def get_user_history(self, user_id: str, limit: int = 200) -> list[Dict]:  # noqa: D401
        return []  # history not supported in dev mode

    # ---------------- internals ----------------
    @staticmethod
    def _discover() -> List[str]:
        if not os.path.isdir(IMAGE_FOLDER):
            return []
        return sorted(
            str(Path(IMAGE_FOLDER) / f)
            for f in os.listdir(IMAGE_FOLDER)
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
        )

    def _csv(self) -> pd.DataFrame:
        if self._df is not None:
            return self._df
        if os.path.exists(LABEL_CSV_PATH):
            self._df = pd.read_csv(LABEL_CSV_PATH)
        else:
            self._df = pd.DataFrame(columns=["image_path"])
        return self._df 