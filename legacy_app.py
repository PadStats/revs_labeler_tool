import streamlit as st
import pandas as pd
import os
from datetime import datetime
from PIL import Image
from typing import Dict, Any, List, Set
from taxonomy import LOCATION_TAXONOMY, FEATURE_TAXONOMY, ATTRIBUTE_RULES


# ====== CONFIG ======
LABEL_CSV_PATH = "labeled_data.csv"
IMAGE_FOLDER = "images/"

# ─── helper callbacks to clear & rerun ────────────────────────────────────
def clear_and_rerun(sel_key):
    """Clear the given multiselect key then rerun the script."""
    st.session_state[sel_key] = []
    st.rerun()

def rerun():
    """Just rerun the script (for immediate UI updates)."""
    st.rerun()


# ====== SESSION STATE INIT ======
def init_session_state():
    if "index" not in st.session_state:
        st.session_state.index = 0
    if "location_chains" not in st.session_state:
        st.session_state.location_chains = [{}]
    if "feature_labels" not in st.session_state:
        st.session_state.feature_labels = set()
    if "feature_na_locations" not in st.session_state:
        st.session_state.feature_na_locations = set()
    if "attribute_labels" not in st.session_state:
        st.session_state.attribute_labels = {}  # Will be changed to location-based structure
    if "location_attributes" not in st.session_state:
        st.session_state.location_attributes = {}  # New: store attributes per location
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
    # NEW: Persistent feature state storage
    if "persistent_feature_state" not in st.session_state:
        st.session_state.persistent_feature_state = {}
    # NEW: Persistent attribute state storage
    if "persistent_attribute_state" not in st.session_state:
        st.session_state.persistent_attribute_state = {}
    # NEW: Track removed locations to ensure proper cleanup
    if "removed_locations" not in st.session_state:
        st.session_state.removed_locations = set()
    
    # UPDATED: Condition Scores - simplified without manual mode
    if "condition_scores" not in st.session_state:
        st.session_state.condition_scores = {
            "property_condition": 3.0,  # Still continuous slider
            # Quality of Construction - discrete selection
            "quality_of_construction": "",  # Will store the selected option
            # Improvement Condition - discrete selection  
            "improvement_condition": ""  # Will store the selected option
        }
    if "property_condition_confirmed" not in st.session_state:
        st.session_state.property_condition_confirmed = False
    # NEW: Persistent condition state storage
    if "persistent_condition_state" not in st.session_state:
        st.session_state.persistent_condition_state = {
            "property_condition": 3.0,
            "quality_of_construction": "",
            "improvement_condition": "",
            "property_confirmed": False
        }

# ====== IMAGE UTILITIES ======
def get_image_paths():
    if not os.path.exists(IMAGE_FOLDER):
        os.makedirs(IMAGE_FOLDER)
        return []
    return sorted([
        os.path.join(IMAGE_FOLDER, f)
        for f in os.listdir(IMAGE_FOLDER)
        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))
    ])

def load_image(path):
    return Image.open(path)

# ====== LABEL DATA HANDLING ======
def load_labeled_data():
    if os.path.exists(LABEL_CSV_PATH):
        return pd.read_csv(LABEL_CSV_PATH)
    attr_keys = list(LOCATION_TAXONOMY.get("attributes", {}).keys())
    cols = [
        "image_path",
        "spatial_labels",
        "feature_labels",
        "notes",
        "timestamp",
        "flagged",
        "labeled_by",
        "property_condition",
        # Simplified condition columns
        "quality_of_construction",
        "improvement_condition"
    ] + attr_keys
    return pd.DataFrame(columns=cols)

def save_labels(df):
    df.to_csv(LABEL_CSV_PATH, index=False)

def reset_session_state_to_defaults():
    # Clear location chains
    st.session_state.location_chains = [{}]
    
    # Clear all feature-related state
    st.session_state.feature_labels = set()
    st.session_state.feature_na_locations = set()
    
    # Clear all feature widget keys from session state
    keys_to_remove = []
    for key in st.session_state.keys():
        if key.startswith(('na_', 'sel_')) and ('_' in key):
            keys_to_remove.append(key)
    for key in keys_to_remove:
        del st.session_state[key]
    
    # Clear persistent feature state completely
    st.session_state.persistent_feature_state = {}
    
    # Clear persistent attribute state completely
    st.session_state.persistent_attribute_state = {}
    
    # Clear all widget states
    st.session_state.widget_states = {}
    
    # Clear location-specific attributes
    st.session_state.location_attributes = {}
    
    # Clear backward compatibility attributes
    attr_keys = list(LOCATION_TAXONOMY.get("attributes", {}).keys())
    st.session_state.attribute_labels = {k: None for k in attr_keys}
    
    # Clear notes and flag
    st.session_state.notes = ""
    st.session_state.flagged = False
    
    # Clear any attribute widget keys
    attr_keys_to_remove = []
    for key in st.session_state.keys():
        if key.startswith('attr_'):
            attr_keys_to_remove.append(key)
    for key in attr_keys_to_remove:
        del st.session_state[key]
    
    # Clear removed locations tracking
    st.session_state.removed_locations = set()
    
    # Reset condition scores and persistent state - simplified
    st.session_state.condition_scores = {
        "property_condition": 3.0,
        "quality_of_construction": "",
        "improvement_condition": ""
    }
    st.session_state.property_condition_confirmed = False
    st.session_state.persistent_condition_state = {
        "property_condition": 3.0,
        "quality_of_construction": "",
        "improvement_condition": "",
        "property_confirmed": False
    }
    
    # Increment widget refresh counter to force UI refresh
    st.session_state.widget_refresh_counter += 1

