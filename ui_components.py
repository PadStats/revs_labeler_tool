from __future__ import annotations

"""Facade that re-exports the UI helpers used by app.py.

This file lets us change the underlying implementation without touching the
UI business logic.  It now depends on `internal_ui`, not `legacy_app`.
"""

import internal_ui as _ui

# Re-export the pieces the new app needs.  Type: ignore is used because legacy
# module isn't typed.
init_session_state = _ui.init_session_state  # type: ignore[attr-defined]
reset_session_state_to_defaults = _ui.reset_session_state_to_defaults  # type: ignore[attr-defined]

build_dropdown_cascade_ui = _ui.build_dropdown_cascade_ui  # type: ignore[attr-defined]
build_feature_ui = _ui.build_feature_ui  # type: ignore[attr-defined]
build_contextual_attribute_ui = _ui.build_contextual_attribute_ui  # type: ignore[attr-defined]
build_condition_scores_ui = _ui.build_condition_scores_ui  # type: ignore[attr-defined]

can_move_on = _ui.can_move_on  # type: ignore[attr-defined]
chains_to_label_strings = _ui.chains_to_label_strings  # type: ignore[attr-defined]
get_leaf_locations = _ui.get_leaf_locations  # type: ignore[attr-defined]
label_strings_to_chains = _ui.label_strings_to_chains  # type: ignore[attr-defined]
get_complete_chains = _ui.get_complete_chains  # type: ignore[attr-defined]

# State restoration functions
restore_attribute_state = _ui.restore_attribute_state  # type: ignore[attr-defined]
restore_condition_state = _ui.restore_condition_state  # type: ignore[attr-defined]

# Taxonomies
LOCATION_TAXONOMY = _ui.LOCATION_TAXONOMY  # type: ignore[attr-defined]
FEATURE_TAXONOMY = _ui.FEATURE_TAXONOMY  # type: ignore[attr-defined]
ATTRIBUTE_RULES = _ui.ATTRIBUTE_RULES  # type: ignore[attr-defined] 