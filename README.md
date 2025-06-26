# Property-Image Labeling Tool
*A Streamlit + Firestore application for large-scale real-estate photo annotation*

---

## 1 · Repository layout
| Path | Purpose |
|------|---------|
| `app.py` | Main Streamlit application (modern, Firestore-ready). |
| `internal_ui.py` | All widgets, validation and state logic; ported from legacy. |
| `ui_components.py` | Thin façade that re-exports the UI helpers needed by `app.py`. |
| `taxonomy.py` | Location hierarchy, feature taxonomy & attribute rules. |
| `labeler_backend/base.py` | `LabelRepo` interface – storage-agnostic contract. |
| `labeler_backend/fire_repo.py` | Production Firestore implementation. |
| `labeler_backend/dev_repo.py` | CSV / in-memory implementation for local dev & tests. |
| `labeler_backend/factory.py` | Picks repo at runtime via `LABEL_REPO` env var. |
| `labeler_backend/bb_resolver.py` | Talks to Cloud-Run service that converts `bb_url` to a signed URL. |
| `legacy_app.py` | The original CSV prototype – kept as reference. |
| `images/` | Optional local folder scanned by `DevRepo`.

---

## 2 · Runtime architecture
```mermaid
graph LR
  subgraph "Streamlit browser session"
    UI["Streamlit GUI\n(app.py + internal_ui)"] --> RepoIface["LabelRepo interface"]
  end
  RepoIface --> DevRepo[(DevRepo\nCSV / mock)]
  RepoIface --> FireRepo[(FirestoreRepo)]
  FireRepo -->|signed URL| Resolver[Backblaze URL API]
  FireRepo --> FS[(Google Firestore)]
  FS --> Img[REVS_images]
  FS --> Lab[REVS_labels]
  FS --> Usr[REVS_users]
```
Switch repo with `LABEL_REPO=dev` (default) or `firestore`.

---

## 3 · Firestore schema (v 1.0)
### 3.1 `REVS_images`
```jsonc
{
  "image_id"          : "uuid-v4",          // doc ID – shared key
  "property_id"       : "mongoId",         
  "image_hash"        : "sha256",
  "bb_url"            : "b2/path.jpg",
  "image_url"         : "https://cdn…",    // optional

  "status"            : "unlabeled | in_progress | labeled",
  "assigned_to"       : "user123 | null",
  "timestamp_uploaded": <timestamp>,
  "timestamp_assigned": <timestamp|null>,
  "timestamp_labeled" : <timestamp|null>,
  "task_expires_at"   : <timestamp|null>,
  "qa_status"         : "pending | approved | rejected",
  "flagged"           : false
}
```
*Composite indexes*
1. `(status, assigned_to)`
2. `(status, task_expires_at)`
3. `(status, timestamp_uploaded)`
4. `(flagged, status)` (optional)

### 3.2 `REVS_labels`
```jsonc
{
  "image_id"       : "uuid-v4",  // same as images doc
  "property_id"    : "mongoId",

  "spatial_labels" : ["Residential Interior", "… > Bathroom > Full"],
  "feature_labels" : ["Granite Countertop", "Double Sink"],
  "attributes"     : { "flooring_type": "Hardwood", … },
  "condition_scores": {
      "property_condition"      : 3.0,
      "quality_of_construction" : "High Quality",
      "improvement_condition"   : "Remodeled"
  },

  "notes"            : "needs white balance",
  "flagged"          : false,
  "schema_version"   : 1,
  "labeled_by"       : "user123",

  "timestamp_created": <ts>,        // first save
  "updated_at"       : <ts>         // last edit
}
```
`/revisions/` sub-collection stores previous payloads on every edit.

### 3.3 `REVS_users`
```jsonc
{
  "user_id"               : "user123",
  "name"                  : "John Doe",
  "email"                 : "j.doe@example.com",

  "current_image_id"      : "uuid | null",   // resume pointer
  "last_labeled_image_id" : "uuid | null",
  "total_images_labeled"  : 122,
  "timestamp_last_labeled": <ts>
}
```

---

