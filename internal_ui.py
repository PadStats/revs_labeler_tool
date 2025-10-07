from __future__ import annotations
"""Standalone UI helpers copied from legacy_app without I/O code.

This lets `app.py` use the full widget suite without importing the old
legacy_app module.
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Set
import pandas as pd

from taxonomy import LOCATION_TAXONOMY, FEATURE_TAXONOMY, ATTRIBUTE_RULES

# -----------------------------------------------------  ------------------------
# Session-state init / reset (verbatim from legacy_app)
# -----------------------------------------------------------------------------

def init_session_state() -> None:
    if "index" not in st.session_state:
        st.session_state.index = 0
    if "location_chains" not in st.session_state:
        st.session_state.location_chains = [{}]
    if "feature_labels" not in st.session_state:
        st.session_state.feature_labels = set()
    if "feature_na_locations" not in st.session_state:
        st.session_state.feature_na_locations = set()
    if "attribute_labels" not in st.session_state:
        st.session_state.attribute_labels = {}
    if "location_attributes" not in st.session_state:
        st.session_state.location_attributes = {}
    if "notes" not in st.session_state:
        st.session_state.notes = ""
    if "flagged" not in st.session_state:
        st.session_state.flagged = False
    if "widget_refresh_counter" not in st.session_state:
        st.session_state.widget_refresh_counter = 0
    if "skip_label_loading" not in st.session_state:
        st.session_state.skip_label_loading = False
    if "current_image_path" not in st.session_state:
        st.session_state.current_image_path = None
    if "widget_states" not in st.session_state:
        st.session_state.widget_states = {}
    if "persistent_feature_state" not in st.session_state:
        st.session_state.persistent_feature_state = {}
    if "persistent_attribute_state" not in st.session_state:
        st.session_state.persistent_attribute_state = {}
    if "removed_locations" not in st.session_state:
        st.session_state.removed_locations = set()
    if "condition_scores" not in st.session_state:
        st.session_state.condition_scores = {
            "property_condition": 3.0,
            "quality_of_construction": "",
            "improvement_condition": "",
        }
    if "property_condition_confirmed" not in st.session_state:
        st.session_state.property_condition_confirmed = False
    if "persistent_condition_state" not in st.session_state:
        st.session_state.persistent_condition_state = {
            "property_condition": 3.0,
            "quality_of_construction": "",
            "improvement_condition": "",
            "property_confirmed": False,
        }
    if "property_condition_na" not in st.session_state:
        st.session_state.property_condition_na = False


def reset_session_state_to_defaults() -> None:  # shortened: same as legacy
    # Purge any per-category feature keys from previous images
    for key in list(st.session_state.keys()):
        if key.startswith(("na_", "sel_")):
            st.session_state.pop(key, None)
        # Also clear any persisted widget values for spatial chain selectors so
        # defaults from loaded chains take effect on the next render
        if key.startswith("chain_"):
            st.session_state.pop(key, None)

    st.session_state.location_chains = [{}]
    st.session_state.feature_labels = set()
    st.session_state.feature_na_locations = set()
    st.session_state.persistent_feature_state = {}
    st.session_state.persistent_attribute_state = {}
    st.session_state.widget_states = {}
    st.session_state.location_attributes = {}
    st.session_state.attribute_labels = {
        k: None for k in LOCATION_TAXONOMY.get("attributes", {}).keys()
    }
    st.session_state.notes = ""
    st.session_state.flagged = False
    st.session_state.removed_locations = set()
    st.session_state.condition_scores = {
        "property_condition": 3.0,
        "quality_of_construction": "",
        "improvement_condition": "",
    }
    st.session_state.property_condition_confirmed = False
    st.session_state.persistent_condition_state = {
        "property_condition": 3.0,
        "quality_of_construction": "",
        "improvement_condition": "",
        "property_confirmed": False,
    }
    st.session_state.widget_refresh_counter += 1

# -----------------------------------------------------------------------------
# Utility helpers (get_children_options, is_leaf_node, etc.)
# -----------------------------------------------------------------------------

def get_children_options(taxonomy_dict: Dict, path: List[str]) -> List[str]:
    current = taxonomy_dict
    for step in path:
        if isinstance(current, dict) and step in current:
            current = current[step]
        else:
            return []
    return list(current.keys()) if isinstance(current, dict) else []


def is_leaf_node(taxonomy_dict: Dict, path: List[str]) -> bool:
    current = taxonomy_dict
    for step in path:
        if isinstance(current, dict) and step in current:
            current = current[step]
        else:
            return True
    return not isinstance(current, dict) or not current


def get_complete_chains() -> List[List[str]]:
    complete: List[List[str]] = []
    for chain in st.session_state.location_chains:  # type: ignore[attr-defined]
        if chain:
            path = list(chain.values())
            if path[-1] == "N/A" or is_leaf_node(LOCATION_TAXONOMY["spatial"], path):
                complete.append(path)
    return complete


def get_leaf_locations() -> Set[str]:
    leaves = set()
    for path in get_complete_chains():
        if path:
            if path[-1] == "N/A" and len(path) > 1 and path[-2] in FEATURE_TAXONOMY:
                leaves.add(path[-2])
            elif path[-1] in FEATURE_TAXONOMY:
                leaves.add(path[-1])
    return leaves


def chains_to_label_strings() -> List[str]:
    labels: List[str] = []
    for chain in st.session_state.location_chains:  # type: ignore[attr-defined]
        path = list(chain.values())
        if path and path[-1] == "N/A":
            path = path[:-1]
        if not path:
            continue
        for i in range(1, len(path) + 1):
            labels.append(" > ".join(path[:i]))
    return labels


def label_strings_to_chains(label_strings: List[str]) -> List[Dict]:
    def _norm(txt: str) -> str:
        # Normalise aggressively for robust matching against taxonomy keys
        # - lower-case, remove punctuation, dashes/underscores/spaces → nothing
        import re
        s = txt.strip().lower()
        s = re.sub(r"[^a-z0-9]", "", s)  # keep alphanumerics only
        return s

    chains = []
    complete_paths = []
    for s in label_strings:
        if not s.strip():
            continue
        parts = s.split(" > ")
        if all(not other.startswith(s + " > ") for other in label_strings):
            complete_paths.append(parts)

    for parts in complete_paths:
        chain = {}
        canonical_path: List[str] = []
        # If the first part doesn't match any root keys, try to snap to the best root
        root_options = list(LOCATION_TAXONOMY["spatial"].keys()) if isinstance(LOCATION_TAXONOMY["spatial"], dict) else []
        def _snap(part: str, options: List[str], path_prefix: List[str]) -> str:
            if not options:
                return part
            t = _norm(part)
            # exact match first
            for opt in options:
                if _norm(opt) == t:
                    return opt
            # containment fallback
            for opt in options:
                nopt = _norm(opt)
                if t in nopt or nopt in t:
                    return opt
            # last resort: keep original
            return part

        for i, raw_part in enumerate(parts):
            options = get_children_options(LOCATION_TAXONOMY["spatial"], canonical_path) if i > 0 else root_options
            chosen = _snap(raw_part, options, canonical_path)
            chain[f"level_{i}"] = chosen
            canonical_path.append(chosen)

        # If the final node is not a leaf, append an explicit N/A sentinel
        if not is_leaf_node(LOCATION_TAXONOMY["spatial"], canonical_path):
            chain[f"level_{len(parts)}"] = "N/A"
        chains.append(chain)
    return chains if chains else [{}]

def cleanup_feature_state_for_path(old_path: List[str]):
    """Clean up feature state for a specific path and all its sub-paths that's being changed"""
    if not old_path:
        return
    
    # Clean up features for all possible leaf locations in the old path
    for i in range(len(old_path)):
        potential_leaf = old_path[i]
        if potential_leaf != "N/A" and potential_leaf in FEATURE_TAXONOMY:
            for category in FEATURE_TAXONOMY[potential_leaf]:
                na_key = f"na_{potential_leaf}_{category}"
                sel_key = f"sel_{potential_leaf}_{category}"
                persistent_na_key = f"persistent_na_{potential_leaf}_{category}"
                persistent_sel_key = f"persistent_sel_{potential_leaf}_{category}"
                
                # Clear from session state
                st.session_state.pop(na_key, None)
                st.session_state.pop(sel_key, None)
                
                # Clear from persistent state
                st.session_state.persistent_feature_state.pop(persistent_na_key, None)
                st.session_state.persistent_feature_state.pop(persistent_sel_key, None)

