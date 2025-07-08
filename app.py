import os
from dotenv import load_dotenv
from datetime import datetime
import requests
from PIL import Image
from io import BytesIO
import time
import logging
import base64

import streamlit as st

from labeler_backend import get_repo
import ui_components as ui
from labeler_backend.bb_resolver import BackblazeResolverError  # new import
import auth  # NEW: authentication helpers
from taxonomy import ATTRIBUTE_RULES  # Import for attribute loading logic

# Constants
HISTORY_LIMIT = int(os.getenv("HISTORY_LIMIT", "10"))  # How many recent images to show in history


# ---------------------------------------------------------------------------
# Logging setup (console only, keeps GUI clean)
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Session-state helpers
# ---------------------------------------------------------------------------


def _init_state() -> None:
    if "current_task" not in st.session_state:
        st.session_state.current_task = None  # type: ignore[assignment]
    if "completed_stack" not in st.session_state:
        st.session_state.completed_stack = []  # type: ignore[assignment]
    if "notes" not in st.session_state:
        st.session_state.notes = ""
    if "flagged" not in st.session_state:
        st.session_state.flagged = False
    if "skip_label_loading" not in st.session_state:
        st.session_state.skip_label_loading = False
    if "navigation_history" not in st.session_state:
        st.session_state.navigation_history = []  # type: ignore[assignment]
    
    # Initialize cache structure
    if "task_cache" not in st.session_state:
        st.session_state.task_cache = {
            'current_image_id': None,
            'task_data': None,
            'labels': None,
            'ui_state': None,
            'cached_at': None,
            'last_accessed': None,
            'resolved_url': None,  # cached resolved Backblaze URL
            'image_bytes': None,   # raw bytes of downloaded image
            'image_meta': None     # (width, height)
        }

    # Counter to detect widget-triggered reruns (used by cache logic)
    if "widget_refresh_counter" not in st.session_state:
        st.session_state.widget_refresh_counter = 0


def _update_cache_ui_state(update_timestamp: bool = False) -> None:
    """Refresh cached ui_state from current session state."""
    cache = st.session_state.task_cache
    if cache.get('current_image_id'):
        cache['ui_state'] = build_complete_ui_state()
        if update_timestamp:
            cache['last_accessed'] = time.time()
        logger.info(f"[CACHE] Hit for image {cache['current_image_id']}")


def cache_task_data(image_id: str, task_data: dict, labels: dict, ui_state: dict) -> None:
    """Cache task data and UI state for the given image."""
    st.session_state.task_cache = {
        'current_image_id': image_id,
        'task_data': task_data,
        'labels': labels,
        'ui_state': ui_state,
        'cached_at': time.time(),
        'last_accessed': time.time(),
        'resolved_url': None,  # cached resolved Backblaze URL
        'image_bytes': None,   # raw bytes of downloaded image
        'image_meta': None     # (width, height)
    }
    logger.info(f"[CACHE] Stored data for image {image_id}")


def restore_from_cache(image_id: str) -> bool:
    """Restore UI state from cache. Returns True if successful, False if cache miss."""
    cache = st.session_state.task_cache
    
    # Check if we have valid cache for this image
    if (cache.get('current_image_id') == image_id and 
        cache.get('cached_at') is not None):
        
        # Restore UI state from cache
        ui_state = cache.get('ui_state', {})
        if ui_state:
            # Restore session state from cached UI state
            for key, value in ui_state.items():
                st.session_state[key] = value
            _update_cache_ui_state(update_timestamp=True)
            logger.info(f"[CACHE] Hit for image {image_id}")
            return True
    
    logger.info(f"[CACHE] Miss for image {image_id}")
    return False


def clear_cache() -> None:
    """Clear the current task cache."""
    st.session_state.task_cache = {
        'current_image_id': None,
        'task_data': None,
        'labels': None,
        'ui_state': None,
        'cached_at': None,
        'last_accessed': None,
        'resolved_url': None,  # cached resolved Backblaze URL
        'image_bytes': None,   # raw bytes of downloaded image
        'image_meta': None     # (width, height)
    }


def build_complete_ui_state() -> dict:
    """Build a complete snapshot of the current UI state for caching."""
    ui_state = {}
    
    # Cache all relevant session state
    cache_keys = [
        'location_chains', 'notes', 'flagged', 'location_attributes',
        'condition_scores', 'property_condition_na', 'property_condition_confirmed',
        'persistent_feature_state', 'persistent_condition_state', 'persistent_attribute_state',
        'widget_refresh_counter'
    ]
    
    for key in cache_keys:
        if key in st.session_state:
            ui_state[key] = st.session_state[key]
    
    # Cache feature selections (only if UI components are available)
    try:
        leaves = ui.get_leaf_locations()
        for loc in leaves:
            if loc not in ui.FEATURE_TAXONOMY:
                continue
            for category in ui.FEATURE_TAXONOMY[loc]:
                na_key = f"na_{loc}_{category}"
                sel_key = f"sel_{loc}_{category}"
                if na_key in st.session_state:
                    ui_state[na_key] = st.session_state[na_key]
                if sel_key in st.session_state:
                    ui_state[sel_key] = st.session_state[sel_key]
    except (AttributeError, NameError):
        # UI components not available yet, skip feature caching
        pass
    
    return ui_state


def update_cache_with_saved_data(image_id: str, saved_labels: dict) -> None:
    """Update cache with newly saved label data."""
    cache = st.session_state.task_cache
    if cache.get('current_image_id') == image_id:
        cache['labels'] = saved_labels
        cache['ui_state'] = build_complete_ui_state()
        cache['last_accessed'] = time.time()
        logger.info(f"[CACHE] Updated after save for image {image_id}")


def show_login_gate():
    """Show login gate before proceeding to main app."""
    st.set_page_config(page_title="Property Labeler – Login", layout="wide")
    _inject_compact_css()

    # Wrap the entire login UI in a disposable container so we can fully clear it
    login_box = st.container()

    with login_box:
        st.title("🏠 Property Image Labeling Tool – Login")
        st.markdown("Please enter the credentials provided to you by your supervisor.")

        # Center the input widgets
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Log in", disabled=not (username and password), use_container_width=True):
                snap = auth.get_user_doc(username)
                if not snap.exists:
                    st.error("Unknown user or password")
                    return

                data = snap.to_dict() or {}
                stored_hash = data.get("password_hash", "")
                if not stored_hash or not auth.verify_pw(password, stored_hash):
                    st.error("Invalid password or password")
                    return

                if not data.get("enabled", True):
                    st.error("Account disabled, please contact your supervisor")
                    return

                # Success – populate session and reload the app
                st.session_state.username = username
                # Store user role for conditional UI rendering (default to 'labeler')
                st.session_state.role = data.get("role", "labeler")
                st.session_state.authenticated = True

                # Clear the login UI immediately to minimise flash before rerun
                login_box.empty()
                st.rerun()


# ---------------------------------------------------------------------------
# One-time environment loading (prevents re-parsing .env on every rerun)
# ---------------------------------------------------------------------------


