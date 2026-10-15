# SevaiCheck API Contract

**Version: 1.6** (bump on every change; see the CLAUDE.md section on the contract change protocol)

**Changelog**
- 1.6 (additive): full **e-Aadhaar letter** support. An A4 e-Aadhaar page uploaded to either Aadhaar slot is validated as a page (number taken from its repeated printings, never the VID) and gets the info issue `EAADHAAR_PAGE`; `doc_type` = the declared slot. The same letter may be uploaded to both slots.
- 1.5 (additive): CAN citizen profiles (`Citizen` table, `Application.can_id`, `POST /api/citizens`, `GET /api/citizens/{can}`); `OfficeType` adds `esevai_centre_private`.
- 1.4 (additive): service-specific supporting documents (`contract/services.json`, 4 new DocTypes); form-vs-document check (`citizen_dob` on applications, `form` argument to `check_consistency`, `ConsistencyResult.form_check`, issue codes `FORM_NAME_MISMATCH`, `FORM_NAME_VARIANT`, `FORM_DOB_MISMATCH`, `CONTENT_NOT_VERIFIED`); stage-aware officer chain VAO → RI → Tahsildar (`stage`, `stage_due_at`, `stage_sla_hours_left`, OfficerAction `forward`, PATCH `role`, `GET /applications?stage=`).
- 1.3: `ApplicationDetail.documents[].declared_type` (string or null).
- 1.2: `Application.consistency_json` (optional, latest ConsistencyResult cached by ops).
- 1.1: `Document.declared_type` + slot grouping by declared type; `AADHAAR_BACK_MISSING` timing rule; nullable quality fields; `name_score` and multi-document tier definitions; `ExtractedDoc` fields spelled out.

## Conventions

- **Base path:** `/api`. In dev, the frontend calls `/api/...` and the Vite proxy forwards it to `http://localhost:8000`.
- **JSON:** snake_case. IDs are strings. Timestamps are ISO 8601 UTC ending in `Z`.
- **Errors:** `{"error": {"code": "STRING", "message": "human readable"}}` with an appropriate 4xx or 5xx status.
- **Uploads:** `multipart/form-data`, with the field name `file`. JPG or PNG only, at most 10 MB.
- **Full Aadhaar numbers never appear** in any response, log line or DB column.

---

## 1. Enums

| Enum | Values |
|---|---|
| `DocType` | `aadhaar_front`, `aadhaar_back`, `pan`, `voter_id`, `unknown`; supporting (v1.4): `parent_community_certificate`, `birth_certificate`, `income_proof`, `address_proof` |
| `DocStatus` | `accepted`, `fixable`, `invalid` |
| `AppStatus` | `submitted`, `needs_fix`, `ready_for_officer`, `approved`, `rejected` |
| `IssueSeverity` | `blocking`, `warning`, `info` |
| `Audience` | `citizen` (shown at the counter and to the officer), `officer` (officer view only) |
| `NameTier` | `match`, `likely_match`, `mismatch`, `not_enough_data` |
| `AlertRule` | `REJECT_SPIKE`, `SLA_BREACH`, `BACKLOG_GROWTH`, `DUPLICATE_CLUSTER`, `USER_REPORTED` |
| `AlertSeverity` | `high`, `medium`, `low` |
| `AlertStatus` | `open`, `acknowledged` |
| `OfficeType` | `taluk_office`, `esevai_centre` (government-run), `esevai_centre_private` (franchise, v1.5) |
| `Service` | `community_certificate`, `income_certificate`, `nativity_certificate`, `ration_card_update` |
| `IssueCategory` | `scanner_problem`, `long_wait`, `wrong_rejection`, `other` |
| `ReporterRole` | `citizen`, `operator`, `officer` |
| `OfficerAction` | `approve`, `reject`, `request_fix`, `forward` (v1.4) |
| `Stage` (v1.4) | `vao`, `ri`, `tahsildar` (order and per-stage SLA hours in `contract/services.json` → `stages`) |

### Issue codes

Messages (`msg_en`, `msg_ta`) live in `contract/messages.json`, and the backend fills them in.