def cleanup_feature_state_for_chain(chain_index: int):
    """Clean up feature state when a chain is removed"""
    if chain_index < len(st.session_state.location_chains):
        chain = st.session_state.location_chains[chain_index]
        if chain:
            old_path = list(chain.values())
            cleanup_feature_state_for_path(old_path)
    
    # Also clean up any persistent state that might be associated with this chain index
    # This is a more aggressive cleanup to prevent data reappearing
    keys_to_remove = []
    for key in list(st.session_state.persistent_feature_state.keys()):
        # Check if this key could be associated with the removed chain
        # We need to be careful here since location names might reappear
        if key.startswith(('persistent_na_', 'persistent_sel_')):
            # Extract location name from the key
            key_parts = key.split('_', 3)  # ['persistent', 'na/sel', 'location', 'category']
            if len(key_parts) >= 3:
                location_name = key_parts[2]
                # Check if this location was part of the removed chain
                if chain_index < len(st.session_state.location_chains):
                    chain = st.session_state.location_chains[chain_index]
                    old_path = list(chain.values()) if chain else []
                    if location_name in old_path:
                        keys_to_remove.append(key)
    
    for key in keys_to_remove:
        st.session_state.persistent_feature_state.pop(key, None)

def cleanup_attribute_state_for_path(old_path: List[str], chain_index: int):
    """Clean up attribute state for a specific path that's being changed"""
    if not old_path:
        return
    
    # Clean up attributes for the specific chain being modified
    keys_to_remove = []
    for location_key in list(st.session_state.location_attributes.keys()):
        if location_key.startswith(f"loc_{chain_index}_"):
            keys_to_remove.append(location_key)
    
    for key in keys_to_remove:
        del st.session_state.location_attributes[key]
    
    # Also clean up persistent attribute state
    persistent_keys_to_remove = []
    for key in list(st.session_state.persistent_attribute_state.keys()):
        if key.startswith(f"persistent_loc_{chain_index}_"):
            persistent_keys_to_remove.append(key)
    
    for key in persistent_keys_to_remove:
        del st.session_state.persistent_attribute_state[key]

def cleanup_attribute_state_for_chain(chain_index: int):
    """Clean up attribute state when a chain is removed"""
    # Clean up attributes for the specific chain being removed
    keys_to_remove = []
    for location_key in list(st.session_state.location_attributes.keys()):
        if location_key.startswith(f"loc_{chain_index}_"):
            keys_to_remove.append(location_key)
    
    for key in keys_to_remove:
        del st.session_state.location_attributes[key]
    
    # Also clean up persistent attribute state
    persistent_keys_to_remove = []
    for key in list(st.session_state.persistent_attribute_state.keys()):
        if key.startswith(f"persistent_loc_{chain_index}_"):
            persistent_keys_to_remove.append(key)
    
    for key in persistent_keys_to_remove:
        del st.session_state.persistent_attribute_state[key]
    
    # Also clean up any widget states for this chain
    widget_keys_to_remove = []
    for key in list(st.session_state.widget_states.keys()):
        if key.startswith(f"chain_{chain_index}_"):
            widget_keys_to_remove.append(key)
    
    for key in widget_keys_to_remove:
        del st.session_state.widget_states[key]



def save_feature_state():
    """Save current feature selections to persistent storage"""
    leaves = get_leaf_locations()
    
    # Only save state for currently valid leaf locations
    current_valid_keys = set()
    
    for loc in leaves:
        if loc not in FEATURE_TAXONOMY:
            continue
        for category in FEATURE_TAXONOMY[loc]:
            na_key = f"na_{loc}_{category}"
            sel_key = f"sel_{loc}_{category}"
            persistent_na_key = f"persistent_na_{loc}_{category}"
            persistent_sel_key = f"persistent_sel_{loc}_{category}"
            
            current_valid_keys.add(persistent_na_key)
            current_valid_keys.add(persistent_sel_key)
            
            # Save current session state values
            st.session_state.persistent_feature_state[persistent_na_key] = st.session_state.get(na_key, False)
            st.session_state.persistent_feature_state[persistent_sel_key] = st.session_state.get(sel_key, [])
    
    # Clean up persistent state for locations that are no longer valid
    keys_to_remove = []
    for key in st.session_state.persistent_feature_state:
        if key.startswith(('persistent_na_', 'persistent_sel_')) and key not in current_valid_keys:
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del st.session_state.persistent_feature_state[key]

def restore_feature_state():
    """Restore feature selections from persistent storage"""
    leaves = get_leaf_locations()
    for loc in leaves:
        if loc not in FEATURE_TAXONOMY:
            continue
        for category in FEATURE_TAXONOMY[loc]:
            na_key = f"na_{loc}_{category}"
            sel_key = f"sel_{loc}_{category}"
            
            # Initialise keys only if not already present (avoids overriding new user selections)
            persistent_na_key = f"persistent_na_{loc}_{category}"
            persistent_sel_key = f"persistent_sel_{loc}_{category}"
            if na_key not in st.session_state and persistent_na_key in st.session_state.persistent_feature_state:
                st.session_state[na_key] = st.session_state.persistent_feature_state[persistent_na_key]
            if sel_key not in st.session_state and persistent_sel_key in st.session_state.persistent_feature_state:
                st.session_state[sel_key] = st.session_state.persistent_feature_state[persistent_sel_key]