## 4 · GUI workflow
1. Analyst enters **username**.  The value is used as `user_id`.
2. `repo.get_next_task(user_id)`
   * returns an `in_progress` image already assigned to the user, **or**
   * locks the next `unlabeled` doc (writes status→`in_progress`, sets `task_expires_at = now+60m`).
3. Image displayed via signed URL from Backblaze.
4. Analyst fills in:
   * **Location cascade** – any leaf produces *all* label prefixes.  Example "Full Bathroom" results in:
     ```json
     [
       "Residential Interior",
       "Residential Interior > Private Spaces",
       "Residential Interior > Private Spaces > Bathroom",
       "Residential Interior > Private Spaces > Bathroom > Full"
     ]
     ```
   * **Features** – multiselects (XOR with N/A).
   * **Contextual attributes** – dropdowns that change with the selected locations.
   * **Condition scores** – slider + two categorical ratings.
5. **Validation** (`internal_ui.can_move_on`) blocks navigation until every required widget is filled.
6. Clicking **Save** or **Next**:
   * writes/updates `REVS_labels/{image_id}` (includes `schema_version` and `updated_at`),
   * changes `REVS_images.status → "labeled"` and clears `task_expires_at`,
   * increments `total_images_labeled` and writes `last_labeled_image_id` in `REVS_users`.
7. Closing the tab: the Cloud-Scheduler job finds rows where `task_expires_at < now()` and resets them to `unlabeled`.

---

## 5 · Setup & execution
### 5.1 Local dev (CSV) --> TO BE IMPLEMENTED
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export LABEL_REPO=dev
streamlit run app.py
```
Place JPG/PNG/WebP files inside `images/`.

### 5.2 Production (Firestore)
```bash
export FIRESTORE_CREDENTIALS_JSON=$(cat service-account.json)
export GCP_PROJECT_ID=my-gcp-project
export BB_RESOLVER_ENDPOINT=https://<cloud-run>/fetch-image-urls
export LABEL_REPO=firestore
streamlit run app.py
```
Docker:
```bash
docker build -t labeler:latest .
docker run -p 8501:8501 --env-file .env labeler:latest
```

#### 5.3  One-liner Docker runner

For convenience the repo ships with `run_labeler.sh`, a wrapper that builds (optional) and runs the container with all the right mounts and environment variables.

```bash
# first time – build image then run
./run_labeler.sh /path/to/service_account.json --build

# subsequent runs – skip rebuild
./run_labeler.sh /path/to/service_account.json
```

What the script does

1. Reads `.env` for variables such as `GCP_PROJECT_ID`, `BB_RESOLVER_ENDPOINT`, and `LABEL_REPO=firestore`.
2. Mounts the given service-account key read-only inside the container at `/secrets/key.json`.
3. Publishes Streamlit on port **8501**.
4. Rebuilds the Docker image when `--build` is passed.

This saves you from memorising the full `docker run` incantation and guarantees consistent flags every time.

---

## 6 · Admin operations
| Task | How |
|------|-----|
| Ingest new photos | Insert docs in **REVS_images** with `status="unlabeled"`. |
| Unlock stale tasks | Cloud Function every 15 min: `status=="in_progress" && task_expires_at < NOW()`. |
| Review flagged | Query `(flagged==true && status=="labeled")`. |
| Export labels | Query `REVS_labels` where `schema_version==1` → write to BigQuery or GCS. |

---

## 7 · Extending
* **Taxonomy update** – bump `schema_version`, update `taxonomy.py`, migrate old docs or keep them read-only.
* **QA workflow** – use `qa_status` in **REVS_images** and enable reviewers to change it.
* **Analytics** – create `(property_id, timestamp_created)` index on **REVS_labels** for time-series per property.

---

## 8 · Troubleshooting
| Symptom | Likely cause |
|---------|--------------|
| Image fails to load | Wrong `bb_url` or resolver endpoint down. |
| "No more images" but queue not empty | Required composite indexes missing or all tasks locked. |
| Save button greyed | Validation failed – open *Current Selections* to see missing items. |

---

© 2025 Real Estate Vision Suite