| Code | Stage | Severity | Audience | Resulting DocStatus |
|---|---|---|---|---|
| `FILE_TOO_LARGE` | file | blocking | citizen | fixable |
| `UNSUPPORTED_FILE` | file | blocking | citizen | fixable |
| `CARD_NOT_FOUND` | quality | blocking | citizen | fixable |
| `CROPPED` | quality | blocking | citizen | fixable |
| `BLUR` | quality | blocking | citizen | fixable |
| `GLARE` | quality | blocking | citizen | fixable |
| `TOO_DARK` | quality | blocking | citizen | fixable |
| `TOO_BRIGHT` | quality | blocking | citizen | fixable |
| `LOW_RESOLUTION` | quality | blocking | citizen | fixable |
| `SKEW_CORRECTED` | quality | info | officer | (no effect) |
| `UNKNOWN_DOC_TYPE` | classify | blocking | citizen | fixable |
| `WRONG_DOC_TYPE` | classify | blocking | citizen | fixable |
| `UNREADABLE` | extract | blocking | citizen | fixable |
| `INVALID_CHECKSUM` | rules | blocking | citizen | **invalid** |
| `INVALID_FORMAT` | rules | blocking | citizen | **invalid** |
| `OCR_AUTOCORRECTED` | rules | info | officer | (no effect) |
| `DUPLICATE_SUSPECTED` | duplicates | warning | officer | (no effect) |
| `AADHAAR_BACK_MISSING` | consistency | blocking | citizen | (application level) |
| `NAME_LIKELY_MATCH` | consistency | warning | officer | (application level) |
| `NAME_MISMATCH` | consistency | blocking | citizen | (application level) |
| `DOB_MISMATCH` | consistency | blocking | citizen | (application level) |
| `FORM_NAME_MISMATCH` (v1.4) | form | blocking | citizen | (application level) |
| `FORM_NAME_VARIANT` (v1.4) | form | warning | officer | (application level) |
| `FORM_DOB_MISMATCH` (v1.4) | form | blocking | citizen | (application level) |
| `CONTENT_NOT_VERIFIED` (v1.4) | supporting doc | info | officer | (no effect) |
| `EAADHAAR_PAGE` (v1.6) | quality | info | officer | (no effect) |

**DocStatus rule:**
- `invalid` if there is any `INVALID_*` issue.
- Otherwise `fixable` if there is any blocking issue.
- Otherwise `accepted`.

**AppStatus rule** (implemented by Person 2 in `ops/status.py`):
- The required documents are `aadhaar_front` + `aadhaar_back` + (`pan` or `voter_id`) **plus the service's supporting document** from `contract/services.json` → `services.<service>.required` (v1.4).
- **Slots are keyed by `declared_type`**, not the detected `doc_type`. A quality early-return has `doc_type = "unknown"`, but it still belongs to the slot the operator uploaded into. "Latest document per slot" and the resubmission counter both use `declared_type`.
- **`AADHAAR_BACK_MISSING` while collecting:** the engine always reports it when the front is present and the back is absent. Ops treats it as blocking **only once every other required slot has been attempted** (or the operator presses "Finish"). Before that, the application stays `submitted`, and no notification is sent for it.
- Notifications are sent only on a **transition into** `needs_fix`, not on every upload that stays `needs_fix`.
- `needs_fix` if any latest document is `fixable` or `invalid`, or if there is a blocking application-level issue.
- `ready_for_officer` if every required document is present and `accepted`, and there are no blocking application-level issues.
- `submitted` otherwise (still collecting documents).
- `approved` and `rejected` are set only by an officer action.

---

## 2. Schemas

### Issue
```json
{"code": "BLUR", "severity": "blocking", "audience": "citizen",
 "msg_en": "...", "msg_ta": "...",
 "evidence": {"blur_score": 41.2, "threshold": 110.0}}
```
`evidence` is a free-form object of numbers or strings explaining why the issue fired. Always include the measured value and the threshold.