# ====== CONDITION SCORES UI ======
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
        
        prop_key = f"prop_condition_slider_{st.session_state.widget_refresh_counter}"
        current_prop_score = st.session_state.condition_scores["property_condition"]
        
        # Check if this is a preloaded score that needs confirmation
        needs_confirmation = (not st.session_state.property_condition_confirmed and 
                            current_prop_score != 3.0)
        
        if needs_confirmation:
            st.warning("⚠️ This property has a preloaded condition score. Please confirm or adjust it below.")
        
        # Always show slider, but disable it when confirmed
        new_prop_score = st.slider(
            "Property Condition Score",
            min_value=1.0,
            max_value=5.0,
            value=current_prop_score,
            step=0.1,
            key=prop_key,
            label_visibility="collapsed",
            disabled=st.session_state.property_condition_confirmed
        )
        
        # Handle immediate change only if not confirmed
        if not st.session_state.property_condition_confirmed:
            if abs(new_prop_score - current_prop_score) > 0.05:  # Small tolerance for float comparison
                st.session_state.condition_scores["property_condition"] = new_prop_score
                save_condition_state()
                st.rerun()
        
        # FLIPPED labels: 1=Excellent, 5=Poor with better alignment
        label_container = st.container()
        with label_container:
            # Use HTML for precise alignment
            labels_html = """
            <div style="display: flex; justify-content: space-between; margin-top: -10px; margin-bottom: 10px; padding: 0 8px;">
                <span style="font-size: 12px; color: #fcfafa; text-align: left;">Excellent</span>
                <span style="font-size: 12px; color: #fcfafa; text-align: center;">Good</span>
                <span style="font-size: 12px; color: #fcfafa; text-align: center;">Average</span>
                <span style="font-size: 12px; color: #fcfafa; text-align: center;">Fair</span>
                <span style="font-size: 12px; color: #fcfafa; text-align: right;">Poor</span>
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
        
        # Find the closest interpretation
        current_interpretation = "Average"  # default
        closest_score = min(score_interpretation.keys(), key=lambda x: abs(x - st.session_state.condition_scores["property_condition"]))
        current_interpretation = score_interpretation[closest_score]
        
        st.markdown(f"**Current Score: {st.session_state.condition_scores['property_condition']:.1f} ({current_interpretation})**")
        
        # Confirmation checkbox for property condition
        confirmed = st.checkbox("✅ Confirm Property Condition Score", value=st.session_state.property_condition_confirmed)
        if confirmed != st.session_state.property_condition_confirmed:
            st.session_state.property_condition_confirmed = confirmed
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
            quality_key = f"quality_slider_{st.session_state.widget_refresh_counter}"
            
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
            improvement_key = f"improvement_slider_{st.session_state.widget_refresh_counter}"
            
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
        
        if st.session_state.property_condition_confirmed:
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
            st.metric(
                "Property Condition",
                f"{st.session_state.condition_scores['property_condition']:.1f}",
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

# ====== HIERARCHY UTILITIES ======
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
    complete = []
    for chain in st.session_state.location_chains:
        if chain:
            path = list(chain.values())
            if path[-1] == "N/A" or is_leaf_node(LOCATION_TAXONOMY["spatial"], path):
                complete.append(path)
    return complete

def get_leaf_locations() -> Set[str]:
    leaves = set()
    for path in get_complete_chains():
        if path and path[-1] != "N/A":
            leaves.add(path[-1])
    return leaves

def chains_to_label_strings() -> List[str]:
    labels: List[str] = []
    for chain in st.session_state.location_chains:
        path = list(chain.values())
        if path and path[-1] == "N/A":
            path = path[:-1]
        if not path:
            continue
        for i in range(1, len(path) + 1):
            labels.append(" > ".join(path[:i]))
    return labels

def label_strings_to_chains(label_strings: List[str]) -> List[Dict]:
    chains = []
    complete_paths = []
    for s in label_strings:
        if not s.strip(): continue
        parts = s.split(" > ")
        if all(not other.startswith(s + " > ") for other in label_strings):
            complete_paths.append(parts)
    for parts in complete_paths:
        chain = {}
        for i, p in enumerate(parts):
            chain[f"level_{i}"] = p
        if not is_leaf_node(LOCATION_TAXONOMY["spatial"], parts):
            chain[f"level_{len(parts)}"] = "N/A"
        chains.append(chain)
    return chains if chains else [{}]

# ====== DROPDOWN CASCADE UI ======
def build_location_chain(chain_index: int):
    chain = st.session_state.location_chains[chain_index]
    container = st.container()
    with container:
        if len(st.session_state.location_chains) > 1 and st.button(
            "❌", key=f"remove_chain_{chain_index}_{st.session_state.widget_refresh_counter}"
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

            # Use a simpler key that doesn't rely on widget_refresh_counter for state storage
            w_key = f"chain_{chain_index}_level_{level}_{st.session_state.widget_refresh_counter}"
            state_key = f"chain_{chain_index}_level_{level}_state"
            
            # Get stored value from our dedicated state storage
            if state_key in st.session_state.widget_states:
                stored = st.session_state.widget_states[state_key]
            else:
                stored = prev
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
                    sel = st.selectbox("", [""] + opts, index=idx, key=w_key, label_visibility="collapsed")

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

def build_dropdown_cascade_ui():
    st.subheader("📍 Location Selection")
    for i in range(len(st.session_state.location_chains)):
        build_location_chain(i)
    col1, _ = st.columns([1, 3])
    with col1:
        if st.button("➕ Add Another Location", key=f"add_location_{st.session_state.widget_refresh_counter}"):
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

# ====== FEATURE UI ======
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
            
            # Restore from persistent storage only if not already in session state
            persistent_na_key = f"persistent_na_{loc}_{category}"
            persistent_sel_key = f"persistent_sel_{loc}_{category}"
            
            if na_key not in st.session_state and persistent_na_key in st.session_state.persistent_feature_state:
                st.session_state[na_key] = st.session_state.persistent_feature_state[persistent_na_key]
            if sel_key not in st.session_state and persistent_sel_key in st.session_state.persistent_feature_state:
                st.session_state[sel_key] = st.session_state.persistent_feature_state[persistent_sel_key]

def build_location_features(location: str):
    """Per‐category N/A checkbox + multiselect—stores only in st.session_state."""
    if location not in FEATURE_TAXONOMY:
        return

    for category, feats in FEATURE_TAXONOMY[location].items():
        st.write(f"**{category}:**")

        na_key  = f"na_{location}_{category}"
        sel_key = f"sel_{location}_{category}"

        # Initialize keys if they don't exist, using persistent state as fallback
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
        
        # Create the N/A checkbox
        na_checked = st.checkbox("🚫 No relevant features", key=na_key, value=current_na)
        
        # Handle state changes after widget interaction
        if na_checked != current_na:
            # N/A state changed
            if na_checked:
                # N/A was just checked - clear selections
                st.session_state[sel_key] = []
                current_selections = []
        
        # Show multiselect or N/A message
        if not na_checked:
            # Show multiselect
            selected_features = st.multiselect(
                "",
                feats,
                default=current_selections,
                key=sel_key
            )
            
            # If features were just selected and N/A is checked, uncheck N/A
            if selected_features and na_checked:
                st.session_state[na_key] = False
                st.rerun()  # Force rerun to update UI
                
        else:
            # Show N/A message
            st.info("✅ Marked this category as N/A")

        st.write("")  # spacing

def build_feature_ui():
    st.subheader("🔧 Features in Selected Locations")
    leaves = get_leaf_locations()
    if not leaves:
        st.info("👆 Complete location selections to see features.")
        return

    avail = [loc for loc in leaves if loc in FEATURE_TAXONOMY]
    if not avail:
        st.info("No specific features defined.")
        return

    st.caption("💡 Select features or mark N/A.")
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

# ====== CONTEXTUAL ATTRIBUTE UI ======
def save_attribute_state():
    """Save current attribute selections to persistent storage"""
    complete = get_complete_chains()
    
    # Only save state for currently valid locations
    current_valid_keys = set()
    
    for chain_idx, chain in enumerate(complete):
        if not chain:
            continue
            
        # Get the leaf location name for this chain
        leaf_location = chain[-1] if chain[-1] != "N/A" else chain[-2] if len(chain) > 1 else None
        if not leaf_location:
            continue
            
        # Create a unique key for this location chain
        location_key = f"loc_{chain_idx}_{leaf_location}"
        
        # Find relevant attributes for this location
        relevant = set()
        for attr, locs in ATTRIBUTE_RULES.items():
            if any(loc in step for step in chain for loc in locs):
                relevant.add(attr)
        
        if not relevant:
            continue
        
        # Save each attribute for this location
        for attr in relevant:
            persistent_key = f"persistent_{location_key}_{attr}"
            current_valid_keys.add(persistent_key)
            
            # Get current value from location_attributes
            current_value = st.session_state.location_attributes.get(location_key, {}).get(attr, "")
            st.session_state.persistent_attribute_state[persistent_key] = current_value
    
    # Clean up persistent state for locations that are no longer valid
    keys_to_remove = []
    for key in st.session_state.persistent_attribute_state:
        if key.startswith('persistent_loc_') and key not in current_valid_keys:
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del st.session_state.persistent_attribute_state[key]

def restore_attribute_state():
    """Restore attribute selections from persistent storage"""
    complete = get_complete_chains()
    
    for chain_idx, chain in enumerate(complete):
        if not chain:
            continue
            
        # Get the leaf location name for this chain
        leaf_location = chain[-1] if chain[-1] != "N/A" else chain[-2] if len(chain) > 1 else None
        if not leaf_location:
            continue
            
        # Create a unique key for this location chain
        location_key = f"loc_{chain_idx}_{leaf_location}"
        
        # Initialize this location's attributes in session state if needed
        if location_key not in st.session_state.location_attributes:
            st.session_state.location_attributes[location_key] = {}
        
        # Find relevant attributes for this location
        relevant = set()
        for attr, locs in ATTRIBUTE_RULES.items():
            if any(loc in step for step in chain for loc in locs):
                relevant.add(attr)
        
        # Restore each attribute from persistent storage
        for attr in relevant:
            persistent_key = f"persistent_{location_key}_{attr}"
            
            # Only restore if not already set and exists in persistent storage
            if attr not in st.session_state.location_attributes[location_key] and persistent_key in st.session_state.persistent_attribute_state:
                st.session_state.location_attributes[location_key][attr] = st.session_state.persistent_attribute_state[persistent_key]

def build_contextual_attribute_ui():
    st.subheader("🏷️ Contextual Attributes")
    complete = get_complete_chains()
    if not complete:
        st.info("👆 Complete locations first.")
        return
    
    # Restore attribute state before building UI
    restore_attribute_state()
    
    # Track completion status
    total_attrs = 0
    completed_attrs = 0
    
    # Process each location chain separately
    for chain_idx, chain in enumerate(complete):
        if not chain:
            continue
            
        # Get the leaf location name for this chain
        leaf_location = chain[-1] if chain[-1] != "N/A" else chain[-2] if len(chain) > 1 else None
        if not leaf_location:
            continue
            
        # Create a unique key for this location chain
        location_key = f"loc_{chain_idx}_{leaf_location}"
        
        # Find relevant attributes for this location
        relevant = set()
        for attr, locs in ATTRIBUTE_RULES.items():
            if any(loc in step for step in chain for loc in locs):
                relevant.add(attr)
                
        if not relevant:
            continue
            
        # Initialize this location's attributes in session state if needed
        if location_key not in st.session_state.location_attributes:
            st.session_state.location_attributes[location_key] = {}
            
        # Display location name as header
        st.write(f"**📍 {leaf_location}:**")
        
        # Display attributes for this location
        attr_map = LOCATION_TAXONOMY.get("attributes", {})
        for attr in sorted(relevant):
            total_attrs += 1
            opts = attr_map.get(attr, [])
            disp = attr.replace("_", " ").title()
            
            # Get current value with empty string as default (forces selection)
            current_value = st.session_state.location_attributes[location_key].get(attr, "")
            
            # Calculate index - default to 0 (blank/empty option)
            idx = 0
            if current_value == "N/A":
                idx = 1  # N/A is at index 1
            elif current_value in opts:
                idx = opts.index(current_value) + 2  # +2 because we add blank and N/A options
            
            # Create a unique widget key that includes the chain index and attribute
            widget_key = f"attr_{location_key}_{attr}_{st.session_state.widget_refresh_counter}"
            
            # Display the dropdown with a blank first option
            choice = st.selectbox(
                disp, 
                [""] + ["N/A"] + opts,  # Blank first option, then N/A, then actual options
                index=idx,
                key=widget_key
            )
            
            # Update the selection immediately in session state
            old_value = st.session_state.location_attributes[location_key].get(attr, "")
            if choice != old_value:
                st.session_state.location_attributes[location_key][attr] = choice
                # Force immediate UI update
                st.rerun()
            
            # Count completed attributes
            if choice:
                completed_attrs += 1
                
        st.markdown("---")
    
    # Save attribute state after UI is built
    save_attribute_state()
    
    # Display completion status
    if total_attrs > 0:
        if completed_attrs == total_attrs:
            st.success(f"✅ All {total_attrs} attributes complete")
        else:
            st.warning(f"⚠️ {completed_attrs}/{total_attrs} attributes complete")

# ====== VALIDATION ======
def is_selection_complete() -> bool:
    complete = get_complete_chains()
    return bool(complete) and len(complete) == len([c for c in st.session_state.location_chains if c])

def can_move_on() -> bool:
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
    for location_key, attrs in st.session_state.location_attributes.items():
        for attr, value in attrs.items():
            if not value:  # Empty string means no selection
                return False

    # 4) Condition scores validation - simplified
    # Property condition must be confirmed
    if not st.session_state.property_condition_confirmed:
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
    
    # Collect all feature labels from current selections
    all_features = set()
    leaves = get_leaf_locations()
    for loc in leaves:
        if loc not in FEATURE_TAXONOMY:
            continue
        for category in FEATURE_TAXONOMY[loc]:
            sel_key = f"sel_{loc}_{category}"
            features = st.session_state.get(sel_key, [])
            all_features.update(features)
    
    data = {
        "image_path": img_path,
        "spatial_labels": "|".join(chains_to_label_strings()),
        "feature_labels": "|".join(sorted(all_features)),
        "notes": st.session_state.notes,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "flagged": st.session_state.flagged,
        "labeled_by": user_name,
        "property_condition": st.session_state.condition_scores["property_condition"],
        # Simplified condition columns
        "quality_of_construction": st.session_state.condition_scores["quality_of_construction"],
        "improvement_condition": st.session_state.condition_scores["improvement_condition"]
    }
    
    # Convert location-specific attributes to the format expected by the CSV
    # We'll use a pipe-separated format: "location1:value1|location2:value2"
    for attr in LOCATION_TAXONOMY.get("attributes", {}):
        attr_values = []
        for location_key, attrs in st.session_state.location_attributes.items():
            if attr in attrs and attrs[attr]:
                # Extract location name from the key (format: loc_idx_name)
                loc_parts = location_key.split('_', 2)
                if len(loc_parts) >= 3:
                    location_name = loc_parts[2]
                    attr_values.append(f"{location_name}:{attrs[attr]}")
        
        if attr_values:
            data[attr] = "|".join(attr_values)
        else:
            data[attr] = None
    
    new_df = pd.DataFrame([data])
    out_df = pd.concat([df[df["image_path"] != img_path], new_df], ignore_index=True)
    save_labels(out_df)
    st.success("✅ Labels saved successfully!")
    return out_df

# ====== MAIN APP ======
def main():
    st.set_page_config(page_title="Property Image Labeling Tool", layout="wide")
    init_session_state()

    user_name = st.text_input("Your Name:", value="anonymous")
    st.session_state.user_name = user_name

    st.title("🏠 Property Image Labeling Tool")

    image_paths = get_image_paths()
    if not image_paths:
        st.error(f"No images found in {IMAGE_FOLDER}.")
        return

    df = load_labeled_data()
    st.session_state.index = max(0, min(st.session_state.index, len(image_paths) - 1))
    img_path = image_paths[st.session_state.index]

    image_changed = (st.session_state.current_image_path != img_path)
    if image_changed:
        st.session_state.current_image_path = img_path
        existing = df[df["image_path"] == img_path]

        if not existing.empty:
            # 1) Reset everything so we start fresh
            reset_session_state_to_defaults()

            # 2) Load the saved row
            row = existing.iloc[0]

            # — Spatial labels —
            raw_spatial = row.get("spatial_labels", "")
            st.session_state.location_chains = (
                label_strings_to_chains(raw_spatial.split("|"))
                if isinstance(raw_spatial, str) and raw_spatial
                else [{}]
            )
            # bump counter so dropdown keys change
            st.session_state.widget_refresh_counter += 1
            # clear any old dropdown states
            st.session_state.widget_states = {}

            # — Feature labels —
            raw_feat = row.get("feature_labels", "")
            feature_set = set(raw_feat.split("|")) if isinstance(raw_feat, str) and raw_feat else set()
            st.session_state.persistent_feature_state = {}
            for loc in get_leaf_locations():
                if loc not in FEATURE_TAXONOMY:
                    continue
                for category, feats in FEATURE_TAXONOMY[loc].items():
                    na_key  = f"persistent_na_{loc}_{category}"
                    sel_key = f"persistent_sel_{loc}_{category}"
                    # pick saved features if any
                    chosen = [f for f in feature_set if f in feats]
                    if chosen:
                        st.session_state.persistent_feature_state[na_key]  = False
                        st.session_state.persistent_feature_state[sel_key] = chosen
                    else:
                        st.session_state.persistent_feature_state[na_key]  = True
                        st.session_state.persistent_feature_state[sel_key] = []

            # — Notes & flag —
            st.session_state.notes   = row.get("notes", "")
            st.session_state.flagged = bool(row.get("flagged", False))

            # — Condition scores - simplified —
            st.session_state.condition_scores = {
                "property_condition": float(row.get("property_condition", 3.0)),
                "quality_of_construction": str(row.get("quality_of_construction", "")),
                "improvement_condition": str(row.get("improvement_condition", ""))
            }
            
            # Set confirmation status based on whether property condition is not default
            property_not_default = st.session_state.condition_scores["property_condition"] != 3.0
            st.session_state.property_condition_confirmed = property_not_default  # If loaded from CSV, consider it confirmed

            # Update persistent state as well
            st.session_state.persistent_condition_state = {
                "property_condition": st.session_state.condition_scores["property_condition"],
                "quality_of_construction": st.session_state.condition_scores["quality_of_construction"],
                "improvement_condition": st.session_state.condition_scores["improvement_condition"],
                "property_confirmed": st.session_state.property_condition_confirmed
            }

            # — Contextual attributes —
            st.session_state.location_attributes      = {}
            st.session_state.persistent_attribute_state = {}

            # build list of complete chains (just like get_complete_chains)
            loaded_complete = []
            for chain in st.session_state.location_chains:
                path = list(chain.values())
                if path and (path[-1] == "N/A" or is_leaf_node(LOCATION_TAXONOMY["spatial"], path)):
                    loaded_complete.append(path)

            for attr in LOCATION_TAXONOMY.get("attributes", {}):
                raw_val = row.get(attr)
                # keep backward-compat label if you want
                st.session_state.attribute_labels[attr] = None if pd.isna(raw_val) else raw_val

                if isinstance(raw_val, str) and not pd.isna(raw_val):
                    for part in raw_val.split("|"):
                        if ":" not in part:
                            continue
                        loc_name, val = part.split(":", 1)
                        # find the matching chain index
                        for idx, path in enumerate(loaded_complete):
                            leaf = path[-1] if path[-1] != "N/A" else path[-2]
                            if leaf == loc_name:
                                loc_key = f"loc_{idx}_{loc_name}"
                                persist_key = f"persistent_{loc_key}_{attr}"
                                st.session_state.location_attributes.setdefault(loc_key, {})[attr] = val
                                st.session_state.persistent_attribute_state[persist_key] = val

            # clear any notion of "just removed" so UI cleanup logic won't fire
            st.session_state.removed_locations = set()

        else:
            # brand-new image, just reset
            reset_session_state_to_defaults()

        # done loading—next render should show exactly what we pulled from CSV
        st.session_state.skip_label_loading = False


    # Smart responsive sizing that adapts to image dimensions
    try:
        img = load_image(img_path)
        
        # Get original image dimensions
        img_width, img_height = img.size
        
        # Define your preferred size range
        MIN_WIDTH = 800   # Minimum display width
        MAX_WIDTH = 1200   # Maximum display width
        MAX_HEIGHT = 1200  # Maximum display height
        MIN_HEIGHT = 800   # Minimum display height
        
        # Calculate optimal display size
        # Start with original dimensions
        display_width = img_width
        display_height = img_height
        
        # If image is too small, scale it up (but not too much to avoid pixelation)
        if display_width < MIN_WIDTH:
            scale_factor = MIN_WIDTH / display_width
            display_width = MIN_WIDTH
            display_height = int(display_height * scale_factor)
        
        # If image is too large, scale it down
        if display_width > MAX_WIDTH:
            scale_factor = MAX_WIDTH / display_width
            display_width = MAX_WIDTH
            display_height = int(display_height * scale_factor)
        
        # Also check height constraint
        if display_height > MAX_HEIGHT:
            scale_factor = MAX_HEIGHT / display_height
            display_height = MAX_HEIGHT
            display_width = int(display_width * scale_factor)
        if display_height < MIN_HEIGHT:
            scale_factor = MIN_HEIGHT / display_height
            display_height = MIN_HEIGHT
            display_width = int(display_width * scale_factor)
        
        # Convert image to base64
        import base64
        from io import BytesIO
        
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # Create responsive HTML with calculated dimensions
        centered_html = f"""
        <div style="display: flex; justify-content: center; align-items: center; width: 100%; margin: 20px 0;">
            <div style="text-align: center;">
                <img src="data:image/png;base64,{img_str}" 
                    style="width: {display_width}px; height: {display_height}px; display: block; margin: 0 auto; object-fit: contain;" 
                    alt="Property Image">
                <p style="text-align: center; margin-top: 10px; color: #666;">
                    {os.path.basename(img_path)} ({st.session_state.index+1}/{len(image_paths)}) - {img_width}×{img_height} → {display_width}×{display_height}
                </p>
            </div>
        </div>
        """
        
        st.markdown(centered_html, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Error loading image: {e}")
        return

    # Restore feature state EARLY - before any validation or UI components
    leaves = get_leaf_locations()
    if leaves:
        # Restore feature state when locations are available
        for loc in leaves:
            if loc not in FEATURE_TAXONOMY:
                continue
            for category in FEATURE_TAXONOMY[loc]:
                na_key = f"na_{loc}_{category}"
                sel_key = f"sel_{loc}_{category}"
                
                # Restore from persistent storage only if not already in session state
                persistent_na_key = f"persistent_na_{loc}_{category}"
                persistent_sel_key = f"persistent_sel_{loc}_{category}"
                
                if na_key not in st.session_state and persistent_na_key in st.session_state.persistent_feature_state:
                    st.session_state[na_key] = st.session_state.persistent_feature_state[persistent_na_key]
                if sel_key not in st.session_state and persistent_sel_key in st.session_state.persistent_feature_state:
                    st.session_state[sel_key] = st.session_state.persistent_feature_state[persistent_sel_key]

    # Restore attribute state EARLY as well
    restore_attribute_state()

    # Restore condition state EARLY as well
    restore_condition_state()

    # Navigation buttons
    nav_left, nav_prev, nav_next, nav_right = st.columns([3, 1, 1, 3], gap="small")

    # Check validation status AFTER state restoration
    can_proceed = can_move_on()

    with nav_prev:
        if st.button("⬅️ Previous",
                     use_container_width=True,
                     disabled=st.session_state.index == 0,
                     key="btn_prev"):
            st.session_state.index -= 1
            st.rerun()

    with nav_next:
        if st.button("➡️ Next",
                     use_container_width=True,
                     disabled=(not can_proceed or st.session_state.index == len(image_paths)-1),
                     key="btn_next"):
            df = save_current_labels(image_paths, df, user_name)
            st.session_state.index += 1
            st.rerun()

    # Current Selections Display
    sel_left, sel_mid, sel_right = st.columns([1, 4, 1], gap="small")
    complete = get_complete_chains()

    # Get features from current session state (after restoration)
    feats_by_loc = {}
    for loc in sorted(leaves):
        feats = []
        if loc in FEATURE_TAXONOMY:
            for category in FEATURE_TAXONOMY[loc]:
                sel_key = f"sel_{loc}_{category}"
                feats.extend(st.session_state.get(sel_key, []))
        feats_by_loc[loc] = feats

    groups = list(feats_by_loc.items())

    with sel_mid:
        with st.expander("📋 Current Selections", expanded=True):
            loc_col, feat_col = st.columns([1, 1], gap="medium")

            # Left: Locations
            with loc_col:
                st.subheader("Locations")
                if complete:
                    for chain in complete:
                        st.write("• " + " → ".join(chain))
                else:
                    st.write("_(none selected)_")

            # Right: Features grid
            with feat_col:
                st.subheader("Features")
                if groups and any(feats for _, feats in groups):
                    # build table header
                    headers = "".join(
                        f"<th style='text-align:left; padding:4px'>{loc}</th>"
                        for loc, feats in groups if feats
                    )
                    filtered_groups = [(loc, feats) for loc, feats in groups if feats]
                    if filtered_groups:
                        max_rows = max(len(feats) for _, feats in filtered_groups)
                        # build rows
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
                        st.markdown(table_html, unsafe_allow_html=True)
                    else:
                        st.write("_(no features yet)_")
                else:
                    st.write("_(no features yet)_")

            # Add attributes section
            st.subheader("Attributes")
            if st.session_state.location_attributes:
                # Build a table of location-specific attributes
                attr_table_html = "<table style='width:100%; border-collapse: collapse;'>"
                attr_table_html += "<tr><th style='text-align:left; padding:4px'>Location</th><th style='text-align:left; padding:4px'>Attribute</th><th style='text-align:left; padding:4px'>Value</th></tr>"
                
                for location_key, attrs in st.session_state.location_attributes.items():
                    if not attrs:
                        continue
                        
                    # Extract location name from key
                    loc_parts = location_key.split('_', 2)
                    if len(loc_parts) < 3:
                        continue
                    location_name = loc_parts[2]
                    
                    # Add each attribute
                    for attr, value in attrs.items():
                        if value:  # Only show attributes with values
                            attr_display = attr.replace("_", " ").title()
                            attr_table_html += f"<tr><td style='text-align:left; padding:2px'>{location_name}</td><td style='text-align:left; padding:2px'>{attr_display}</td><td style='text-align:left; padding:2px'>{value}</td></tr>"
                
                attr_table_html += "</table>"
                st.markdown(attr_table_html, unsafe_allow_html=True)
            else:
                st.write("_(no attributes yet)_")

            # Add condition scores section - simplified
            st.subheader("Condition Scores")
            scores_table_html = "<table style='width:100%; border-collapse: collapse;'>"
            scores_table_html += "<tr><th style='text-align:left; padding:4px'>Category</th><th style='text-align:left; padding:4px'>Score/Selection</th></tr>"
            
            # Property condition with interpretation
            prop_score = st.session_state.condition_scores['property_condition']
            score_interpretation = {
                1.0: "Excellent", 1.1: "Excellent", 1.2: "Excellent", 1.3: "Excellent", 1.4: "Excellent", 1.5: "Excellent", 1.6: "Excellent", 1.7: "Excellent", 1.8: "Excellent", 1.9: "Excellent",
                2.0: "Good", 2.1: "Good", 2.2: "Good", 2.3: "Good", 2.4: "Good", 2.5: "Good", 2.6: "Good", 2.7: "Good", 2.8: "Good", 2.9: "Good",
                3.0: "Average", 3.1: "Average", 3.2: "Average", 3.3: "Average", 3.4: "Average", 3.5: "Average", 3.6: "Average", 3.7: "Average", 3.8: "Average", 3.9: "Average",
                4.0: "Fair", 4.1: "Fair", 4.2: "Fair", 4.3: "Fair", 4.4: "Fair", 4.5: "Fair", 4.6: "Fair", 4.7: "Fair", 4.8: "Fair", 4.9: "Fair",
                5.0: "Poor"
            }
            closest_score = min(score_interpretation.keys(), key=lambda x: abs(x - prop_score))
            current_interpretation = score_interpretation[closest_score]
            
            scores_table_html += f"<tr><td style='text-align:left; padding:2px'>Property Condition</td><td style='text-align:left; padding:2px'>{prop_score:.1f} ({current_interpretation})</td></tr>"
            
            # Quality of Construction
            quality_display = st.session_state.condition_scores["quality_of_construction"] or "Not Selected"
            scores_table_html += f"<tr><td style='text-align:left; padding:2px'>Quality of Construction</td><td style='text-align:left; padding:2px'>{quality_display}</td></tr>"
            
            # Improvement Condition
            improvement_display = st.session_state.condition_scores["improvement_condition"] or "Not Selected"
            scores_table_html += f"<tr><td style='text-align:left; padding:2px'>Improvement Condition</td><td style='text-align:left; padding:2px'>{improvement_display}</td></tr>"
            
            scores_table_html += "</table>"
            st.markdown(scores_table_html, unsafe_allow_html=True)

    # Clear/Save buttons - recalculate validation for buttons that may be affected by UI interactions
    cs_left, cs_clear, cs_save, cs_right = st.columns([3, 1, 1, 3], gap="small")

    with cs_clear:
        if st.button("🗑️ Clear Labels",
                     use_container_width=True,
                     key="btn_clear"):
            reset_session_state_to_defaults()
            st.session_state.skip_label_loading = True
            st.rerun()

    # Recalculate validation for Save button in case UI interactions have changed state
    current_validation = can_move_on()
    
    with cs_save:
        if st.button("💾 Save Labels",
                     type="primary",
                     use_container_width=True,
                     disabled=not current_validation,
                     key="btn_save"):
            df = save_current_labels(image_paths, df, user_name)

    # Flag for Review button (centered)
    flag_left, flag_center, flag_right = st.columns([2, 1, 2], gap="small")
    with flag_center:
        flag_text = "🚩 Unflag" if st.session_state.flagged else "🚩 Flag for Review"
        flag_type = "secondary" if st.session_state.flagged else "primary"
        if st.button(flag_text,
                     type=flag_type,
                     use_container_width=True,
                     key="btn_flag"):
            st.session_state.flagged = not st.session_state.flagged
            st.rerun()

    # Location and Feature selection (side by side)
    col1, col2 = st.columns([1.2, 0.8])
    with col1:
        build_dropdown_cascade_ui()
    with col2:
        build_feature_ui()
        build_contextual_attribute_ui()

    # Add Condition Scores section
    st.markdown("---")
    build_condition_scores_ui()

    # Additional Information
    st.subheader("📝 Additional Information")
    st.session_state.notes = st.text_area("Notes", value=st.session_state.notes, height=80)

    # Go-to-page - recalculate validation for final buttons
    final_validation = can_move_on()
    
    go_left, go_mid, go_right = st.columns([3, 1, 3], gap="small")
    with go_mid:
        goto = st.number_input(
            "",
            min_value=1,
            max_value=len(image_paths),
            value=st.session_state.index + 1,
            step=1,
            key="goto_input_bottom",
            label_visibility="collapsed"
        )
        if st.button("🔎 Go", 
                     use_container_width=True, 
                     disabled=not final_validation,
                     key="btn_goto_bottom"):
            df = save_current_labels(image_paths, df, user_name)
            st.session_state.index = goto - 1
            st.rerun()


if __name__ == "__main__":
    main()