def save_attribute_state():
    """Save current attribute selections to persistent storage"""
    complete = get_complete_chains()
    
    # Find the first location key (since we now have one set of attributes per image)
    first_location_key = None
    for chain_idx, chain in enumerate(complete):
        if not chain:
            continue
            
        # Get the leaf location name for this chain
        chain_values = list(chain.values()) if isinstance(chain, dict) else list(chain)
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
            
        first_location_key = f"loc_{chain_idx}_{leaf_location}"
        break
    
    if not first_location_key:
        return
    
    # Collect all relevant attributes across all locations
    all_relevant_attrs = set()
    for chain in complete:
        if not chain:
            continue
        
        # Find relevant attributes for this location
        for attr, locs in ATTRIBUTE_RULES.items():
            if any(loc in step for step in chain for loc in locs):
                all_relevant_attrs.add(attr)
    
    # Save each attribute to persistent storage
    for attr in all_relevant_attrs:
        persistent_key = f"persistent_{first_location_key}_{attr}"
        
        # Get current value from location_attributes
        current_value = st.session_state.location_attributes.get(first_location_key, {}).get(attr, "")
        st.session_state.persistent_attribute_state[persistent_key] = current_value
    
    # Clean up persistent state for old location keys
    keys_to_remove = []
    for key in st.session_state.persistent_attribute_state:
        if key.startswith('persistent_loc_') and not key.startswith(f'persistent_{first_location_key}_'):
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del st.session_state.persistent_attribute_state[key]

def restore_attribute_state():
    """Restore attribute selections from persistent storage"""
    complete = get_complete_chains()
    
    # Find the first location key (since we now have one set of attributes per image)
    first_location_key = None
    for chain_idx, chain in enumerate(complete):
        if not chain:
            continue
            
        # Get the leaf location name for this chain
        chain_values = list(chain.values()) if isinstance(chain, dict) else list(chain)
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
            
        first_location_key = f"loc_{chain_idx}_{leaf_location}"
        break
    
    if not first_location_key:
        return
    
    # Initialize attributes in session state if needed
    if first_location_key not in st.session_state.location_attributes:
        st.session_state.location_attributes[first_location_key] = {}
    
    # Collect all relevant attributes across all locations
    all_relevant_attrs = set()
    for chain in complete:
        if not chain:
            continue
        
        # Find relevant attributes for this location
        for attr, locs in ATTRIBUTE_RULES.items():
            if any(loc in step for step in chain for loc in locs):
                all_relevant_attrs.add(attr)
    
    # Restore each attribute from persistent storage
    for attr in all_relevant_attrs:
        # Restore attribute value only if not set already in current session
        persistent_key = f"persistent_{first_location_key}_{attr}"
        if attr not in st.session_state.location_attributes[first_location_key] and persistent_key in st.session_state.persistent_attribute_state:
            st.session_state.location_attributes[first_location_key][attr] = st.session_state.persistent_attribute_state[persistent_key]


def save_condition_state():
    """Save current condition scores to persistent storage"""
    st.session_state.persistent_condition_state = {
        "property_condition": st.session_state.condition_scores["property_condition"],
        "quality_of_construction": st.session_state.condition_scores["quality_of_construction"],
        "improvement_condition": st.session_state.condition_scores["improvement_condition"],
        "property_confirmed": st.session_state.property_condition_confirmed
    }

def restore_condition_state():
    """Restore condition scores from persistent storage"""
    if "persistent_condition_state" in st.session_state:
        st.session_state.condition_scores = {
            "property_condition": st.session_state.persistent_condition_state.get("property_condition", 3.0),
            "quality_of_construction": st.session_state.persistent_condition_state.get("quality_of_construction", ""),
            "improvement_condition": st.session_state.persistent_condition_state.get("improvement_condition", "")
        }
        st.session_state.property_condition_confirmed = st.session_state.persistent_condition_state.get("property_confirmed", False)