@st.cache_resource  # runs once per browser session
def _load_env() -> None:
    """Load .env only once per Streamlit session."""
    load_dotenv()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:  # noqa: C901
    print("DEBUG: main UI function CALLED")
    """Slimmed-down but functional prototype using LabelRepo."""

    _init_state()  # Initialize our custom session state
    ui.init_session_state()

    # Load environment variables (cached so we do not redo I/O every rerun)
    _load_env()

    # Authentication gate – user must be logged in
    if not st.session_state.get("authenticated"):
        show_login_gate()
        return

    # ------------------------------------------------------------------
    # HEADER CONTAINER – we will populate it later once image and metadata
    # are available.  We purposely leave it empty now to avoid extra DOM
    # nodes that could linger.
    # ------------------------------------------------------------------
    header_container = st.container()

    # Determine current user's role
    is_admin = st.session_state.get("role") == "admin"

    # ------------------------------------------------------------------
    # Admin controls (sidebar) – allow switching between Label & Review
    # ------------------------------------------------------------------
    admin_mode: str = st.session_state.get("admin_mode", "Label")
    review_target_user: str = st.session_state.get("review_target_user", "")
    if is_admin:
        with st.sidebar:
            st.markdown("### Admin Controls")
            admin_mode = st.radio("Mode", ["Label", "Review"], key="admin_mode")
            if admin_mode == "Review":
                review_target_user = st.text_input("Labeler username", key="review_target_user")
    else:
        # force defaults for non-admins
        admin_mode, review_target_user = "Label", ""

    is_admin_review = is_admin and admin_mode == "Review" and bool(review_target_user)

    # Handle mode switch: if admin switches from Review to Label, reset state and load labeler image
    if is_admin and admin_mode == "Label" and st.session_state.get("_last_review_user"):
        st.session_state._last_review_user = None
        st.session_state.current_task = None
        # Reset all session state relevant to labeling UI
        for key in list(st.session_state.keys()):
            if key not in ("role", "username", "authenticated", "repo", "repo_mode", "admin_mode"):
                del st.session_state[key]
        st.rerun()

    # ---------------------------------------------------------------
    # Cache the LabelRepo so we do NOT rebuild a Firestore client on
    # every Streamlit rerun (which causes perceptible UI lag).
    # ---------------------------------------------------------------

    mode = os.getenv("LABEL_REPO", "dev")

    # Build the repo only once per Streamlit session and reuse it.
    # We keep the selected mode alongside to allow hot-switching if
    # the env var changes while the session is running (unlikely but
    # prevents stale caching during development).
    if (
        "repo" not in st.session_state  # first run
        or st.session_state.get("repo_mode") != mode  # mode changed
    ):
        st.session_state.repo = get_repo(mode)
        st.session_state.repo_mode = mode

    repo = st.session_state.repo  # type: ignore[assignment]

    # Note: Removed st.on_session_end() as it's not available in current Streamlit version
    # Task cleanup will be handled differently - tasks will be released when user navigates away
    # or when the session naturally ends (Firestore has timeout reclaim for stale locks)

    st.set_page_config(page_title="Property Labeler – prototype", layout="wide")
    _inject_compact_css()

    # 1️⃣ acquire or resume a task ------------------------------------------------
    task = st.session_state.current_task
    if task is None and st.session_state.get("_last_loaded_id") is not None:
        logger.info(f"[DEBUG] WARNING: current_task is None but _last_loaded_id exists: {st.session_state.get('_last_loaded_id')}")
    logger.info(f"[DEBUG] Task at start: {task.get('image_id') if task else 'None'} (status: {task.get('status') if task else 'N/A'})")
    if task is None:
        logger.info(f"[DEBUG] No current task, loading new task")

        # --- Admin review path -------------------------------------------------
        if is_admin_review:
            # If the username changed or no current task, load the first pending image
            if (
                st.session_state.get("_last_review_user") != review_target_user
                or st.session_state.current_task is None
            ):
                task = repo.get_next_review_task(review_target_user)
                st.session_state.current_task = task
                st.session_state._last_review_user = review_target_user
                if task is None:
                    st.success(f"🎉 No more images to review for {review_target_user}.")
                    return
            else:
                task = st.session_state.current_task
        # --- Normal labeler path ---------------------------------------------
        else:
            # first check if we already have a pre-loaded history stack
            hist_stack: list = st.session_state.get("history_stack", [])  # type: ignore[var-annotated]
            if hist_stack:
                task = hist_stack.pop(0)
                st.session_state.history_stack = hist_stack
                st.session_state.current_task = task
                logger.info(f"[DEBUG] Loaded task from history stack: {task.get('image_id')} (status: {task.get('status')})")
                # Add to navigation history when loading from history stack
                if task.get("image_id") and task.get("image_id") not in st.session_state.navigation_history:
                    st.session_state.navigation_history.append(task.get("image_id"))
            else:
                logger.info(f"[DEBUG] No history stack, getting next task from repo")
                task = repo.get_next_task(st.session_state.username)
                if task is None:
                    logger.info(f"[DEBUG] No next task available, falling back to labeled history")
                    # nothing in progress – fall back to labeled history
                    history = repo.get_user_history(st.session_state.username, limit=HISTORY_LIMIT)
                    if history:
                        st.session_state.history_stack = history[1:]
                        task = history[0]
                        st.session_state.current_task = task
                        logger.info(f"[DEBUG] Loaded task from user history: {task.get('image_id')} (status: {task.get('status')})")
                        # Add to navigation history when loading from user history
                        if task.get("image_id") and task.get("image_id") not in st.session_state.navigation_history:
                            st.session_state.navigation_history.append(task.get("image_id"))
                    else:
                        logger.info(f"[DEBUG] No user history available")
                        st.success("🎉 No more images to label.")
                        return
                else:
                    logger.info(f"[DEBUG] Got new task from repo: {task.get('image_id')} (status: {task.get('status')})")
                    # Add to navigation history when loading new task
                    if task.get("image_id") and task.get("image_id") not in st.session_state.navigation_history:
                        st.session_state.navigation_history.append(task.get("image_id"))

    # ---- Load task data and rebuild session state with caching ----
    logger.info(f"[DEBUG] Task loading condition: task={task.get('image_id') if task else 'None'}, _last_loaded_id={st.session_state.get('_last_loaded_id')}")
    if task is not None and (st.session_state.get("_last_loaded_id") != task["image_id"]):
        image_id = task["image_id"]
        
        # Try to restore from cache first
        if restore_from_cache(image_id):
            # Successfully restored from cache - no Firestore calls needed
            st.session_state._last_loaded_id = image_id
        else:
            # Cache miss - load from Firestore and cache the data
            logger.info(f"[FS] Loading labels for image {image_id}")
            existing = repo.load_labels(image_id)
            st.session_state._last_loaded_id = image_id

        if existing:
            # Update task status to labeled since we found existing labels
            task["status"] = "labeled"
            st.session_state.current_task = task
            ui.reset_session_state_to_defaults()

            # Spatial chains
            raw_spatial = existing.get("spatial_labels", [])
            if isinstance(raw_spatial, str):
                labels_list = [s for s in raw_spatial.split("|") if s]
            else:
                labels_list = raw_spatial

            st.session_state.location_chains = (
                ui.label_strings_to_chains(labels_list) if labels_list else [{}]
            )

            # Notes & flag
            st.session_state.notes = existing.get("notes", "")
            st.session_state.flagged = bool(existing.get("flagged", False))

            # Feature selections
            st.session_state.persistent_feature_state = {}
            features_raw = existing.get("feature_labels", [])
            
            # Parse features from the new structured format "Location:Category:Feature"
            # or fall back to legacy flat format for backward compatibility
            feature_by_location_category = {}  # {(location, category): [features]}
            
            if isinstance(features_raw, str):
                feature_list = features_raw.split("|") if features_raw else []
            else:
                feature_list = features_raw
            
            # Check if this is the new structured format (contains ":")
            is_structured_format = any(":" in feature for feature in feature_list)
            
            if is_structured_format:
                # New structured format: "Location:Category:Feature"
                for feature_entry in feature_list:
                    if ":" in feature_entry:
                        parts = feature_entry.split(":", 2)  # Split into max 3 parts
                        if len(parts) == 3:
                            location, category, feature = parts
                            if (location, category) not in feature_by_location_category:
                                feature_by_location_category[(location, category)] = []
                            feature_by_location_category[(location, category)].append(feature)
            else:
                # Legacy flat format - convert to structured for processing
                for loc in ui.get_leaf_locations():
                    if loc not in ui.FEATURE_TAXONOMY:
                        continue
                    for category, feats in ui.FEATURE_TAXONOMY[loc].items():
                        # Check if "None" is in the feature set for this category
                        if "None" in feature_list and "None" in feats:
                            feature_by_location_category[(loc, category)] = ["None"]
                        else:
                            # Look for actual feature selections
                            sel = [f for f in feature_list if f in feats]
                            if sel:
                                feature_by_location_category[(loc, category)] = sel
            
            # Process the parsed features
            for loc in ui.get_leaf_locations():
                if loc not in ui.FEATURE_TAXONOMY:
                    continue
                for category in ui.FEATURE_TAXONOMY[loc]:
                    if (loc, category) in feature_by_location_category:
                        # Features were found for this category
                        features = feature_by_location_category[(loc, category)]
                        
                        # --- NEW: canonicalise loaded feature names to match taxonomy options (case-insensitive) ---
                        canon_options = ui.FEATURE_TAXONOMY[loc][category]
                        canon_features = []
                        for feat in features:
                            # Find first option whose lower-case matches
                            matched = next((opt for opt in canon_options if opt.lower() == feat.lower()), None)
                            canon_features.append(matched if matched is not None else feat)
                        # -------------------------------------------------------------------------------
                        
                        st.session_state.persistent_feature_state[f"persistent_na_{loc}_{category}"] = False
                        st.session_state.persistent_feature_state[f"persistent_sel_{loc}_{category}"] = canon_features
                    else:
                        # No features found - this category was marked as N/A
                        st.session_state.persistent_feature_state[f"persistent_na_{loc}_{category}"] = True
                        st.session_state.persistent_feature_state[f"persistent_sel_{loc}_{category}"] = []

            # Attributes
            st.session_state.location_attributes = {}
            attrs_map = existing.get("attributes", {})
            if isinstance(attrs_map, dict):
                # First, collect all attributes that are present in the database
                loaded_attrs = set()
                for attr, value in attrs_map.items():
                    # Find the original attribute name (with spaces) from the normalized name
                    original_attr = None
                    for orig_attr in ui.LOCATION_TAXONOMY.get("attributes", {}):
                        if orig_attr.replace(" ", "_") == attr:
                            original_attr = orig_attr
                            break
                    if not original_attr:
                        logger.warning(f"[ATTR LOAD] Could not map attribute key '{attr}' to taxonomy. Using key as-is.")
                        original_attr = attr  # Fallback: use the Firestore key as the attribute name
                    logger.info(f"[ATTR LOAD] Mapping Firestore key '{attr}' to UI attribute '{original_attr}' with value '{value}'")
                    # Normalize value for UI
                    if value is None or value == "N/A":
                        val = "N/A"
                    else:
                        attr_opts = ui.LOCATION_TAXONOMY.get("attributes", {}).get(original_attr, []) if original_attr else []
                        # If options are strings "True"/"False", convert booleans to strings
                        if isinstance(value, bool) and all(isinstance(o, str) for o in attr_opts):
                            val = "True" if value else "False"
                        else:
                            val = value
                    # Since attributes are now image-level, not location-dependent, always use the first location key
                    found_location = False
                    for idx, chain in enumerate(st.session_state.location_chains):
                        if not chain or found_location:
                            continue
                        # Safely get the leaf location with proper bounds checking
                        chain_values = list(chain.values())
                        if not chain_values:
                            continue
                        if chain_values[-1] != "N/A":
                            leaf_location = chain_values[-1]
                        elif len(chain_values) > 1:
                            leaf_location = chain_values[-2]
                        else:
                            leaf_location = None
                        if not leaf_location:
                            continue
                        location_key = f"loc_{idx}_{leaf_location}"
                        # For image-level attributes, just use the first location key
                        st.session_state.location_attributes.setdefault(location_key, {})[original_attr] = val
                        loaded_attrs.add((location_key, original_attr))
                        found_location = True  # Only set for the first location
                        break
                
                # Now handle missing attributes - if an attribute should be present but isn't in the database,
                # it means it was "N/A" and we didn't save it. We need to set it to "N/A" for the UI.
                for idx, chain in enumerate(st.session_state.location_chains):
                    if not chain:
                        continue
                    
                    # Safely get the leaf location with proper bounds checking
                    chain_values = list(chain.values())
                    if not chain_values:
                        continue
                    
                    if chain_values[-1] != "N/A":
                        leaf_location = chain_values[-1]
                    elif len(chain_values) > 1:
                        leaf_location = chain_values[-2]
                    else:
                        leaf_location = None
                    
                    if not leaf_location:
                        continue
                    
                    location_key = f"loc_{idx}_{leaf_location}"
                    
                    # Find relevant attributes for this location
                    relevant = set()
                    for attr, locs in ATTRIBUTE_RULES.items():
                        if any(loc in step for step in chain for loc in locs):
                            relevant.add(attr)
                    
                    # For each relevant attribute, if it's not in the database, set it to "N/A"
                    for attr in relevant:
                        if (location_key, attr) not in loaded_attrs:
                            st.session_state.location_attributes.setdefault(location_key, {})[attr] = "N/A"

            # Populate persistent_attribute_state from loaded location_attributes
            # This is needed for the restore_attribute_state() function to work properly
            for location_key, attrs in st.session_state.location_attributes.items():
                for attr, value in attrs.items():
                    persistent_key = f"persistent_{location_key}_{attr}"
                    st.session_state.persistent_attribute_state[persistent_key] = value

            # Condition scores
            cond = existing.get("condition_scores", {})

            if isinstance(cond, dict):
                # New schema: condition_scores as object
                prop_val = cond.get("property_condition", 3.0)
                if prop_val is None:
                    # Handle None values for quality and improvement condition - convert to "N/A" for UI
                    quality_val = cond.get("quality_of_construction", "")
                    if quality_val is None:
                        quality_val = "N/A"
                    elif quality_val == "N/A":
                        quality_val = "N/A"
                    
                    improvement_val = cond.get("improvement_condition", "")
                    if improvement_val is None:
                        improvement_val = "N/A"
                    elif improvement_val == "N/A":
                        improvement_val = "N/A"
                    
                    st.session_state.condition_scores = {
                        "property_condition": 3.0,
                        "quality_of_construction": quality_val,
                        "improvement_condition": improvement_val,
                    }
                    st.session_state.property_condition_na = True
                    st.session_state.property_condition_confirmed = False
                else:
                    # Handle None values for quality and improvement condition - convert to "N/A" for UI
                    quality_val = cond.get("quality_of_construction", "")
                    if quality_val is None:
                        quality_val = "N/A"
                    elif quality_val == "N/A":
                        quality_val = "N/A"
                    
                    improvement_val = cond.get("improvement_condition", "")
                    if improvement_val is None:
                        improvement_val = "N/A"
                    elif improvement_val == "N/A":
                        improvement_val = "N/A"
                    
                    st.session_state.condition_scores = {
                        "property_condition": float(prop_val),
                        "quality_of_construction": quality_val,
                        "improvement_condition": improvement_val,
                    }
                    st.session_state.property_condition_na = False
                    st.session_state.property_condition_confirmed = True

                st.session_state.persistent_condition_state = {
                    "property_condition": st.session_state.condition_scores["property_condition"],
                    "quality_of_construction": st.session_state.condition_scores["quality_of_construction"],
                    "improvement_condition": st.session_state.condition_scores["improvement_condition"],
                    "property_confirmed": st.session_state.property_condition_confirmed,
                }

            elif "condition_score" in existing:
                # Legacy schema: single field condition_score
                prop_val = existing["condition_score"]
                if prop_val is None:
                    st.session_state.condition_scores = {
                        "property_condition": 3.0,
                        "quality_of_construction": "",
                        "improvement_condition": "",
                    }
                    st.session_state.property_condition_na = True
                    st.session_state.property_condition_confirmed = False
                else:
                    st.session_state.condition_scores = {
                        "property_condition": float(prop_val),
                        "quality_of_construction": "",
                        "improvement_condition": "",
                    }
                    st.session_state.property_condition_na = False
                    st.session_state.property_condition_confirmed = True

                st.session_state.persistent_condition_state = {
                    "property_condition": st.session_state.condition_scores["property_condition"],
                    "quality_of_construction": "",
                    "improvement_condition": "",
                    "property_confirmed": st.session_state.property_condition_confirmed,
                }

            # Increment/initialise widget refresh counter and cache data
            st.session_state.widget_refresh_counter += 1

            ui_state = build_complete_ui_state()
            cache_task_data(image_id, task, existing, ui_state)

        else:
            # No existing labels document – start with defaults and cache blank label set
            ui.reset_session_state_to_defaults()

            # ------------------------------------------------------------------
            # Seed pre-existing condition score (if any) from the image document.
            # The REVS_images schema evolved over time, so we support multiple
            # possible field layouts:
            #   1) Legacy  – top-level  "condition_score" (float | null)
            #   2) Current – nested     "condition_scores.property_condition"
            #   3) Ad-hoc  – top-level  "property_condition" (float | null)
            # Any *null* value is interpreted as "N/A".
            # ------------------------------------------------------------------

            prop_val = None

            if "condition_scores" in task and isinstance(task["condition_scores"], dict):
                # Newer schema – grab the nested field if present.
                prop_val = task["condition_scores"].get("property_condition")
            elif "condition_score" in task:
                # Legacy flat field.
                prop_val = task["condition_score"]
            elif "property_condition" in task:
                # Fallback catch-all.
                prop_val = task["property_condition"]

            # Normalise the value and update session state.
            if prop_val is None:
                # Treat null/None as "N/A".
                st.session_state.condition_scores = {
                    "property_condition": 3.0,
                    "quality_of_construction": "",
                    "improvement_condition": "",
                }
                st.session_state.property_condition_na = True
            else:
                try:
                    st.session_state.condition_scores = {
                        "property_condition": float(prop_val),
                        "quality_of_construction": "",
                        "improvement_condition": "",
                    }
                except (TypeError, ValueError):
                    # If the value is not directly castable (e.g. Decimal), fall back.
                    st.session_state.condition_scores = {
                        "property_condition": float(str(prop_val)),
                        "quality_of_construction": "",
                        "improvement_condition": "",
                    }
                st.session_state.property_condition_na = False

            # For images yet to be reviewed by a human the score is *not* confirmed.
            st.session_state.property_condition_confirmed = False

            # Persist so downstream UI rebuilds pick up the value via
            # ui.restore_condition_state().
            st.session_state.persistent_condition_state = {
                "property_condition": st.session_state.condition_scores["property_condition"],
                "quality_of_construction": "",
                "improvement_condition": "",
                "property_confirmed": False,
            }

            # Cache the loaded data (empty labels)
            st.session_state.widget_refresh_counter += 1
            ui_state = build_complete_ui_state()
            cache_task_data(image_id, task, {}, ui_state)

    # Admin info will be displayed in sticky header

    # Refresh cached ui_state snapshot (no GUI output)
    _update_cache_ui_state(update_timestamp=True)

    # Optional: log cache hit status for this image (after UI built, before debug panel)
    cache = st.session_state.task_cache
    hit = cache.get('current_image_id') == task['image_id']
    logger.info(f"[CACHE] {'Hit' if hit else 'Miss'} for image {task['image_id']}")

    # Store cache info for later rendering at very bottom
    cache_debug_info = {
        "cache": cache,
        "hit": hit,
    }

    # 2️⃣ display image in sticky header ----------------------------------------------------------
    image_displayed = False
    image_html = ""

    cache_entry = st.session_state.task_cache

    # ------------------------------------------------------------------
    # Resolve image URL (cached)
    # ------------------------------------------------------------------
    resolved_url: str | None = None
    if cache_entry.get('current_image_id') == task['image_id']:
        resolved_url = cache_entry.get('resolved_url')

    if resolved_url is None:
        try:
            resolved_url = repo.get_image_url(task)
            cache_entry['resolved_url'] = resolved_url
            logger.info(f"[CACHE] Stored resolved URL for {task['image_id']}")
        except Exception as e:
            logger.warning(f"API resolver failed: {e}")

    # Candidate sources (resolved URL first, fallback to raw image_url)
    image_sources: list[tuple[str, str]] = []
    if resolved_url:
        image_sources.append(("API Endpoint", resolved_url))

    if task.get('image_url'):
        image_sources.append(("Raw URL", task['image_url']))
    else:
        st.warning("⚠️ No raw image_url available in task")

    # ------------------------------------------------------------------
    # Use cached image bytes if present
    # ------------------------------------------------------------------
    if (
        cache_entry.get('current_image_id') == task['image_id']
        and cache_entry.get('image_b64')
        and cache_entry.get('image_meta')
    ):
        b64: str = cache_entry['image_b64']  # type: ignore[assignment]
        w, h = cache_entry['image_meta']
        logger.info("[PERF] base64 path used")
        image_html = _html_image_from_b64(b64, w, h, "Cache", task['image_id'], admin=is_admin)
        image_displayed = True
    else:
        # Try each image source and cache the first successful bytes download
        for source_name, url in image_sources:
            try:
                response = requests.get(url, timeout=2)
                response.raise_for_status()
                content_type = response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    raise ValueError(f"URL returned non-image content: {content_type}")
                img_bytes = response.content
                img = Image.open(BytesIO(img_bytes))

                # Pre-compute & store heavy transforms once
                img_b64 = base64.b64encode(img_bytes).decode()

                image_html = _html_image_from_b64(img_b64, img.size[0], img.size[1], source_name, task['image_id'], admin=is_admin)
                image_displayed = True

                # Cache bytes & meta for future reruns
                cache_entry['image_bytes'] = img_bytes
                cache_entry['image_meta'] = img.size
                cache_entry['image_b64'] = img_b64
                logger.info(f"[CACHE] Stored image bytes for {task['image_id']}")
                break
            except requests.HTTPError as http_err:
                st.warning(f"HTTP error for {source_name}: {http_err}")
                continue  # Try next source
            except Exception as e:
                st.warning(f"⚠️ Responsive sizing failed for {source_name}, trying simple display: {e}")
                try:
                    # For simple mode, we'll use st.image but need to handle it differently
                    st.image(url, use_container_width=True)
                    st.success(f"✅ Successfully displayed image via {source_name} (simple mode)")
                    image_displayed = True
                    # Create a placeholder HTML for the sticky header
                    image_html = f"<div style='text-align:center;padding:1rem;'><p>Image loaded via {source_name} (simple mode)</p></div>"
                    break
                except Exception as e:
                    st.error(f"❌ Failed to display image via {source_name}: {e}")
                    continue
    
    # If no image sources worked, allow user to skip
    if not image_displayed:
        st.error("❌ Unable to load image from any source")
        st.markdown("**Available image sources:**")
        for source_name, url in image_sources:
            st.markdown(f"- {source_name}: `{url}`")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔄 Retry Image Loading", use_container_width=True):
                st.rerun()
        with col2:
            if st.button("⏭️ Skip This Image", use_container_width=True, type="primary"):
                # Mark as flagged and move to next
                st.session_state.flagged = True
                # Save current state (even if minimal) and move to next
                try:
                    payload = _build_payload()
                    logger.info(f"[FS] Saving labels for image {task['image_id']} (skip)")
                    repo.save_labels(task["image_id"], payload, st.session_state.username)
                    # Update cache with saved data
                    update_cache_with_saved_data(task["image_id"], payload)
                except:
                    pass  # Even if save fails, continue
                # Clear cache for new image
                clear_cache()
                st.session_state.current_task = None  # triggers get_next_task on rerun
                st.rerun()
        
        st.stop()  # Don't proceed with the rest of the app

    # Update the early header placeholder with the final version (includes image)
    header_container.empty()
    with header_container:
        render_sticky_header(image_html, st.session_state.username, is_admin, mode, task)

    # Dynamically offset subsequent content so it starts below the sticky header
    spacer_px: int
    if cache_entry.get('image_meta'):
        w, h = cache_entry['image_meta']  # type: ignore[assignment]
        # Add extra padding for header text, fade overlay, etc.
        base_extra = 40  # baseline for labelers
        if is_admin:
            base_extra += 50  # meta debug paragraph & extra margin
        spacer_px = _compute_display_height(w, h) + base_extra
    else:
        # Fallback if image dimensions are unavailable
        print("no image meta, using fallback")
        spacer_px = 600
    _inject_dynamic_spacer(spacer_px)

    # QA feedback banners will be shown in labeler mode only, positioned after navigation buttons
    confirmed_readonly = False

    # ------------------------------------------------------------------
    # Restore feature state EARLY - before UI
    # ------------------------------------------------------------------
    leaves = ui.get_leaf_locations()
    if leaves:
        # Restore feature state when locations are available
        for loc in leaves:
            if loc not in ui.FEATURE_TAXONOMY:
                continue
            for category in ui.FEATURE_TAXONOMY[loc]:
                na_key = f"na_{loc}_{category}"
                sel_key = f"sel_{loc}_{category}"
                
                # Restore from persistent storage only if not already in session state
                persistent_na_key = f"persistent_na_{loc}_{category}"
                persistent_sel_key = f"persistent_sel_{loc}_{category}"
                
                if na_key not in st.session_state and persistent_na_key in st.session_state.persistent_feature_state:
                    st.session_state[na_key] = st.session_state.persistent_feature_state[persistent_na_key]
                if sel_key not in st.session_state and persistent_sel_key in st.session_state.persistent_feature_state:
                    st.session_state[sel_key] = st.session_state.persistent_feature_state[persistent_sel_key]

    # Restore attribute state EARLY as well (from legacy)
    ui.restore_attribute_state()

    # Restore condition state EARLY as well (from legacy)
    ui.restore_condition_state()

    # ------------------------------------------------------------------
    # Admin review action buttons (Confirm / Needs changes)
    # ------------------------------------------------------------------
    if is_admin_review:
        # Navigation buttons for admin review
        nav_left, nav_prev, nav_next, nav_right = st.columns([3, 1, 1, 3], gap="small")

        # Check if navigation is available (similar to labeler mode)
        has_prev = False
        has_next = False
        try:
            # Check if previous image is available
            prev_check = repo.get_prev_review_task(review_target_user, before_image_id=task["image_id"])
            has_prev = prev_check is not None
            
            # Check if next image is available  
            next_check = repo.get_next_review_task(review_target_user, after_image_id=task["image_id"])
            has_next = next_check is not None
        except Exception as e:
            logger.error(f"[ADMIN NAV] Error checking navigation availability: {e}")
            has_prev = False
            has_next = False

        with nav_prev:
            # Check if we have a last action that can be undone
            last_action = st.session_state.get("last_review_action")
            can_undo = last_action and last_action.get("image_id") != task.get("image_id")
            has_prev_or_undo = has_prev or can_undo
            
            if st.button("⬅️ Previous", use_container_width=True, disabled=not has_prev_or_undo, key="admin_btn_prev"):
                # First check if we should load the last action image
                if can_undo:
                    # Load the last confirmed/needs_changes image
                    last_image_id = last_action["image_id"]
                    img_doc = repo.get_image_doc(last_image_id)
                    if img_doc:
                        st.session_state.current_task = img_doc
                        # Clear the last action since we're now viewing it
                        st.session_state.last_review_action = None
                        st.rerun()
                        return
                
                # Fall back to normal previous logic
                prev_task = repo.get_prev_review_task(review_target_user, before_image_id=task["image_id"])
                if prev_task:
                    st.session_state.current_task = prev_task
                    st.rerun()

        with nav_next:
            if st.button("➡️ Next", use_container_width=True, disabled=not has_next, key="admin_btn_next"):
                next_task = repo.get_next_review_task(review_target_user, after_image_id=task["image_id"])
                if next_task:
                    st.session_state.current_task = next_task
                    st.rerun()

        # Debug info in admin review mode
        with st.expander("🔍 Debug Info", expanded=False):
            st.write(f"**Mode:** {admin_mode}")
            st.write(f"**Review Target:** {review_target_user}")
            last_action = st.session_state.get("last_review_action")
            if last_action:
                st.write("**Last Review Action:**")
                st.json(last_action)
            else:
                st.write("**Last Review Action:** None")
            
            st.write(f"**Current Task ID:** {task.get('image_id', 'None')}")
            st.write(f"**Task Status:** {task.get('status', 'None')}")
            st.write(f"**QA Status:** {task.get('qa_status', 'None')}")

        # QA feedback and action buttons
        st.markdown("---")
        # Pre-populate feedback box with existing feedback (if any)
        existing_feedback = task.get("qa_feedback", "")
        fb_input = st.text_area("Optional feedback for labeler", value=existing_feedback, key="qa_feedback_input")
        col_c, col_r = st.columns([1, 1], gap="small")
        with col_c:
            if st.button("✅ Confirm", type="primary", use_container_width=True):
                repo.confirm_labels(task["image_id"], st.session_state.username)
                # Store last action for potential undo
                st.session_state.last_review_action = {
                    "image_id": task["image_id"],
                    "action": "confirmed",
                    "labeler": review_target_user
                }
                st.session_state.current_task = repo.get_next_review_task(review_target_user, after_image_id=task["image_id"])
                st.rerun()
        with col_r:
            if st.button("↩️ Needs changes", use_container_width=True):
                repo.request_revision(task["image_id"], review_target_user, st.session_state.username, fb_input)
                # Store last action for potential undo
                st.session_state.last_review_action = {
                    "image_id": task["image_id"],
                    "action": "needs_changes",
                    "labeler": review_target_user,
                    "feedback": fb_input
                }
                st.session_state.current_task = repo.get_next_review_task(review_target_user, after_image_id=task["image_id"])
                st.rerun()

        # Admin review: show current selections with improved layout
        st.markdown("---")
        
        # Create a nice header
        st.markdown("## 📋 Current Labels (Read-Only)")
        
        complete = ui.get_complete_chains()

        # Get features from current session state
        feats_by_loc = {}
        for loc in sorted(leaves):
            feats = []
            if loc in ui.FEATURE_TAXONOMY:
                for category in ui.FEATURE_TAXONOMY[loc]:
                    sel_key = f"sel_{loc}_{category}"
                    na_key = f"na_{loc}_{category}"
                    
                    # Get current state
                    selections = st.session_state.get(sel_key, [])
                    is_na = st.session_state.get(na_key, False)
                    
                    # If N/A is checked, don't show any features for this category
                    if not is_na:
                        # Add category context to features for better display
                        for feature in selections:
                            if feature == "None":
                                feats.append(f"{category}: None")
                            else:
                                feats.append(f"{category}: {feature}")
            feats_by_loc[loc] = feats

        # Improved 4-column layout: Locations | Features | Attributes | Condition Scores
        loc_col, feat_col, attr_col, cond_col = st.columns([1, 1, 1, 1], gap="medium")

        # ---- Locations ----
        with loc_col:
            st.markdown("### 🏠 Locations")
            if complete:
                for chain in complete:
                    st.markdown(f"**•** {' → '.join(chain)}")
            else:
                st.markdown("*No locations selected*")

        # ---- Features ----
        with feat_col:
            st.markdown("### 🔧 Features")
            
            groups = list(feats_by_loc.items())
            feature_hash = "|".join(
                f"{loc}:{','.join(sorted(feats))}" for loc, feats in sorted(feats_by_loc.items()) if feats
            )

            if not feature_hash:
                st.markdown("*No features selected*")
            else:
                # Create a nice table using Streamlit's built-in dataframe display
                import pandas as pd
                
                # Collect all features with their locations for table format
                table_data = []
                for loc, feats in groups:
                    if feats:
                        for feat in feats:
                            # Extract category and feature name from "Category: Feature" format
                            if ": " in feat:
                                category, feature_name = feat.split(": ", 1)
                                table_data.append({
                                    "Location": loc,
                                    "Category": category,
                                    "Feature": feature_name
                                })
                            else:
                                # Fallback for features without category prefix
                                table_data.append({
                                    "Location": loc,
                                    "Category": "General",
                                    "Feature": feat
                                })
                
                if table_data:
                    df = pd.DataFrame(table_data)
                    st.dataframe(
                        df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Location": st.column_config.TextColumn("Location", width="small"),
                            "Category": st.column_config.TextColumn("Category", width="medium"),
                            "Feature": st.column_config.TextColumn("Feature", width="medium")
                        }
                    )

        # ---- Attributes ----
        with attr_col:
            st.markdown("### 📊 Attributes")

            if not st.session_state.location_attributes:
                st.markdown("*No attributes set*")
            else:
                # Better formatted attribute display
                displayed_any = False
                for location_key, attrs in st.session_state.location_attributes.items():
                    if not attrs:
                        continue
                    loc_parts = location_key.split('_', 2)
                    if len(loc_parts) < 3:
                        continue
                    location_name = loc_parts[2]

                    for attr, value in attrs.items():
                        if value:
                            attr_display = attr.replace("_", " ").title()
                            st.markdown(f"**{location_name}** - {attr_display}: **{value}**")
                            displayed_any = True
                
                if not displayed_any:
                    st.markdown("*No attributes set*")

        # ---- Condition Scores ----
        with cond_col:
            st.markdown("### 🏗️ Condition Scores")

            cond = st.session_state.condition_scores  # type: ignore[attr-defined]
            prop_score = st.session_state.condition_scores['property_condition']
            
            if st.session_state.get("property_condition_na", False):
                st.markdown("**Property Condition:** N/A")
            else:
                score_interpretation = {
                    **{k: "Excellent" for k in [round(x/10,1) for x in range(10,20)]},
                    **{k: "Good" for k in [round(x/10,1) for x in range(20,30)]},
                    **{k: "Average" for k in [round(x/10,1) for x in range(30,40)]},
                    **{k: "Fair" for k in [round(x/10,1) for x in range(40,50)]},
                    5.0: "Poor",
                }
                closest = min(score_interpretation, key=lambda x: abs(x - prop_score))
                interp = score_interpretation[closest]
                st.markdown(f"**Property Condition:** {prop_score:.3f} ({interp})")

            quality_display = st.session_state.condition_scores["quality_of_construction"] or "Not Selected"
            st.markdown(f"**Quality of Construction:** {quality_display}")

            improvement_display = st.session_state.condition_scores["improvement_condition"] or "Not Selected"
            st.markdown(f"**Improvement Condition:** {improvement_display}")

        # Notes section for admin review
        st.markdown("---")
        st.markdown("### 📝 Notes")
        if st.session_state.notes.strip():
            st.markdown(f"**Labeler Notes:** {st.session_state.notes}")
        else:
            st.markdown("*No notes provided*")

    else:
        # ------------------------------------------------------------------
        # Main labeling UI (selectors, save/clear/flag, etc.)
        # ------------------------------------------------------------------
        
        # Navigation buttons (moved above current selections - from legacy)
        nav_left, nav_prev, nav_next, nav_right = st.columns([3, 1, 1, 3], gap="small")

        # Check validation status AFTER state restoration
        can_proceed = ui.can_move_on()

        with nav_prev:
            # Debug logging for navigation state
            current_image_id = task.get("image_id") if task else None
            current_status = task.get("status") if task else "N/A"
            logger.info(f"[NAV] Previous button check - Current: {current_image_id} (status: {current_status})")
            
            # Initialize navigation history if not exists
            if "navigation_history" not in st.session_state:
                st.session_state.navigation_history = []
            
            # Add current image to navigation history if not already there
            if current_image_id and current_image_id not in st.session_state.navigation_history:
                st.session_state.navigation_history.append(current_image_id)
                logger.info(f"[NAV] Added to history: {current_image_id}")

            # Check if we have more history to go back to
            has_remote_prev = False
            prev_entry = None
            
            try:
                # Get full user history (not limited by HISTORY_LIMIT)
                prev_hist = repo.get_user_history(st.session_state.username, limit=200)
                logger.info(f"[NAV] Retrieved {len(prev_hist)} labeled images from history")
                
                if prev_hist:
                    # History is ordered DESCENDING (newest first)
                    # So index 0 = newest, index 1 = second newest, etc.
                    
                    if current_status == "labeled":
                        # We're on a labeled image - find the next labeled image (older timestamp)
                        current_idx = None
                        for idx, entry in enumerate(prev_hist):
                            if entry.get("image_id") == current_image_id:
                                current_idx = idx
                                break
                        
                        if current_idx is not None and current_idx + 1 < len(prev_hist):
                            # Found current image in history, get the next one (older)
                            prev_entry = prev_hist[current_idx + 1]
                            has_remote_prev = True
                            logger.info(f"[NAV] Found previous labeled image: {prev_entry.get('image_id')} (idx: {current_idx + 1})")
                        else:
                            logger.info(f"[NAV] Current labeled image not found in history or is oldest")
                    else:
                        # We're on an in-progress/new image - get the most recent labeled image
                        prev_entry = prev_hist[0]  # Newest labeled image
                        has_remote_prev = True
                        logger.info(f"[NAV] On in-progress image, getting most recent labeled: {prev_entry.get('image_id')}")
                else:
                    logger.info(f"[NAV] No labeled images in history")
                    
            except Exception as e:
                logger.error(f"[NAV] Error getting user history: {e}")
                has_remote_prev = False

            disabled = not has_remote_prev
            logger.info(f"[NAV] Previous button disabled: {disabled}")

            if st.button("⬅️ Previous",
                         use_container_width=True,
                         disabled=disabled,
                         key="btn_prev"):
                logger.info(f"[NAV] Previous button clicked")
                clear_cache()

                if prev_entry:
                    image_id = prev_entry.get("image_id")
                    logger.info(f"[NAV] Loading previous image: {image_id}")
                    
                    if image_id:
                        try:
                            img_doc = repo.get_image_doc(image_id)
                        except AttributeError:
                            img_doc = None

                        if not img_doc:
                            img_doc = {
                                "image_id": image_id,
                                "status": "labeled",
                                "bb_url": prev_entry.get("bb_url", ""),
                            }

                        # Merge history data with image doc
                        merged_task = {**prev_entry, **img_doc}
                        st.session_state.current_task = merged_task
                        logger.info(f"[NAV] Set current_task to: {image_id} (status: {merged_task.get('status')})")
                        
                        # Clear _last_loaded_id to force reload
                        st.session_state._last_loaded_id = None
                        st.rerun()

        with nav_next:
            is_labeled_now = task.get("status") == "labeled"
            # Additional check: if this is a review image, user must save before proceeding
            is_review_image = task.get("qa_status") == "review"
            can_proceed_next = is_labeled_now and not is_review_image
            logger.info(f"[NAV] Next button check - Current: {current_image_id} (status: {current_status}), is_review: {is_review_image}, enabled: {can_proceed_next}")
            
            if st.button("➡️ Next",
                         use_container_width=True,
                         disabled=not can_proceed_next,
                         key="btn_next"):
                logger.info(f"[NAV] Next button clicked")
                
                # ------------------------------------------------------------------
                # Next navigation logic
                # ------------------------------------------------------------------
                next_task: dict | None = None

                if task.get("status") == "labeled":
                    # ---- Case A: we're on a labeled image – get the *next* labeled image ----
                    try:
                        hist = repo.get_user_history(st.session_state.username, limit=200)
                        logger.info(f"[NAV] Retrieved {len(hist)} labeled images for next navigation")
                    except Exception as e:
                        logger.error(f"[NAV] Error getting history for next: {e}")
                        hist = []

                    if hist:
                        # History is ordered DESCENDING (newest first)
                        # So to get "next" (newer), we need to go to a lower index
                        current_idx = None
                        for idx, entry in enumerate(hist):
                            if entry.get("image_id") == task["image_id"]:
                                current_idx = idx
                                break
                        
                        if current_idx is not None and current_idx > 0:
                            # Found current image, get the previous one (newer timestamp)
                            next_entry = hist[current_idx - 1]
                            image_id = next_entry.get("image_id")
                            logger.info(f"[NAV] Found next labeled image: {image_id} (idx: {current_idx - 1})")
                            
                            if image_id:
                                try:
                                    doc = repo.get_image_doc(image_id)
                                except AttributeError:
                                    doc = None
                                if not doc:
                                    doc = {
                                        "image_id": image_id,
                                        "status": "labeled",
                                        "bb_url": next_entry.get("bb_url", ""),
                                    }
                                next_task = {**next_entry, **doc}
                        else:
                            logger.info(f"[NAV] Current image not found in history or is newest")

                # ---- Case B: no further labeled images – fall back to in-progress queue ----
                if next_task is None:
                    logger.info(f"[NAV] No next labeled image, checking in-progress queue")
                    # Use any preloaded history_stack first (these are usually in-progress)
                    hist_stack: list = st.session_state.get("history_stack", [])
                    logger.info(f"[NAV] History stack has {len(hist_stack)} items")
                    
                    # Remove any labeled entries from the stack
                    while hist_stack and hist_stack[0].get("status") == "labeled":
                        removed = hist_stack.pop(0)
                        logger.info(f"[NAV] Removed labeled entry from stack: {removed.get('image_id')}")
                    
                    if hist_stack:
                        next_task = hist_stack.pop(0)
                        st.session_state.history_stack = hist_stack
                        logger.info(f"[NAV] Got in-progress task from stack: {next_task.get('image_id')}")

                # ---- Case C: still nothing – ask repo for a brand-new task ----
                if next_task is None:
                    logger.info(f"[NAV] No in-progress tasks, getting new task from repo")
                    next_task = repo.get_next_task(st.session_state.username)
                    if next_task:
                        logger.info(f"[NAV] Got new task from repo: {next_task.get('image_id')}")
                    else:
                        logger.info(f"[NAV] No new tasks available")

                # ------------------------------------------------------------------
                # Update session & cache, no Firestore writes here
                # ------------------------------------------------------------------
                if next_task:
                    clear_cache()
                    st.session_state.current_task = next_task
                    st.session_state._last_loaded_id = None  # Force reload
                    logger.info(f"[NAV] Set current_task to: {next_task.get('image_id')} (status: {next_task.get('status')})")
                    st.rerun()
                else:
                    logger.info(f"[NAV] No next task available")
                    st.warning("No more images available")

        # ------------------------------------------------------------------
        # Debug info for admins
        # ------------------------------------------------------------------
        if is_admin:
            with st.expander("🔍 Debug Info", expanded=False):
                st.write(f"**Mode:** {admin_mode}")
                if admin_mode == "Review":
                    st.write(f"**Review Target:** {review_target_user}")
                    last_action = st.session_state.get("last_review_action")
                    if last_action:
                        st.write("**Last Review Action:**")
                        st.json(last_action)
                    else:
                        st.write("**Last Review Action:** None")
                
                st.write(f"**Current Task ID:** {task.get('image_id', 'None')}")
                st.write(f"**Task Status:** {task.get('status', 'None')}")
                st.write(f"**QA Status:** {task.get('qa_status', 'None')}")

        # ------------------------------------------------------------------
        # QA feedback / confirmation banners (positioned after navigation)
        # ------------------------------------------------------------------
        if task.get("qa_status") == "review":
            fb = (task.get("qa_feedback") or "").strip()
            if fb:
                st.warning(f"✍️ **Reviewer feedback:**\n\n{fb}")
            else:
                st.info("🔄 **Reviewer has requested changes** – please update the labels.")
        elif task.get("qa_status") == "confirmed":
            st.success("✅ **Labels have been confirmed.** This image is read-only.")
            confirmed_readonly = True

        # Current Selections Display (from legacy)
        sel_left, sel_mid, sel_right = st.columns([1, 4, 1], gap="small")
        complete = ui.get_complete_chains()

        # Get features from current session state (after restoration)
        feats_by_loc = {}
        for loc in sorted(leaves):
            feats = []
            if loc in ui.FEATURE_TAXONOMY:
                for category in ui.FEATURE_TAXONOMY[loc]:
                    sel_key = f"sel_{loc}_{category}"
                    na_key = f"na_{loc}_{category}"
                    
                    # Get current state
                    selections = st.session_state.get(sel_key, [])
                    is_na = st.session_state.get(na_key, False)
                    
                    # If N/A is checked, don't show any features for this category
                    if not is_na:
                        # Add category context to features for better display
                        for feature in selections:
                            if feature == "None":
                                feats.append(f"{category}: None")
                            else:
                                feats.append(f"{category}: {feature}")
            feats_by_loc[loc] = feats

        groups = list(feats_by_loc.items())

        with sel_mid:
            with st.expander("📋 Current Selections", expanded=True):
                # ------------------------------------------------------------------
                # 3-column grid: Locations | Features | Attributes
                # ------------------------------------------------------------------
                loc_col, feat_col, attr_col = st.columns([1, 1, 1], gap="medium")

                # ---- Locations ----
                with loc_col:
                    st.subheader("Locations")
                    if complete:
                        for chain in complete:
                            st.write("• " + " → ".join(chain))
                    else:
                        st.write("_(none selected)_")

                # ---- Features ----
                with feat_col:
                    st.subheader("Features")
                    
                    # Hash current selections for change detection
                    feature_hash = "|".join(
                        f"{loc}:{','.join(sorted(feats))}" for loc, feats in sorted(feats_by_loc.items()) if feats
                    )

                    if not feature_hash:
                        st.write("_(no features yet)_")
                    else:
                        # Rebuild table only if selections changed
                        if cache_entry.get('feature_table_hash') != feature_hash:
                            logger.info("[PERF] feature table rebuilt")
                            headers = "".join(
                                f"<th style='text-align:left; padding:4px'>{loc}</th>"
                                for loc, feats in groups if feats
                            )
                            filtered_groups = [(loc, feats) for loc, feats in groups if feats]
                            max_rows = max(len(feats) for _, feats in filtered_groups)
                            rows_html = ""
                            for i in range(max_rows):
                                row_cells = ""
                                for _, feats in filtered_groups:
                                    if i < len(feats):
                                        row_cells += (
                                            "<td style='text-align:left; padding:2px'>"
                                            f"• {feats[i]}"
                                            "</td>"
                                        )
                                    else:
                                        row_cells += "<td></td>"
                                rows_html += f"<tr>{row_cells}</tr>"

                            table_html = (
                                "<table style='width:100%; border-collapse: collapse;'>"
                                f"<tr>{headers}</tr>"
                                f"{rows_html}"
                                "</table>"
                            )

                            cache_entry['feature_table_html'] = table_html
                            cache_entry['feature_table_hash'] = feature_hash
                        else:
                            table_html = cache_entry['feature_table_html']

                        st.markdown(table_html, unsafe_allow_html=True)

                # ---- Attributes ----
                with attr_col:
                    st.subheader("Attributes")

                    # Build hash for attribute selections
                    attr_hash = hash(str(st.session_state.location_attributes))

                    if not st.session_state.location_attributes:
                        st.write("_(no attributes yet)_")
                    else:
                        if cache_entry.get('attr_table_hash') != attr_hash:
                            logger.info("[PERF] attribute table rebuilt")
                            attr_table_html = "<table style='width:100%; border-collapse: collapse;'>"
                            attr_table_html += "<tr><th style='text-align:left; padding:4px'>Location</th><th style='text-align:left; padding:4px'>Attribute</th><th style='text-align:left; padding:4px'>Value</th></tr>"

                            for location_key, attrs in st.session_state.location_attributes.items():
                                if not attrs:
                                    continue
                                loc_parts = location_key.split('_', 2)
                                if len(loc_parts) < 3:
                                    continue
                                location_name = loc_parts[2]

                                for attr, value in attrs.items():
                                    if value:
                                        attr_display = attr.replace("_", " ").title()
                                        attr_table_html += (
                                            f"<tr><td style='text-align:left; padding:2px'>{location_name}</td>"
                                            f"<td style='text-align:left; padding:2px'>{attr_display}</td>"
                                            f"<td style='text-align:left; padding:2px'>{value}</td></tr>"
                                        )

                            attr_table_html += "</table>"

                            cache_entry['attr_table_html'] = attr_table_html
                            cache_entry['attr_table_hash'] = attr_hash
                        st.markdown(cache_entry['attr_table_html'], unsafe_allow_html=True)

                # ---------------- Condition Scores ------------------
                st.subheader("Condition Scores")

                cond = st.session_state.condition_scores  # type: ignore[attr-defined]

                # Build stable hash string so equality survives reruns
                na_flag = bool(st.session_state.get("property_condition_na", False))
                prop_score_val = round(cond["property_condition"], 3)
                quality_val = cond["quality_of_construction"] or ""
                improvement_val = cond["improvement_condition"] or ""

                cs_state = f"{na_flag}|{prop_score_val:.3f}|{quality_val}|{improvement_val}"

                if cache_entry.get('cond_scores_hash') != cs_state:
                    logger.info("[PERF] condition table rebuilt")
                    scores_table_html = "<table style='width:100%; border-collapse: collapse;'>"
                    scores_table_html += "<tr><th style='text-align:left; padding:4px'>Category</th><th style='text-align:left; padding:4px'>Score/Selection</th></tr>"

                    prop_score = st.session_state.condition_scores['property_condition']
                    if st.session_state.get("property_condition_na", False):
                        scores_table_html += (
                            "<tr><td style='text-align:left; padding:2px'>Property Condition</td>"
                            "<td style='text-align:left; padding:2px'>N/A (N/A)</td></tr>"
                        )
                    else:
                        score_interpretation = {
                            **{k: "Excellent" for k in [round(x/10,1) for x in range(10,20)]},
                            **{k: "Good" for k in [round(x/10,1) for x in range(20,30)]},
                            **{k: "Average" for k in [round(x/10,1) for x in range(30,40)]},
                            **{k: "Fair" for k in [round(x/10,1) for x in range(40,50)]},
                            5.0: "Poor",
                        }
                        closest = min(score_interpretation, key=lambda x: abs(x - prop_score))
                        interp = score_interpretation[closest]
                        scores_table_html += (
                            f"<tr><td style='text-align:left; padding:2px'>Property Condition</td>"
                            f"<td style='text-align:left; padding:2px'>{prop_score:.3f} ({interp})</td></tr>"
                        )

                    quality_display = st.session_state.condition_scores["quality_of_construction"] or "Not Selected"
                    scores_table_html += (
                        f"<tr><td style='text-align:left; padding:2px'>Quality of Construction</td>"
                        f"<td style='text-align:left; padding:2px'>{quality_display}</td></tr>"
                    )

                    improvement_display = st.session_state.condition_scores["improvement_condition"] or "Not Selected"
                    scores_table_html += (
                        f"<tr><td style='text-align:left; padding:2px'>Improvement Condition</td>"
                        f"<td style='text-align:left; padding:2px'>{improvement_display}</td></tr>"
                    )

                    scores_table_html += "</table>"

                    cache_entry['cond_scores_html'] = scores_table_html
                    cache_entry['cond_scores_hash'] = cs_state

                st.markdown(cache_entry['cond_scores_html'], unsafe_allow_html=True)

        # Unified Action Buttons Row: Flag | Clear | Save | Refresh (moved right after Current Selections)
        current_validation = ui.can_move_on()  # refresh validation state
        flag_col, clear_col, save_col, refresh_col = st.columns([1, 1, 1, 1], gap="small")

        # Flag / Unflag
        with flag_col:
            flag_text = "🚩 Unflag" if st.session_state.flagged else "🚩 Flag for Review"
            flag_type = "secondary" if st.session_state.flagged else "primary"
            if st.button(flag_text, type=flag_type, use_container_width=True, key="btn_flag"):
                st.session_state.flagged = not st.session_state.flagged
                st.rerun()

        # Clear Labels
        with clear_col:
            if st.button("🗑️ Clear Labels", use_container_width=True, key="btn_clear"):
                ui.reset_session_state_to_defaults()
                st.session_state.skip_label_loading = True
                st.rerun()

        # Save Labels
        with save_col:
            if st.button("💾 Save Labels", type="primary", use_container_width=True,
                         disabled=not current_validation, key="btn_save"):
                payload = _build_payload()
                logger.info(f"[FS] Saving labels for image {task['image_id']}")
                repo.save_labels(task["image_id"], payload, st.session_state.username)
                update_cache_with_saved_data(task["image_id"], payload)
                # Mark as labeled for downstream logic
                task["status"] = "labeled"
                st.session_state.current_task = task  # Update the session state with the new status
                st.success("Saved ✔︎")
                st.rerun()

        # Refresh from Firestore
        with refresh_col:
            if st.button("🔄 Refresh", type="secondary", use_container_width=True, key="btn_refresh"):
                clear_cache()
                st.session_state._last_loaded_id = None  # force reload on rerun
                st.rerun()

        # Main labeling UI components
        col_left, col_mid, col_right = st.columns([1.0, 1.0, 1.0])
        with col_left:
            ui.build_dropdown_cascade_ui()
        with col_mid:
            ui.build_feature_ui()
        with col_right:
            ui.build_contextual_attribute_ui()

        st.markdown("---")
        ui.build_condition_scores_ui()

        # Notes section
        st.subheader("📝 Additional Information")
        st.session_state.notes = st.text_area("Notes", value=st.session_state.notes, height=80)

        # Go-to-page navigation is an admin-only feature
        final_validation = ui.can_move_on()

        if is_admin:
            go_left, go_mid, go_right = st.columns([3, 1, 3], gap="small")
            with go_mid:
                goto = st.number_input(
                    "Go to page",
                    min_value=1,
                    max_value=1000,  # Reasonable upper bound
                    value=1,
                    step=1,
                    key="goto_input_bottom",
                    label_visibility="collapsed"
                )
                if st.button(
                    "🔎 Go",
                    use_container_width=True,
                    disabled=not final_validation,
                    key="btn_goto_bottom",
                ):
                    # Save current task first
                    payload = _build_payload()
                    logger.info(f"[FS] Saving labels for image {task['image_id']} (Go)")
                    repo.save_labels(task["image_id"], payload, st.session_state.username)
                    # Update cache with saved data
                    update_cache_with_saved_data(task["image_id"], payload)
                    # Clear cache and load next image
                    clear_cache()
                    st.session_state.current_task = None  # triggers get_next_task on rerun
                    st.rerun()

    # Admin-only debug panels ---------------------------------------------------
    if is_admin:
        # Cache debug panel
        with st.container():
            with st.expander("🗄️ Cache Debug", expanded=False):
                st.json(cache_debug_info["cache"], expanded=False)
                st.write("**Cache Hit:**", cache_debug_info["hit"])
                c = cache_debug_info["cache"]
                if c.get('cached_at'):
                    st.write("**Cache Age:**", f"{time.time() - c['cached_at']:.1f}s")
                if c.get('last_accessed'):
                    st.write("**Last Accessed:**", f"{time.time() - c['last_accessed']:.1f}s ago")

        # Task document debug dump
        st.markdown("---")
        st.markdown(f"**Debug - Task keys:** `{list(task.keys())}`")
        st.markdown(f"**Debug - bb_url:** `{repr(task.get('bb_url'))}`")
        
        potential_url_fields = ['backblaze_url', 'image_url', 'url', 'path', 'file_path', 'storage_path']
        for field in potential_url_fields:
            if field in task:
                st.markdown(f"**Debug - {field}:** `{repr(task.get(field))}`")