### ValidationResult
```json
{
  "document_id": null,
  "doc_type": "aadhaar_front",
  "declared_type": "aadhaar_front",
  "status": "fixable",
  "issues": [Issue],
  "quality": {"card_found": true, "blur_score": 41.2, "glare_fraction": 0.004,
              "brightness": 131.0, "skew_deg": 3.1, "card_width_px": 1180, "passed": false},
  "fields": null,
  "ocr": null,
  "timings_ms": {"quality": 180, "ocr": 0, "total": 195}
}
```
When `card_found` is `false`, the measured quality fields (`blur_score`, `glare_fraction`, `brightness`, `skew_deg`, `card_width_px`) are `null`. On a quality early-return, `doc_type` is `"unknown"` because classification did not run.

When OCR ran, these become:
```json
"fields": {"id_number_display": "XXXX XXXX 4321", "name": "R. KARTHIK",
           "dob": "1998-04-12", "gender": "M", "father_name": null},
"ocr": {"mean_confidence": 0.91, "id_number_confidence": 0.94}
```
- `id_number_display` is masked for Aadhaar. PAN and EPIC numbers are shown in full.
- `aadhaar_back` has no name or DOB. Its `fields` are `{"id_number_display": "...", "pin_code": "641402"}`.
- `document_id` is `null` from `/api/validate`, and set when a document is uploaded to an application.
- **Supporting documents (v1.4):** with a supporting `declared_type`, the engine runs page-quality checks (blur, glare, exposure, resolution on the whole photo; no card detection, so never `CARD_NOT_FOUND`/`CROPPED`) and a keyword check. Text that clearly belongs to another document type → `WRONG_DOC_TYPE`; otherwise `accepted` with an info `CONTENT_NOT_VERIFIED` issue (the officer verifies the contents). `doc_type` = the declared type, `fields` = `{"title": "<detected heading or null>"}`, `extracted` and `aadhaar_hmac` are `None`.

### ConsistencyResult
```json
{"name_tier": "likely_match", "name_score": 86.0,
 "names_compared": ["R. KARTHIK", "KARTHIK RAJENDRAN"],
 "dob_match": true, "issues": [Issue]}
```
- `name_score` is the rapidfuzz `token_sort_ratio` of the two **full, normalised** name strings (0–100). When an initial was expanded, the expansion is recorded in the `NAME_LIKELY_MATCH` evidence (`"initial_expanded": "R→RAJENDRAN"`), and the score is still the full-string score.
- With more than two named documents, the Aadhaar front name is compared with each other document, and the **worst** pair (mismatch < likely_match < match) is reported.
- `name_score`, `names_compared` and `dob_match` are `null` / `[]` / `null` when `name_tier` is `not_enough_data`.
- **`form_check` (v1.4, optional, null when no form was passed):** `{"name_on_form": "KARTHIK R", "name_on_documents": "R. KARTHIK", "name_tier": "match", "dob_on_form": "1998-04-12", "dob_match": true}`. The operator-typed name is compared with the Aadhaar front (else the first named document) using the same tier logic: `mismatch` → `FORM_NAME_MISMATCH` (blocking), `likely_match` → `FORM_NAME_VARIANT` (warning, officer); a different DOB → `FORM_DOB_MISMATCH` (blocking). This catches the e-Sevai CAN problem: the typed name is what gets printed on the certificate.

### Citizen (CAN profile, v1.5)
```json
{"can": "CAN2026000123", "name": "KARTHIK R", "dob": "1998-04-12", "phone_masked": "98XXXXXX21",
 "address_line": "27, Gandhi Street, Sulur", "pin_code": "641402", "created_at": "..."}
```
- Created once and **never edited** (there is no PATCH). Its `name`/`dob` are what e-Sevai prints on the certificate.
- Looked up by phone: the server stores `phone_hmac` (keyed HMAC, `app.core.security.phone_hmac`) and `phone_masked`,
  never the raw number. One CAN per phone number.
- An application created with `can` copies `citizen_name`/`citizen_dob` from the CAN, and the form-vs-document check
  (`check_consistency(docs, form=...)`) uses those values.

### Office
```json
{"id": "off_sulur_es2", "name": "e-Sevai Centre – Sulur 2", "type": "esevai_centre",
 "taluk": "Sulur", "lat": 11.0247, "lng": 77.1256}
```

