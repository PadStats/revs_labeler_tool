from __future__ import annotations

from typing import Dict, Optional, Protocol


class LabelRepo(Protocol):
    """Storage-agnostic contract used by the Streamlit UI."""

    # --- task management ---
    def get_next_task(self, user_id: str) -> Optional[Dict]:
        """Lock & return the next image for *user_id*, or None if none left."""

    def release_task(self, image_id: str, user_id: str, *, abandon: bool = False) -> None:
        """Unlock *image_id* (set abandon=True to return it to the pool)."""

    # --- I/O ---
    def load_labels(self, image_id: str) -> Optional[Dict]:
        """Return existing payload or None."""

    def save_labels(self, image_id: str, payload: Dict, user_id: str) -> None:
        """Persist labels & mark task done."""

    # --- helper ---
    def get_image_url(self, image_doc: Dict) -> str:
        """Translate storage pointer into a displayable URL."""

    # --- user history ---
    def get_user_history(self, user_id: str, limit: int = 200) -> list[Dict]:
        """Return newest-first list of this user's labeled docs (length <= *limit*).""" 