# ---------------------------------------------------------------------------
# Helper: build centered HTML when base64 already available (no re-encode)
# ---------------------------------------------------------------------------


def _html_image_from_b64(
    img_b64: str,
    img_width: int,
    img_height: int,
    source: str,
    image_id: str,
    *,
    admin: bool = False,
) -> str:
    """Return HTML snippet using a pre-computed base64 string."""

    # ------------------------------------------------------------------
    # FORCED IMAGE DIMENSIONS  (set to None to fall back to old scaling)
    # ------------------------------------------------------------------
    TARGET_W: int | None = 1000  # e.g. 1200 px wide
    TARGET_H: int | None = 500   # e.g. 700  px tall

    if TARGET_W is not None and TARGET_H is not None:
        # Hard-override, ignore original aspect ratio
        disp_w, disp_h = TARGET_W, TARGET_H
    else:
        # ------- legacy min/max scaling logic (kept for reference) -------
        # MIN_W, MAX_W, MIN_H, MAX_H = 400, 800, 400, 800
        # disp_w, disp_h = img_width, img_height
        # if disp_w < MIN_W:
        #     f = MIN_W / disp_w
        #     disp_w, disp_h = MIN_W, int(disp_h * f)
        # if disp_w > MAX_W:
        #     f = MAX_W / disp_w
        #     disp_w, disp_h = MAX_W, int(disp_h * f)
        # if disp_h > MAX_H:
        #     f = MAX_H / disp_h
        #     disp_h, disp_w = MAX_H, int(disp_w * f)
        # if disp_h < MIN_H:
        #     f = MIN_H / disp_h
        #     disp_h, disp_w = MIN_H, int(disp_w * f)
        disp_w, disp_h = img_width, img_height  # no scaling if both targets None

    meta = (
        f"<p style='text-align:center;margin-top:10px;color:#666;'>"
        f"{image_id} - {img_width}×{img_height} → {disp_w}×{disp_h} (via {source})"
        f"</p>"
    ) if admin else ""

    return (
        f"<div style='display:flex;justify-content:center;align-items:center;width:100%;margin:0 0 2px 0;'>"
        f"<div style='text-align:center;'>"
        f"<img src='data:image/jpeg;base64,{img_b64}' "
        f"style='width:{disp_w}px;height:{disp_h}px;display:block;margin:0 auto;object-fit:contain;' />"
        f"{meta}"
        f"</div></div>"
    )