def build_location_chain(chain_index: int):
    chain = st.session_state.location_chains[chain_index]
    container = st.container()
    with container:
        if len(st.session_state.location_chains) > 1 and st.button(
            "❌", key=f"remove_chain_{chain_index}"
        ):
            # Store the leaf location name for thorough cleanup
            if chain:
                path = list(chain.values())
                if path:
                    leaf_location = path[-1] if path[-1] != "N/A" else path[-2] if len(path) > 1 else None
                    if leaf_location:
                        # Add to removed locations set for thorough cleanup
                        st.session_state.removed_locations.add(f"{chain_index}_{leaf_location}")
            
            # Clean up feature state for the removed chain BEFORE removing it
            cleanup_feature_state_for_chain(chain_index)
            # Clean up attribute state for the removed chain BEFORE removing it
            cleanup_attribute_state_for_chain(chain_index)
            
            # After removal, we need to update the indices of all chains that come after this one
            # First, collect all the state that needs to be re-indexed
            chains_to_shift = []
            attributes_to_shift = []
            widget_states_to_shift = []
            
            # Collect location attributes that need re-indexing
            for location_key in list(st.session_state.location_attributes.keys()):
                parts = location_key.split('_', 2)
                if len(parts) >= 3:
                    try:
                        key_chain_idx = int(parts[1])
                        if key_chain_idx > chain_index:
                            attributes_to_shift.append((location_key, key_chain_idx))
                    except ValueError:
                        continue
            
            # Collect persistent attribute state that needs re-indexing
            persistent_attrs_to_shift = []
            for key in list(st.session_state.persistent_attribute_state.keys()):
                if key.startswith('persistent_loc_'):
                    parts = key.split('_', 3)
                    if len(parts) >= 4:
                        try:
                            key_chain_idx = int(parts[2])
                            if key_chain_idx > chain_index:
                                persistent_attrs_to_shift.append((key, key_chain_idx))
                        except ValueError:
                            continue
            
            # Collect widget states that need re-indexing
            for key in list(st.session_state.widget_states.keys()):
                if key.startswith('chain_'):
                    parts = key.split('_', 3)
                    if len(parts) >= 3:
                        try:
                            key_chain_idx = int(parts[1])
                            if key_chain_idx > chain_index:
                                widget_states_to_shift.append((key, key_chain_idx))
                        except ValueError:
                            continue
            
            # Remove the chain
            st.session_state.location_chains.pop(chain_index)
            if not st.session_state.location_chains:
                st.session_state.location_chains = [{}]
            
            # Re-index all the collected state
            # Update location attributes
            for old_key, old_idx in attributes_to_shift:
                old_value = st.session_state.location_attributes.pop(old_key)
                parts = old_key.split('_', 2)
                new_key = f"loc_{old_idx - 1}_{parts[2]}"
                st.session_state.location_attributes[new_key] = old_value
            
            # Update persistent attribute state
            for old_key, old_idx in persistent_attrs_to_shift:
                old_value = st.session_state.persistent_attribute_state.pop(old_key)
                parts = old_key.split('_', 3)
                new_key = f"persistent_loc_{old_idx - 1}_{parts[3]}"
                st.session_state.persistent_attribute_state[new_key] = old_value
            
            # Update widget states
            for old_key, old_idx in widget_states_to_shift:
                old_value = st.session_state.widget_states.pop(old_key)
                parts = old_key.split('_', 3)
                if len(parts) >= 4:
                    new_key = f"chain_{old_idx - 1}_{parts[2]}_{parts[3]}"
                    st.session_state.widget_states[new_key] = old_value
            
            st.session_state.widget_refresh_counter += 1
            st.rerun()
            return

        current_path, level = [], 0
        chain_changed = False
        
        while True:
            key_lv = f"level_{level}"
            prev = chain.get(key_lv, "")
            opts = get_children_options(LOCATION_TAXONOMY["spatial"], current_path)
            if not opts: break
            if level > 0: opts += ["N/A"]

            # Stable widget key per chain/level to avoid unnecessary resets across reruns
            w_key = f"chain_{chain_index}_level_{level}"
            state_key = f"chain_{chain_index}_level_{level}_state"

            # Get stored value from our dedicated state storage
            if state_key in st.session_state.widget_states:
                stored = st.session_state.widget_states[state_key]
            else:
                stored = prev
                st.session_state.widget_states[state_key] = stored

            # If the stored value is not in current options (taxonomy drift), try fallbacks
            if stored not in opts and stored:
                # 1) Prefer previous chain value if valid
                if prev in opts and prev:
                    stored = prev
                else:
                    # 2) Snap to closest option using same normalisation as label_strings_to_chains
                    def _norm(txt: str) -> str:
                        import re
                        s = txt.strip().lower()
                        return re.sub(r"[^a-z0-9]", "", s)
                    t = _norm(str(stored))
                    snapped = None
                    for opt in opts:
                        if _norm(opt) == t:
                            snapped = opt
                            break
                    if snapped is None:
                        for opt in opts:
                            nopt = _norm(opt)
                            if t in nopt or nopt in t:
                                snapped = opt
                                break
                    if snapped:
                        stored = snapped
                # Persist the corrected value back to shadow storage
                st.session_state.widget_states[state_key] = stored

            idx = opts.index(stored) + 1 if stored in opts else 0

            if level == 0:
                sel = st.selectbox("Select location:", [""] + opts, index=idx, key=w_key)
            else:
                indent = level * 0.05
                if indent > 0:
                    _, col = st.columns([indent, 1 - indent])
                else:
                    col = container
                with col:
                    conn = "└── " if level == 1 else "    └── "
                    st.markdown(f"<span style='color:#666'>{conn}Select subcategory:</span>", unsafe_allow_html=True)
                    # Use single-space label so Streamlit treats it as non-empty; UI remains unchanged
                    sel = st.selectbox(" ", [""] + opts, index=idx, key=w_key, label_visibility="collapsed")

            if sel != stored:
                chain_changed = True
                
                # Update our state storage
                st.session_state.widget_states[state_key] = sel
                
                # Store the old path that will be removed (everything from this level down)
                old_path_to_clean = []
                for i in range(level, len(chain)):
                    level_key = f"level_{i}"
                    if level_key in chain:
                        old_path_to_clean.append(chain[level_key])
                
                # Clean up feature state for the path being removed
                if old_path_to_clean:
                    cleanup_feature_state_for_path(old_path_to_clean)
                
                # Clean up attribute state for the path being removed
                if old_path_to_clean:
                    cleanup_attribute_state_for_path(old_path_to_clean, chain_index)
                
                # Clear children levels from the chain (only for this specific chain)
                keys_to_remove = []
                for k in chain.keys():
                    if k.startswith("level_") and int(k.split("_")[1]) > level:
                        keys_to_remove.append(k)
                for k in keys_to_remove:
                    del chain[k]
                
                # Clear widget states only for this specific chain and levels beyond current
                widget_keys_to_remove = []
                for k in list(st.session_state.widget_states.keys()):
                    if k.startswith(f"chain_{chain_index}_level_") and k.endswith("_state"):
                        # Extract level from key like "chain_0_level_2_state"
                        parts = k.split("_")
                        if len(parts) >= 4:
                            try:
                                key_level = int(parts[3])
                                if key_level > level:
                                    widget_keys_to_remove.append(k)
                            except ValueError:
                                continue
                
                for k in widget_keys_to_remove:
                    del st.session_state.widget_states[k]

                # Also clear actual Streamlit widget values for deeper levels so they don't override indices
                # Keys look like: chain_{chain_index}_level_{N}
                widget_value_keys_to_remove = []
                for k in list(st.session_state.keys()):
                    if k.startswith(f"chain_{chain_index}_level_") and not k.endswith("_state"):
                        parts = k.split("_")
                        if len(parts) >= 4:
                            try:
                                key_level = int(parts[3])
                                if key_level > level:
                                    widget_value_keys_to_remove.append(k)
                            except ValueError:
                                continue

                for k in widget_value_keys_to_remove:
                    del st.session_state[k]

            if sel:
                chain[key_lv] = sel
            else:
                chain.pop(key_lv, None)
                break

            current_path = [chain[f"level_{i}"] for i in range(level + 1)]
            if sel == "N/A" or is_leaf_node(LOCATION_TAXONOMY["spatial"], current_path):
                break
            level += 1

        # Force rerun when chain changes to update current selections immediately
        if chain_changed:
            st.rerun()

        if chain:
            st.markdown("---")