### ApplicationSummary
```json
{"id": "app_7f3a91", "citizen_name": "KARTHIK R", "citizen_dob": "1998-04-12", "can_id": "CAN2026000123", "phone_masked": "98XXXXXX21",
 "service": "community_certificate", "office_id": "off_sulur_es2", "office_name": "e-Sevai Centre – Sulur 2",
 "status": "needs_fix", "created_at": "...", "updated_at": "...",
 "sla_due_at": "...", "sla_hours_left": 41.5,
 "flag_codes": ["BLUR"], "doc_count": 2, "resubmissions": 1,
 "stage": null, "stage_due_at": null, "stage_sla_hours_left": null}
```
- v1.4: `citizen_dob` is the ISO date typed by the operator (or null). `stage` is `null` unless `status == "ready_for_officer"`; an application entering `ready_for_officer` starts at `"vao"`. `stage_due_at` = when the stage was entered + that stage's `sla_hours`; `stage_sla_hours_left` can be negative.
`sla_due_at` is `created_at` + 72 h. `sla_hours_left` can be negative, which means the SLA has been breached.

### ApplicationDetail
ApplicationSummary plus:
```json
{"documents": [{"id": "doc_1", "doc_type": "aadhaar_front", "declared_type": "aadhaar_front", "status": "accepted",
                "issues": [Issue], "fields": {...}, "uploaded_at": "...", "image_available": true}],
 "consistency": ConsistencyResult,
 "history": [{"at": "...", "event": "document_uploaded", "actor": "operator", "note": "aadhaar_front: fixable (BLUR)"}],
 "decision": null}
```
`decision` is set after an officer acts: `{"action": "approve", "reason_code": null, "note": null, "at": "..."}`.

### Alert
```json
{"id": "al_01", "rule": "REJECT_SPIKE", "severity": "high",
 "office_id": "off_sulur_es2", "office_name": "e-Sevai Centre – Sulur 2",
 "title_en": "Blur rejections up 3.4× this week",
 "detail_en": "38 of 104 documents rejected for BLUR in the last 7 days (36.5%) vs 11 of 102 (10.8%) the week before.",
 "evidence": {"code": "BLUR", "rate_now": 0.365, "rate_prev": 0.108, "n_now": 104, "n_prev": 102},
 "suggested_action_en": "Check the scanner or camera focus at this centre; brief operators on holding cards steady.",
 "status": "open", "created_at": "..."}
```

### DetectionMetrics
This is produced by Person 1's `evaluation/run.py`.
```json
{"generated_at": "...", "source": "evaluation|FIXTURE",
 "dataset": {"tune_n": 300, "test_n": 300, "sets_n": 60,
             "note_en": "Held-out synthetic captures with simulated phone-camera degradation."},
 "per_code": [{"code": "BLUR", "precision": 0.0, "recall": 0.0, "f1": 0.0, "support": 0}],
 "doc_type_accuracy": 0.0,
 "field_accuracy": {"aadhaar_number": 0.0, "pan_number": 0.0, "epic_number": 0.0, "dob": 0.0, "name": 0.0},
 "false_invalid_rate": 0.0,
 "latency_ms": {"quality_p50": 0, "quality_p95": 0, "full_p50": 0, "full_p95": 0},
 "consistency": {"labels": ["match", "likely_match", "mismatch"],
                 "confusion": [[0,0,0],[0,0,0],[0,0,0]]}}
```
`false_invalid_rate` is the share of genuine (valid-number) cards that the system marked `invalid`. **This is the key trust metric.**