# Add global build payload helper before main definition
def _build_payload() -> dict:
    """Collect current UI selections into a Firestore-ready payload.

    Moved to module scope so it is defined before `main()` references it.
    Uses only `st.session_state`, so no args are required.
    """

    import ui_components as ui  # local import to avoid circular at top
    import streamlit as st

    # --- spatial labels ---
    spatial_list = ui.chains_to_label_strings()

    # --- feature labels ---
    feature_list: list[str] = []
    leaves = ui.get_leaf_locations()
    for loc in leaves:
        if loc not in ui.FEATURE_TAXONOMY:
            continue
        for category in ui.FEATURE_TAXONOMY[loc]:
            sel_key = f"sel_{loc}_{category}"
            na_key = f"na_{loc}_{category}"
            
            # Get current state
            selections = st.session_state.get(sel_key, [])  # type: ignore[arg-type]
            is_na = st.session_state.get(na_key, False)
            
            # If N/A is checked, don't save anything for this category
            if is_na:
                continue
            
            # If no selections are made and "None" is available as an option, save "None"
            if not selections and "None" in ui.FEATURE_TAXONOMY[loc][category]:
                feature_list.append(f"{loc}:{category}:None")
            else:
                # Save the actual selections with location and category context
                for feature in selections:
                    feature_list.append(f"{loc}:{category}:{feature}")

    # --- contextual attributes ---
    attributes_map: dict[str, str] = {}
    for attr in ui.LOCATION_TAXONOMY.get("attributes", {}):
        # Normalize attribute name (replace spaces with underscores)
        normalized_attr = attr.replace(" ", "_")
        
        # Find the first location that has this attribute set
        # Since we now have one set of attributes per image, we just need the first value
        for loc_key, attrs in st.session_state.location_attributes.items():  # type: ignore[attr-defined]
            if attr in attrs and attrs[attr]:  # Has a value (including "N/A")
                if attrs[attr] == "N/A":
                    # Save N/A as null in the database
                    attributes_map[normalized_attr] = None
                else:
                    # Save the simple value (no location prefix)
                    attributes_map[normalized_attr] = attrs[attr]
                break  # Take the first value since all locations should have the same value

    # --- condition scores ---
    cond = st.session_state.condition_scores  # type: ignore[attr-defined]
    condition_scores = {
        "property_condition": None if st.session_state.get("property_condition_na", False) else cond["property_condition"],
        "quality_of_construction": None if cond["quality_of_construction"] == "N/A" else cond["quality_of_construction"],
        "improvement_condition": None if cond["improvement_condition"] == "N/A" else cond["improvement_condition"],
    }

    return {
        "notes": st.session_state.notes,
        "flagged": st.session_state.flagged,
        "schema_version": 1,
        "labeled_by": st.session_state.get("username", ""),
        "spatial_labels": spatial_list,  # list[str]
        "feature_labels": sorted(feature_list),  # list[str] with format "Location:Category:Feature"
        "attributes": attributes_map,
        "condition_scores": condition_scores,
    }


