# SevaiCheck API Contract

**Version: 1.0** (bump on every change; see the CLAUDE.md section on the contract change protocol)

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
| `DocType` | `aadhaar_front`, `aadhaar_back`, `pan`, `voter_id`, `unknown` |
| `DocStatus` | `accepted`, `fixable`, `invalid` |
| `AppStatus` | `submitted`, `needs_fix`, `ready_for_officer`, `approved`, `rejected` |
| `IssueSeverity` | `blocking`, `warning`, `info` |
| `Audience` | `citizen` (shown at the counter and to the officer), `officer` (officer view only) |
| `NameTier` | `match`, `likely_match`, `mismatch`, `not_enough_data` |
| `AlertRule` | `REJECT_SPIKE`, `SLA_BREACH`, `BACKLOG_GROWTH`, `DUPLICATE_CLUSTER`, `USER_REPORTED` |
| `AlertSeverity` | `high`, `medium`, `low` |
| `AlertStatus` | `open`, `acknowledged` |
| `OfficeType` | `taluk_office`, `esevai_centre` |
| `Service` | `community_certificate`, `income_certificate`, `nativity_certificate`, `ration_card_update` |
| `IssueCategory` | `scanner_problem`, `long_wait`, `wrong_rejection`, `other` |
| `ReporterRole` | `citizen`, `operator`, `officer` |
| `OfficerAction` | `approve`, `reject`, `request_fix` |

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

**DocStatus rule:**
- `invalid` if there is any `INVALID_*` issue.
- Otherwise `fixable` if there is any blocking issue.
- Otherwise `accepted`.

**AppStatus rule** (implemented by Person 2 in `ops/status.py`):
- The required documents are `aadhaar_front` + `aadhaar_back` + (`pan` or `voter_id`).
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
When OCR ran, these become:
```json
"fields": {"id_number_display": "XXXX XXXX 4321", "name": "R. KARTHIK",
           "dob": "1998-04-12", "gender": "M", "father_name": null},
"ocr": {"mean_confidence": 0.91, "id_number_confidence": 0.94}
```
- `id_number_display` is masked for Aadhaar. PAN and EPIC numbers are shown in full.
- `aadhaar_back` has no name or DOB. Its `fields` are `{"id_number_display": "...", "pin_code": "641402"}`.
- `document_id` is `null` from `/api/validate`, and set when a document is uploaded to an application.

### ConsistencyResult
```json
{"name_tier": "likely_match", "name_score": 86.0,
 "names_compared": ["R. KARTHIK", "KARTHIK RAJENDRAN"],
 "dob_match": true, "issues": [Issue]}
```

### Office
```json
{"id": "off_sulur_es2", "name": "e-Sevai Centre – Sulur 2", "type": "esevai_centre",
 "taluk": "Sulur", "lat": 11.0247, "lng": 77.1256}
```

### ApplicationSummary
```json
{"id": "app_7f3a91", "citizen_name": "KARTHIK R", "phone_masked": "98XXXXXX21",
 "service": "community_certificate", "office_id": "off_sulur_es2", "office_name": "e-Sevai Centre – Sulur 2",
 "status": "needs_fix", "created_at": "...", "updated_at": "...",
 "sla_due_at": "...", "sla_hours_left": 41.5,
 "flag_codes": ["BLUR"], "doc_count": 2, "resubmissions": 1}
```
`sla_due_at` is `created_at` + 72 h. `sla_hours_left` can be negative, which means the SLA has been breached.

### ApplicationDetail
ApplicationSummary plus:
```json
{"documents": [{"id": "doc_1", "doc_type": "aadhaar_front", "status": "accepted",
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
| 1 | `GET /api/health` | P1 | none | `{"status":"ok","ocr_engine":"easyocr","version":"1.0"}` |
| 2 | `POST /api/validate` | P1 | multipart `file`, optional form `declared_type` | `ValidationResult` (not persisted) |
| 3 | `GET /api/metrics/detection` | P1 | none | `DetectionMetrics` (reads `engine/evaluation/results.json`, or the fixture if that file is missing) |
| 4 | `GET /api/offices` | P2 | none | `Office[]` |
| 5 | `POST /api/applications` | P2 | `{"citizen_name","phone","service","office_id"}` | `ApplicationSummary` (201) |
| 6 | `GET /api/applications` | P2 | query `status?`, `office_id?`, `limit=50`, `offset=0` | `{"items": ApplicationSummary[], "total": int}`. Sorted: `ready_for_officer` first, then by `sla_hours_left` ascending |
| 7 | `GET /api/applications/{id}` | P2 | none | `ApplicationDetail` |
| 8 | `POST /api/applications/{id}/documents` | P2 (calls P1 functions) | multipart `file`, form `declared_type` | `{"document_id": str, "validation": ValidationResult, "application": ApplicationSummary, "consistency": ConsistencyResult}` |
| 9 | `GET /api/documents/{id}/image` | P2 (uses P1 storage) | none | `image/jpeg` (perspective-corrected card), or 404 if deleted |
| 10 | `PATCH /api/applications/{id}` | P2 | `{"action": OfficerAction, "reason_code": str?, "note": str?}` | `ApplicationSummary` |
| 11 | `GET /api/alerts` | P2 | query `status?` | `Alert[]`, newest first |
| 12 | `POST /api/alerts/{id}/ack` | P2 | none | `Alert` |
| 13 | `GET /api/metrics/operations` | P2 | query `days=30` | `OperationsMetrics` |
| 14 | `POST /api/issues` / `GET /api/issues` | P2 | Issue report fields without `id`/`created_at` | `Issue` / `Issue[]` |
| 15 | `GET /api/notifications` | P2 | query `application_id?` | `Notification[]`, newest first |
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
#  ValidationOutcome.extracted     -> ExtractedDoc | None (unmasked-safe fields: name, dob, gender, doc_type)

def check_consistency(docs: list[ExtractedDoc]) -> ConsistencyResult: ...
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
| `Application` | id, citizen_name, phone_masked, service, office_id, status, created_at, updated_at, sla_due_at, resubmissions, decision_action, decision_reason, decision_note, decided_at, is_seed |
| `Document` | id, application_id, doc_type, status, issues_json, fields_json, aadhaar_hmac, phash, image_path, uploaded_at, is_seed |
| `AppEvent` | id, application_id, at, event, actor, note |
| `Alert` | id, rule, severity, office_id, title_en, detail_en, evidence_json, suggested_action_en, status, created_at, dedupe_key |
| `IssueReport` | id, office_id, category, description, reporter_role, created_at |
| `Notification` | id, application_id, channel, to_masked, body_en, body_ta, created_at |

Seeded historical documents have `image_path = NULL` and `is_seed = true`.