### OperationsMetrics
This is produced by Person 2's `ops/metrics_ops.py`.
```json
{"days": 30, "source": "seed|FIXTURE",
 "totals": {"applications": 0, "documents": 0, "first_time_right_rate": 0.0,
            "avg_resubmissions": 0.0, "backlog_now": 0, "sla_breaches_now": 0},
 "daily": [{"date": "2026-10-01", "submitted": 0, "approved": 0, "rejected": 0, "backlog": 0}],
 "by_office": [{"office_id": "...", "office_name": "...", "taluk": "...", "lat": 0, "lng": 0,
                "submissions": 0, "reject_rate": 0.0, "backlog": 0, "top_issue": "BLUR"}],
 "by_issue": [{"code": "BLUR", "count": 0}],
 "projection": {"baseline_reject_rate": 0.0, "projected_reject_rate": 0.0,
                "prevented_rejections": 0, "assumptions_en": "..."}}
```
**Projection formula:**
- `prevented_rejections = Σ over counter-detectable codes of (rejections_with_code × recall(code))`
- `recall(code)` comes from DetectionMetrics.
- `assumptions_en` states this formula in plain words.

### Issue report (user-reported event)
```json
{"id": "is_1", "office_id": "off_sulur_es2", "category": "scanner_problem",
 "description": "Scanner output is blurry since Monday", "reporter_role": "operator", "created_at": "..."}
```

### Notification (mock SMS)
```json
{"id": "nt_1", "application_id": "app_7f3a91", "channel": "sms", "to_masked": "98XXXXXX21",
 "body_en": "...", "body_ta": "...", "created_at": "..."}
```

---

## 3. Endpoints

| # | Method and path | Owner | Request | Response |
|---|---|---|---|---|
| 1 | `GET /api/health` | P1 | none | `{"status":"ok","ocr_engine":"easyocr","ocr_gpu":true,"ocr_ready":true,"version":"1.1"}` (`ocr_ready` is false while the OCR model warms up after start) |
| 2 | `POST /api/validate` | P1 | multipart `file`, optional form `declared_type` | `ValidationResult` (not persisted) |
| 3 | `GET /api/metrics/detection` | P1 | none | `DetectionMetrics` (reads `engine/evaluation/results.json`, or the fixture if that file is missing) |
| 4 | `GET /api/offices` | P2 | none | `Office[]` |
| 5 | `POST /api/applications` | P2 | `{"citizen_name","phone","service","office_id","citizen_dob"?,"can"?}` (v1.4; v1.5: with `can`, name/DOB/phone come from the CAN and the typed values are ignored) | `ApplicationSummary` (201) |
| 6 | `GET /api/applications` | P2 | query `status?`, `office_id?`, `stage?` (v1.4), `limit=50`, `offset=0` | `{"items": ApplicationSummary[], "total": int}`. Sorted: `ready_for_officer` first, then by `sla_hours_left` ascending |
| 7 | `GET /api/applications/{id}` | P2 | none | `ApplicationDetail` |
| 8 | `POST /api/applications/{id}/documents` | P2 (calls P1 functions) | multipart `file`, form `declared_type` | `{"document_id": str, "validation": ValidationResult, "application": ApplicationSummary, "consistency": ConsistencyResult}` |
| 9 | `GET /api/documents/{id}/image` | P2 (uses P1 storage) | none | `image/jpeg` (perspective-corrected card), or 404 if deleted |
| 10 | `PATCH /api/applications/{id}` | P2 | `{"action": OfficerAction, "reason_code": str?, "note": str?, "role": Stage?}` | `ApplicationSummary`. v1.4: `forward` moves `vao → ri → tahsildar`; when `role` is given it must equal the current `stage`, else 409 `STAGE_MISMATCH`. `request_fix` is allowed at any stage; `approve`/`reject` only at `tahsildar` when `role` is given. Without `role`, the old single-officer behaviour is kept. |
| 11 | `GET /api/alerts` | P2 | query `status?` | `Alert[]`, newest first |
| 12 | `POST /api/alerts/{id}/ack` | P2 | none | `Alert` |
| 13 | `GET /api/metrics/operations` | P2 | query `days=30` | `OperationsMetrics` |
| 14 | `POST /api/issues` / `GET /api/issues` | P2 | Issue report fields without `id`/`created_at` | `Issue` / `Issue[]` |
| 15 | `GET /api/notifications` | P2 | query `application_id?` | `Notification[]`, newest first |
| 17 | `POST /api/citizens` (v1.5) | P2 | `{"name","dob","phone","address_line"?,"pin_code"?}` | `Citizen`: 201 if created, 200 with the existing CAN if the phone already has one (create-or-find) |
| 18 | `GET /api/citizens/{can}` (v1.5) | P2 | none | `Citizen`, or 404 |
| 16 | `GET /api/reports/weekly.pdf` | P2 (stretch) | query `office_id?` | `application/pdf` |