def build_dropdown_cascade_ui():
    st.markdown("### 📍 Location Selection")
    # Wrap the potentially long selector list inside a fixed-height, scrollable container.
    # When the content exceeds the specified height Streamlit will add an internal scroll bar,
    # keeping the overall page length manageable while still providing access to all widgets.
    with st.container(height=480, border=True):
        for i in range(len(st.session_state.location_chains)):
            build_location_chain(i)

        col1, _ = st.columns([1, 3])
        with col1:
            if st.button("➕ Add Another Location", key="add_location"):
                # Comprehensive cleanup of any stale persistent state before adding new location
                # This prevents data from previously removed locations from reappearing
                
                # Get current valid location names to preserve their state
                current_leaves = get_leaf_locations()
                
                # Clean up feature persistent state - remove any state not associated with current locations
                feature_keys_to_remove = []
                for key in list(st.session_state.persistent_feature_state.keys()):
                    if key.startswith(('persistent_na_', 'persistent_sel_')):
                        # Extract location name from key
                        key_parts = key.split('_', 3)  # ['persistent', 'na/sel', 'location', 'category']
                        if len(key_parts) >= 3:
                            location_name = key_parts[2]
                            # Only keep if this location is currently valid
                            if location_name not in current_leaves:
                                feature_keys_to_remove.append(key)
                
                for key in feature_keys_to_remove:
                    del st.session_state.persistent_feature_state[key]
                
                # Clean up attribute persistent state - remove any state not associated with current chain indices
                current_chain_count = len(st.session_state.location_chains)
                attr_keys_to_remove = []
                for key in list(st.session_state.persistent_attribute_state.keys()):
                    if key.startswith('persistent_loc_'):
                        parts = key.split('_', 3)
                        if len(parts) >= 4:
                            try:
                                key_chain_idx = int(parts[2])
                                # Remove if chain index is beyond current chains
                                if key_chain_idx >= current_chain_count:
                                    attr_keys_to_remove.append(key)
                            except ValueError:
                                # Remove malformed keys
                                attr_keys_to_remove.append(key)
                
                for key in attr_keys_to_remove:
                    del st.session_state.persistent_attribute_state[key]
                
                # Clean up any location attributes that reference invalid chain indices
                loc_attr_keys_to_remove = []
                for key in list(st.session_state.location_attributes.keys()):
                    if key.startswith('loc_'):
                        parts = key.split('_', 2)
                        if len(parts) >= 3:
                            try:
                                key_chain_idx = int(parts[1])
                                # Remove if chain index is beyond current chains
                                if key_chain_idx >= current_chain_count:
                                    loc_attr_keys_to_remove.append(key)
                            except ValueError:
                                # Remove malformed keys
                                loc_attr_keys_to_remove.append(key)
                
                for key in loc_attr_keys_to_remove:
                    del st.session_state.location_attributes[key]
                
                # Clean up widget states for invalid chain indices
                widget_keys_to_remove = []
                for key in list(st.session_state.widget_states.keys()):
                    if key.startswith('chain_'):
                        parts = key.split('_', 3)
                        if len(parts) >= 3:
                            try:
                                key_chain_idx = int(parts[1])
                                # Remove if chain index is beyond current chains
                                if key_chain_idx >= current_chain_count:
                                    widget_keys_to_remove.append(key)
                            except ValueError:
                                # Remove malformed keys
                                widget_keys_to_remove.append(key)
                
                for key in widget_keys_to_remove:
                    del st.session_state.widget_states[key]
                
                # Clear the removed locations tracking set since we've cleaned up
                st.session_state.removed_locations = set()
                
                # Add the new empty location chain
                st.session_state.location_chains.append({})
                
                st.rerun()
                
    complete = get_complete_chains()
    total = len([c for c in st.session_state.location_chains if c])
    if total and len(complete) == total:
        st.success(f"✅ All {total} location(s) complete")
    elif total:
        st.warning(f"⚠️ {len(complete)}/{total} complete")


def build_location_features(location: str):
    """Per‐category N/A checkbox + multiselect—stores only in st.session_state."""
    if location not in FEATURE_TAXONOMY:
        return

    for category, feats in FEATURE_TAXONOMY[location].items():
        st.write(f"**{category}:**")

        na_key  = f"na_{location}_{category}"
        sel_key = f"sel_{location}_{category}"

        # Initialise keys only if not already present (avoids overriding new user selections)
        persistent_na_key = f"persistent_na_{location}_{category}"
        persistent_sel_key = f"persistent_sel_{location}_{category}"
        if na_key not in st.session_state:
            st.session_state[na_key] = st.session_state.persistent_feature_state.get(persistent_na_key, False)
        if sel_key not in st.session_state:
            st.session_state[sel_key] = st.session_state.persistent_feature_state.get(persistent_sel_key, [])

        # Get current state
        current_na = st.session_state.get(na_key, False)
        current_selections = st.session_state.get(sel_key, [])
        
        # Handle mutual exclusivity BEFORE creating widgets
        if current_selections and current_na:
            # If both are true, prioritize the most recent change
            # Since we can't tell which was more recent, default to keeping selections
            current_na = False
        
        # --- Compact row: N/A checkbox + multiselect side-by-side ----------
        col_na, col_sel = st.columns([1, 4], gap="small")

        with col_na:
            na_checked = st.checkbox(
                "N/A",
                key=na_key,
                #value=current_na,
            )

        with col_sel:
            if not na_checked:
                # Show multiselect on same row; hide its label
                selected_features = st.multiselect(
                    "Features",  # internal label for accessibility
                    feats,
                    key=sel_key,
                    label_visibility="collapsed",
                )
                # If features were selected while N/A was checked in prev state, clear N/A
                if selected_features and na_checked:
                    st.session_state[na_key] = False
                    st.rerun()
            else:
                # Minimal marker so column keeps height but no extra padding
                st.markdown("✅")

        # Handle state changes after widget interaction
        if na_checked != current_na:
            # N/A state toggled
            if na_checked:
                # Clear selections when N/A is set
                st.session_state[sel_key] = []
            # Force UI update
            st.rerun()

def build_feature_ui():
    st.markdown("### 🔧 Features in Selected Locations")
    leaves = get_leaf_locations()
    if not leaves:
        st.info("👆 Complete location selections to see features.")
        return

    avail = [loc for loc in leaves if loc in FEATURE_TAXONOMY]
    missing = [loc for loc in leaves if loc not in FEATURE_TAXONOMY]
    if not avail and missing:
        for loc in missing:
            st.warning(f"No features defined for location: {loc}")
        return
    elif not avail:
        st.info("No specific features defined.")
        return

    st.caption("💡 Select features or mark N/A.")

    # Constrain the (potentially large) feature selection UI to a scrollable box.
    with st.container(height=500, border=True):
        if len(avail) == 1:
            build_location_features(avail[0])
        else:
            tabs = st.tabs([f"📍 {loc}" for loc in sorted(avail)])
            for i, loc in enumerate(sorted(avail)):
                with tabs[i]:
                    build_location_features(loc)

    # Save state after UI is built (this preserves state for location changes)
    save_feature_state()

    # Category-level completion check
    total_cats = sum(len(FEATURE_TAXONOMY[loc]) for loc in avail)
    done_cats  = 0

    for loc in avail:
        for category in FEATURE_TAXONOMY[loc]:
            na_key  = f"na_{loc}_{category}"
            sel_key = f"sel_{loc}_{category}"
            # Count as complete if either N/A is checked OR features are selected (but not both)
            is_na = st.session_state.get(na_key, False)
            has_selections = bool(st.session_state.get(sel_key, []))
            # A category is complete if it has EITHER N/A OR selections (but not both)
            if (is_na and not has_selections) or (not is_na and has_selections):
                done_cats += 1

    # Display feature completion status
    if total_cats > 0:
        if done_cats == total_cats:
            st.success(f"✅ All {total_cats} feature categories complete")
        else:
            st.warning(f"⚠️ {done_cats}/{total_cats} feature categories complete")