# ---------------------------------------------------------------------------
# Global UI tweaks – compact layout
# ---------------------------------------------------------------------------


def _inject_compact_css() -> None:
    """Add a small CSS payload that shrinks default paddings & fonts."""
    st.markdown(
        """
        <style>
        /* tighten global vertical rhythm */
        section[data-testid="stVerticalBlock"] { padding-top:0.25rem;padding-bottom:0.25rem; }
        /* make headers & labels slimmer */
        h1,h2,h3,h4,h5,h6,label,p,span,div { font-size:0.85rem !important; }
        /* remove empty spacers Streamlit adds between widgets */
        div[data-testid="stSpacer"] { height:0rem !important; }
        /* cut the extra top padding around sliders */
        div[data-testid="stSlider"] > div:first-child { padding-top:0rem; }
        /* NEW: Pull overall content closer to the top */
        .block-container { padding-top:0.5rem !important; padding-bottom:0.5rem !important; }
        header[data-testid="stHeader"] { height:0rem; padding:0rem; }
        
        /* Sticky header styles */
        .sticky-header {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            z-index: 1000;
            background: var(--background-color, #fff);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 1rem 1rem 0 1rem; /* no bottom padding */
            margin: 0;
            border-bottom: 1px solid rgba(0,0,0,0.1);
        }
        .header-row { display:flex; align-items:baseline; gap:1rem; flex-wrap:wrap; }
        .sticky-header-fade {
            position: absolute;
            left: 0; right: 0; bottom: 0;
            height: 8px; /* even shorter fade */
            background: linear-gradient(to bottom, rgba(255,255,255,0.95) 60%, rgba(255,255,255,0));
            pointer-events: none;
        }
        /* Dark mode support for sticky header */
        @media (prefers-color-scheme: dark) {
            .sticky-header {
                background: var(--background-color, #0e1117);
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }
            .sticky-header-fade {
                background: linear-gradient(to bottom, rgba(14,17,23,0.95) 60%, rgba(14,17,23,0));
            }
        }
        /* inline code badge */
        .code-inline { font-family: monospace; background: rgba(135,131,120,0.15); padding:2px 4px; border-radius:4px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sticky_header(image_html: str, username: str, is_admin: bool = False, repo_mode: str = "", task: dict = None):
    """Render the title, user info, and image in a sticky header container."""
    # Build single-line info row to save vertical space
    info_parts = [
        "<span style='font-weight:600;'>Logged in as:</span> "
        f"<span class='code-inline'>{username}</span>"
    ]

    if is_admin and task:
        info_parts.extend([
            "| <span style='font-weight:600;'>Repo mode:</span> ",
            f"<span class='code-inline'>{repo_mode}</span>",
            "| <span style='font-weight:600;'>image_id:</span> ",
            f"<span class='code-inline'>{task['image_id']}</span>",
            "| <span style='font-weight:600;'>status:</span> ",
            f"<span class='code-inline'>{task['status']}</span>",
        ])

    info_html = "".join(info_parts)

    st.markdown(
        f"""
        <div class="sticky-header">
            <div class="header-row">
                <h1 style="margin:0;">🏠 Property Image Labeling Tool – prototype</h1>
                <div style="font-size:0.85rem;">{info_html}</div>
            </div>
            {image_html}
            <div class="sticky-header-fade"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Helper: compute displayed image height (mirrors _html_image_from_b64 logic)
# ---------------------------------------------------------------------------

def _compute_display_height(img_width: int, img_height: int) -> int:
    """Calculate the height the image will be shown at after the scaling rules.

    This mirrors the logic in `_html_image_from_b64` so we can derive an accurate
    spacer value for the sticky header.
    """
    TARGET_H: int | None = 500  # keep in sync with _html_image_from_b64

    if TARGET_H is not None:
        return TARGET_H

    # Legacy scaling path (commented for reference)
    # MIN_W, MAX_W, MIN_H, MAX_H = 800, 1200, 800, 1200
    # disp_w, disp_h = img_width, img_height
    # if disp_w < MIN_W:
    #     f = MIN_W / disp_w
    #     disp_w, disp_h = MIN_W, int(disp_h * f)
    # if disp_w > MAX_W:
    #     f = MAX_W / disp_w
    #     disp_w, disp_h = MAX_W, int(disp_h * f)
    # if disp_h > MAX_H:
    #     f = MAX_H / disp_h
    #     disp_h, disp_w = MAX_H, int(disp_w * f)
    # if disp_h < MIN_H:
    #     f = MIN_H / disp_h
    #     disp_h, disp_w = MIN_H, int(disp_w * f)
    # return disp_h

    return img_height  # fallback: original height


# ---------------------------------------------------------------------------
# Helper: inject dynamic spacer so widgets render below sticky header
# ---------------------------------------------------------------------------

def _inject_dynamic_spacer(pixels: int) -> None:
    """Add CSS that offsets Streamlit's content by *pixels* so it starts below the header."""
    st.markdown(
        f"<style>div.block-container{{padding-top:{pixels}px !important;}}</style>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main() 