---

## 4. Internal Python interface (Person 1 → Person 2)

Person 2's `ops` code calls only these functions from `app.validation.api` and `app.core.storage`. Person 1 ships **stubs with these exact signatures by Sync 1**, then makes them real without changing the signatures.

```python
# app/validation/api.py
from app.validation.types import ValidationOutcome, ConsistencyResult, ExtractedDoc

def validate_image(image_bytes: bytes, declared_type: str | None = None) -> ValidationOutcome: ...
#  ValidationOutcome.result        -> ValidationResult (pydantic, exactly the contract shape)
#  ValidationOutcome.aadhaar_hmac  -> str | None   (hex; only for aadhaar_front/back)
#  ValidationOutcome.phash         -> str | None   (perceptual hash of warped card)
#  ValidationOutcome.card_jpeg     -> bytes | None (perspective-corrected card for officer view)
#  ValidationOutcome.extracted     -> ExtractedDoc | None (set whenever OCR ran)
#  ExtractedDoc fields: doc_type, declared_type, name, dob (ISO or None), gender, father_name, id_last4
#  (never the full ID number)

def check_consistency(docs: list[ExtractedDoc], form: dict | None = None) -> ConsistencyResult: ...
#  v1.4: form = {"name": application.citizen_name, "dob": application.citizen_dob (ISO or None)}
#        adds ConsistencyResult.form_check and FORM_* issues. Omit it for the old behaviour.
#  Pass the latest accepted/extracted doc of each type in the application.
#  Includes AADHAAR_BACK_MISSING when aadhaar_front present and aadhaar_back absent.

def find_duplicates(session, aadhaar_hmac: str | None, phash: str | None,
                    exclude_application_id: str) -> list[str]: ...
#  Returns other application_ids with the same HMAC or phash distance <= thresholds.phash_max_distance.

# Other read-only imports Person 2 may use:
# app.validation.messages.make_issue(code, evidence) -> Issue
# app.core.security.aadhaar_hmac(digits) -> str        (seed data for the duplicate story)
# app.core.security.mask_phone(phone) -> str
# app.routers.metrics_detection.load_detection_metrics() -> dict

# app/core/storage.py
def save_image(document_id: str, jpeg_bytes: bytes) -> str: ...   # returns path; encrypted at rest
def load_image(document_id: str) -> bytes | None: ...
def delete_image(document_id: str) -> None: ...
```

---

## 5. Database tables (`app/core/models.py`, Person 1 implements by hour ~0.75)

| Table | Columns |
|---|---|
| `Office` | id, name, type, taluk, lat, lng |
| `Citizen` (v1.5) | id (the CAN), name, dob, phone_hmac (unique), phone_masked, address_line, pin_code, created_at |
| `Application` | id, citizen_name, citizen_dob (v1.4), can_id (v1.5), stage (v1.4), stage_entered_at (v1.4), phone_masked, service, office_id, status, created_at, updated_at, sla_due_at, resubmissions, decision_action, decision_reason, decision_note, decided_at, consistency_json, is_seed |
| `Document` | id, application_id, doc_type, declared_type, status, issues_json, fields_json, extracted_json, aadhaar_hmac, phash, image_path, uploaded_at, is_seed |
| `AppEvent` | id, application_id, at, event, actor, note |
| `Alert` | id, rule, severity, office_id, title_en, detail_en, evidence_json, suggested_action_en, status, created_at, dedupe_key |
| `IssueReport` | id, office_id, category, description, reporter_role, created_at |
| `Notification` | id, application_id, channel, to_masked, body_en, body_ta, created_at |

Seeded historical documents have `image_path = NULL` and `is_seed = true`.

`Document.extracted_json` stores the `ExtractedDoc` (no full ID number) so ops can recompute consistency from the latest document of each slot without re-running OCR.