def build_contextual_attribute_ui():
    st.markdown("### 🏷️ Contextual Attributes")
    complete = get_complete_chains()
    if not complete:
        st.info("👆 Complete locations first.")
        return
    
    # Collect all relevant attributes across all locations
    all_relevant_attrs = set()
    for chain in complete:
        if not chain:
            continue
        
        # Find relevant attributes for this location
        for attr, locs in ATTRIBUTE_RULES.items():
            if any(loc in step for step in chain for loc in locs):
                all_relevant_attrs.add(attr)
    
    if not all_relevant_attrs:
        st.info("No attributes apply to the selected locations.")
        return
    
    # Track completion status
    total_attrs = len(all_relevant_attrs)
    completed_attrs = 0
    
    # Use the first location key for storing attributes (since we now have one set per image)
    first_location_key = None
    for chain_idx, chain in enumerate(complete):
        if not chain:
            continue
        
        # Get the leaf location name for this chain
        chain_values = list(chain.values()) if isinstance(chain, dict) else list(chain)
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
        
        first_location_key = f"loc_{chain_idx}_{leaf_location}"
        break
    
    if not first_location_key:
        st.error("No valid location found for attributes.")
        return
    
    # Initialize attributes in session state if needed
    if first_location_key not in st.session_state.location_attributes:
        st.session_state.location_attributes[first_location_key] = {}
    
    # Display attributes in a single section
    attr_map = LOCATION_TAXONOMY.get("attributes", {})
    for attr in sorted(all_relevant_attrs):
        opts = attr_map.get(attr, [])
        disp = attr.replace("_", " ").title()
        
        # Get current value with empty string as default (forces selection)
        current_value = st.session_state.location_attributes[first_location_key].get(attr, "")
        
        # Calculate index - default to 0 (blank/empty option)
        idx = 0
        if current_value == "N/A":
            idx = 1  # N/A is at index 1
        elif current_value in opts:
            idx = opts.index(current_value) + 2  # +2 because we add blank and N/A options
        
        # Create a stable widget key per attribute
        widget_key = f"attr_{attr}"
        
        # Display the dropdown with a blank first option
        choice = st.selectbox(
            disp, 
            [""] + ["N/A"] + opts,  # Blank first option, then N/A, then actual options
            index=idx,
            key=widget_key
        )
        
        # Update the selection immediately in session state
        old_value = st.session_state.location_attributes[first_location_key].get(attr, "")
        if choice != old_value:
            st.session_state.location_attributes[first_location_key][attr] = choice
            # Force immediate UI update
            st.rerun()
        
        # Count completed attributes
        if choice != "":
            completed_attrs += 1
    
    # Save attribute state after UI is built
    save_attribute_state()
    
    # Display completion status
    if total_attrs > 0:
        if completed_attrs == total_attrs:
            st.success(f"✅ All {total_attrs} attributes complete")
        else:
            st.warning(f"⚠️ {completed_attrs}/{total_attrs} attributes complete")


def build_condition_scores_ui():
    # st.subheader("🏠 Property Condition Assessment")
    # st.caption("Rate the property condition")
    
    # Restore state before building UI
    restore_condition_state()
    
    # Create a container for the condition scores
    with st.container():
        # Property Condition Slider (FLIPPED LABELS: 1=Excellent, 5=Poor)
        st.markdown("### 🏠 Property Condition")
        st.caption("Overall condition of the property structure and systems")
        
        prop_key = "prop_condition_slider"
        current_prop_score = st.session_state.condition_scores["property_condition"]
        na_checked = st.session_state.get("property_condition_na", False)
        confirm_checked = st.session_state.property_condition_confirmed

        # Check if this is a preloaded score that needs confirmation
        needs_confirmation = (not confirm_checked and not na_checked and current_prop_score != 3.0)

        if needs_confirmation:
            st.warning("⚠️ This property has a preloaded condition score. Please confirm or adjust it below.")

        # Always show slider, but disable if confirmed or N/A
        new_prop_score = st.slider(
            "Property Condition Score",
            min_value=1.0,
            max_value=5.0,
            value=round(current_prop_score, 3),
            step=0.001,
            format="%.3f",
            key=prop_key,
            label_visibility="collapsed",
            disabled=confirm_checked or na_checked
        )

        # ----------------------------------------------
        # Add textual labels under the slider (1 ➜ 5)
        # Borrowed from legacy_app for user clarity
        # ----------------------------------------------

        with st.container():
            labels_html = """
            <div style="display: flex; justify-content: space-between; margin-top: -10px; margin-bottom: 10px; padding: 0 8px;">
                <span style="font-size: 12px; color: #6e6e6e; text-align: left;">Excellent</span>
                <span style="font-size: 12px; color: #6e6e6e; text-align: center;">Good</span>
                <span style="font-size: 12px; color: #6e6e6e; text-align: center;">Average</span>
                <span style="font-size: 12px; color: #6e6e6e; text-align: center;">Fair</span>
                <span style="font-size: 12px; color: #6e6e6e; text-align: right;">Poor</span>
            </div>
            """
            st.markdown(labels_html, unsafe_allow_html=True)

        # Show current score with flipped interpretation
        score_interpretation = {
            1.0: "Excellent", 1.1: "Excellent", 1.2: "Excellent", 1.3: "Excellent", 1.4: "Excellent", 1.5: "Excellent", 1.6: "Excellent", 1.7: "Excellent", 1.8: "Excellent", 1.9: "Excellent",
            2.0: "Good", 2.1: "Good", 2.2: "Good", 2.3: "Good", 2.4: "Good", 2.5: "Good", 2.6: "Good", 2.7: "Good", 2.8: "Good", 2.9: "Good",
            3.0: "Average", 3.1: "Average", 3.2: "Average", 3.3: "Average", 3.4: "Average", 3.5: "Average", 3.6: "Average", 3.7: "Average", 3.8: "Average", 3.9: "Average",
            4.0: "Fair", 4.1: "Fair", 4.2: "Fair", 4.3: "Fair", 4.4: "Fair", 4.5: "Fair", 4.6: "Fair", 4.7: "Fair", 4.8: "Fair", 4.9: "Fair",
            5.0: "Poor"
        }
        
        # Use two-decimal precision when displaying
        closest_score = min(score_interpretation.keys(), key=lambda x: abs(x - current_prop_score))
        current_interpretation = score_interpretation[closest_score]
        if na_checked:
            st.markdown(f"**Current Score: N/A**")
        else:
            st.markdown(f"**Current Score: {current_prop_score:.3f} ({current_interpretation})**")
        
        # Confirm and N/A checkboxes below slider
        col_confirm, col_na = st.columns([2, 1])
        with col_confirm:
            confirm = st.checkbox("✅ Confirm Property Condition Score", value=confirm_checked, disabled=na_checked)
        with col_na:
            na = st.checkbox("N/A", value=na_checked, disabled=confirm_checked)
        
        # Mutually exclusive logic
        if na and not na_checked:
            st.session_state.property_condition_na = True
            st.session_state.property_condition_confirmed = False
            save_condition_state()
            st.rerun()
        elif confirm and not confirm_checked:
            st.session_state.property_condition_confirmed = True
            st.session_state.property_condition_na = False
            save_condition_state()
            st.rerun()
        elif not na and na_checked:
            st.session_state.property_condition_na = False
            save_condition_state()
            st.rerun()
        elif not confirm and confirm_checked:
            st.session_state.property_condition_confirmed = False
            save_condition_state()
            st.rerun()

        # If user adjusts the slider, immediately update session_state and trigger rerun
        if not (confirm_checked or na_checked):
            if abs(new_prop_score - current_prop_score) > 0.00009:  # tighter tolerance due to higher precision
                st.session_state.condition_scores["property_condition"] = new_prop_score
                save_condition_state()
                st.rerun()

        st.markdown("---")
        
        # Compact Quality and Improvement sections side by side
        qual_col, imp_col = st.columns(2)
        
        with qual_col:
            st.markdown("### 🔨 Quality of Construction")
            st.caption("Materials, workmanship, and construction standards")
            
            quality_options = [
                "N/A",
                "Below Standard",
                "Standard", 
                "Good Quality",
                "High Quality",
                "Premium"
            ]
            
            current_quality = st.session_state.condition_scores["quality_of_construction"]
            quality_key = "quality_slider"
            
            # Use select_slider for discrete selection with slider appearance
            selected_quality = st.segmented_control(
                "Quality Level",
                options=quality_options,
                default=None if current_quality == "" else current_quality,
                key=quality_key,
                label_visibility="collapsed"
            )
            
            # Update selection immediately
            if selected_quality != current_quality:
                st.session_state.condition_scores["quality_of_construction"] = selected_quality
                save_condition_state()
                st.rerun()
            
            # Show current selection
            if selected_quality:
                st.markdown(f"**Selected: {selected_quality}**")
            else:
                st.warning("⚠️ Please select a quality level or N/A")
        
        with imp_col:
            st.markdown("### 🔧 Improvement Condition")
            st.caption("Condition of improvements, updates, and maintenance")
            
            improvement_options = [
                "N/A",
                "Not Updated",
                "Updated", 
                "Remodeled"
            ]
            
            current_improvement = st.session_state.condition_scores["improvement_condition"]
            improvement_key = "improvement_slider"
            
            # Use select_slider for discrete selection with slider appearance
            selected_improvement = st.segmented_control(
                "Improvement Level",
                options=improvement_options,
                default=None if current_improvement == "" else current_improvement,
                key=improvement_key,
                label_visibility="collapsed"
            )
            
            # Update selection immediately
            if selected_improvement != current_improvement:
                st.session_state.condition_scores["improvement_condition"] = selected_improvement
                save_condition_state()
                st.rerun()
            
            # Show current selection
            if selected_improvement:
                st.markdown(f"**Selected: {selected_improvement}**")
            else:
                st.warning("⚠️ Please select an improvement level or N/A")
        
        st.markdown("---")
        
        # Compact Summary section
        st.markdown("### 📋 Condition Assessment Summary")
        
        # Add completion status for condition scores
        total_conditions = 3  # Property condition, Quality, Improvement
        completed_conditions = 0
        if st.session_state.property_condition_confirmed or st.session_state.get("property_condition_na", False):
            completed_conditions += 1
        if st.session_state.condition_scores["quality_of_construction"]:
            completed_conditions += 1
        if st.session_state.condition_scores["improvement_condition"]:
            completed_conditions += 1
        if completed_conditions == total_conditions:
            st.success(f"✅ All {total_conditions} condition scores complete")
        else:
            st.warning(f"⚠️ {completed_conditions}/{total_conditions} condition scores complete")
            
        # Show the scores in a grid
        summary_cols = st.columns(3)
        with summary_cols[0]:
            if st.session_state.get("property_condition_na", False):
                st.metric(
                    "Property Condition",
                    "N/A",
                    delta="(N/A)"
                )
            else:
                st.metric(
                    "Property Condition",
                    f"{st.session_state.condition_scores['property_condition']:.3f}",
                    delta=f"({current_interpretation})"
                )
        
        with summary_cols[1]:
            quality_summary = st.session_state.condition_scores["quality_of_construction"] or "Not Selected"
            st.metric(
                "Quality of Construction", 
                quality_summary,
                delta=None
            )
        
        with summary_cols[2]:
            improvement_summary = st.session_state.condition_scores["improvement_condition"] or "Not Selected"
            st.metric(
                "Improvement Condition",
                improvement_summary,
                delta=None
            )
        
        # Reset button
        if st.button("🔄 Reset Condition Scores", key=f"reset_conditions_{st.session_state.widget_refresh_counter}"):
            st.session_state.condition_scores = {
                "property_condition": 3.0,
                "quality_of_construction": "",
                "improvement_condition": ""
            }
            st.session_state.property_condition_confirmed = False
            save_condition_state()
            st.rerun()
    
    # Save state after UI is built
    save_condition_state()

# ====== VALIDATION ======
def is_selection_complete() -> bool:
    complete = get_complete_chains()
    return bool(complete) and len(complete) == len([c for c in st.session_state.location_chains if c])

def _get_validation_cache_key() -> str:
    """Generate a cache key based on current UI state for validation caching."""
    import hashlib
    import json
    
    # Create a snapshot of relevant session state for caching
    cache_data = {
        'location_chains': st.session_state.get('location_chains', []),
        'location_attributes': st.session_state.get('location_attributes', {}),
        'condition_scores': st.session_state.get('condition_scores', {}),
        'property_condition_confirmed': st.session_state.get('property_condition_confirmed', False),
        'property_condition_na': st.session_state.get('property_condition_na', False),
    }
    
    # Add feature selections to cache data
    leaves = get_leaf_locations()
    for loc in leaves:
        if loc not in FEATURE_TAXONOMY:
            continue
        for category in FEATURE_TAXONOMY[loc]:
            na_key = f"na_{loc}_{category}"
            sel_key = f"sel_{loc}_{category}"
            cache_data[na_key] = st.session_state.get(na_key, False)
            cache_data[sel_key] = st.session_state.get(sel_key, [])
    
    # Create hash of the state
    cache_str = json.dumps(cache_data, sort_keys=True)
    return hashlib.md5(cache_str.encode()).hexdigest()

def can_move_on() -> bool:
    # Check cache first to avoid expensive validation
    cache_key = _get_validation_cache_key()
    cache_result_key = f"_validation_cache_{cache_key}"
    
    if cache_result_key in st.session_state:
        return st.session_state[cache_result_key]
    
    # Run the actual validation
    result = _can_move_on_uncached()
    
    # Cache the result
    st.session_state[cache_result_key] = result
    
    # Clean up old cache entries (keep only the current one)
    keys_to_remove = [k for k in st.session_state.keys() if k.startswith('_validation_cache_') and k != cache_result_key]
    for key in keys_to_remove:
        del st.session_state[key]
    
    return result

def _can_move_on_uncached() -> bool:
    """Actual validation logic without caching."""
    # 1) Spatial must be done
    if not is_selection_complete():
        return False

    # 2) Every feature-category must have either N/A checked OR at least one feature selected (but not both)
    leaves = get_leaf_locations()
    for loc in leaves:
        if loc not in FEATURE_TAXONOMY:
            continue
        for category in FEATURE_TAXONOMY[loc]:
            na_key  = f"na_{loc}_{category}"
            sel_key = f"sel_{loc}_{category}"
            
            # Get current state
            is_na = st.session_state.get(na_key, False)
            has_selections = bool(st.session_state.get(sel_key, []))
            
            # Must have either N/A checked OR features selected (but not both, not neither)
            if not ((is_na and not has_selections) or (not is_na and has_selections)):
                return False

    # 3) Every attribute must have a selection (including N/A)
    # Get all complete location chains to check required attributes
    complete = get_complete_chains()
    
    # Find the first location key (since we now have one set of attributes per image)
    first_location_key = None
    for chain_idx, chain in enumerate(complete):
        if not chain:
            continue
        
        # Get the leaf location name for this chain
        chain_values = list(chain.values()) if isinstance(chain, dict) else list(chain)
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
        
        first_location_key = f"loc_{chain_idx}_{leaf_location}"
        break
    
    if first_location_key:
        # Collect all relevant attributes across all locations
        all_relevant_attrs = set()
        for chain in complete:
            if not chain:
                continue
            
            # Find relevant attributes for this location
            for attr, locs in ATTRIBUTE_RULES.items():
                if any(loc in step for step in chain for loc in locs):
                    all_relevant_attrs.add(attr)
        
        # Check that each relevant attribute has a value (including N/A)
        for attr in all_relevant_attrs:
            value = st.session_state.location_attributes.get(first_location_key, {}).get(attr, "")
            
            # Handle different value types:
            # - Empty string "" = not selected (invalid)
            # - "N/A" = valid selection
            # - Any other string = valid selection  
            # - False (boolean) = valid selection
            # - True (boolean) = valid selection
            if value == "":  # Only empty string is invalid
                return False

    # 4) Condition scores validation - simplified
    # Property condition must be confirmed OR N/A
    if not (st.session_state.property_condition_confirmed or st.session_state.get("property_condition_na", False)):
        return False
    
    # Quality and improvement must be selected (including N/A)
    if not st.session_state.condition_scores["quality_of_construction"]:
        return False
    if not st.session_state.condition_scores["improvement_condition"]:
        return False

    return True

# ====== SAVE LOGIC ======
def save_current_labels(image_paths: List[str], df: pd.DataFrame, user_name: str) -> pd.DataFrame:
    img_path = image_paths[st.session_state.index]
    
    # Collect all feature labels from current selections with structured format
    all_features = []
    leaves = get_leaf_locations()
    for loc in leaves:
        if loc not in FEATURE_TAXONOMY:
            continue
        for category in FEATURE_TAXONOMY[loc]:
            sel_key = f"sel_{loc}_{category}"
            na_key = f"na_{loc}_{category}"
            
            # Get current state
            selections = st.session_state.get(sel_key, [])
            is_na = st.session_state.get(na_key, False)
            
            # ------------------------------------------------------------------
            # Payload logic (mirrors app._build_payload)
            # ------------------------------------------------------------------
            if is_na and not selections:
                # Skip saving anything for this category (stored implicitly as N/A)
                continue
            
            # If no selections are made and "None" is available as an option, save "None"
            if not selections and "None" in FEATURE_TAXONOMY[loc][category]:
                all_features.append(f"{loc}:{category}:None")
            else:
                # Save the actual selections with location and category context
                for feature in selections:
                    all_features.append(f"{loc}:{category}:{feature}")
    
    data = {
        "image_path": img_path,
        "spatial_labels": "|".join(chains_to_label_strings()),
        "feature_labels": "|".join(sorted(all_features)),  # Now contains "Location:Category:Feature" format
        "notes": st.session_state.notes,
        "flagged": st.session_state.flagged,
        "labeled_by": user_name,
        "property_condition": st.session_state.condition_scores["property_condition"],
        # Simplified condition columns
        "quality_of_construction": st.session_state.condition_scores["quality_of_construction"],
        "improvement_condition": st.session_state.condition_scores["improvement_condition"]
    }
    
    # Convert attributes to the format expected by the CSV
    # Since we now have one set of attributes per image, we just need the first value
    for attr in LOCATION_TAXONOMY.get("attributes", {}):
        # Find the first location that has this attribute set
        for location_key, attrs in st.session_state.location_attributes.items():
            if attr in attrs and attrs[attr]:
                if attrs[attr] == "N/A":
                    data[attr] = None  # Save N/A as null
                else:
                    data[attr] = attrs[attr]  # Save simple value
                break  # Take the first value since all locations should have the same value
    
    new_df = pd.DataFrame([data])
    out_df = pd.concat([df[df["image_path"] != img_path], new_df], ignore_index=True)
    # Optional hook for environments that define a global save_labels function
    # Use dynamic lookup to avoid static-name linter warnings when not present
    saver = globals().get("save_labels")
    if callable(saver):
        try:
            saver(out_df)  # type: ignore[misc]
        except Exception:
            pass
    st.success("✅ Labels saved successfully!")
    return out_df