# SevaiCheck held-out evaluation

Generated 2026-10-15T00:16:12Z on the **test split only** (300 images, background set B) and 34 held-out document sets. Thresholds were tuned on a separate split (background set A).

## Key trust metric

- **False-invalid rate: 0.00%** (0 of 282 genuine cards were marked `invalid`).
- Clean genuine cards accepted first time: 97.3% (111 cards).

## Detection per code

| Code | Precision | Recall | F1 | Support | False flags |
|---|---|---|---|---|---|
| CROPPED | 1.00 | 1.00 | 1.00 | 35 | 0 |
| BLUR | 0.88 | 0.81 | 0.85 | 27 | 3 |
| GLARE | 1.00 | 1.00 | 1.00 | 33 | 0 |
| TOO_DARK | 1.00 | 1.00 | 1.00 | 27 | 0 |
| TOO_BRIGHT | 1.00 | 0.85 | 0.92 | 20 | 0 |
| LOW_RESOLUTION | 1.00 | 1.00 | 1.00 | 27 | 0 |
| WRONG_DOC_TYPE | 1.00 | 1.00 | 1.00 | 19 | 0 |
| INVALID_CHECKSUM | 1.00 | 0.94 | 0.97 | 18 | 0 |

Document-type accuracy (images without quality errors): **100.0%** (n=148)

## Field accuracy

| Field | Accuracy | n |
|---|---|---|
| aadhaar_number | 98.1% | 53 |
| pan_number | 100.0% | 23 |
| epic_number | 97.1% | 35 |
| dob | 100.0% | 93 |
| name | 96.8% | 93 |

Names are compared ignoring spaces (rapidfuzz ratio >= 95 on letters only), because the OCR engine often drops word spaces. Aadhaar numbers are compared via their HMAC, so the engine never has to return them. A retake request counts as a miss.

## Latency (sequential, single process)

- Quality gate: p50 119 ms, p95 241 ms
- Full validation (quality + OCR + rules): p50 1656 ms, p95 6856 ms

## Consistency (held-out sets)

| expected \ predicted | match | likely_match | mismatch |
|---|---|---|---|
| match | 11 | 0 | 0 |
| likely_match | 0 | 12 | 0 |
| mismatch | 0 | 0 | 11 |

- Sets with too little readable data (`not_enough_data`, excluded above): 0
- `AADHAAR_BACK_MISSING` raised on 4/4 sets missing the back.

## Worst failures (up to 10)

| File | Doc | True codes | Predicted | Status |
|---|---|---|---|---|
| img_00020.jpg | aadhaar_back | INVALID_CHECKSUM | EAADHAAR_PAGE, UNREADABLE | fixable |
| img_00029.jpg | aadhaar_back | BLUR | - | accepted |
| img_00040.jpg | aadhaar_back | TOO_BRIGHT | EAADHAAR_PAGE, UNREADABLE | fixable |
| img_00070.jpg | voter_id | BLUR | - | accepted |
| img_00102.jpg | aadhaar_back | BLUR | - | accepted |
| img_00111.jpg | aadhaar_back | TOO_BRIGHT | EAADHAAR_PAGE | accepted |
| img_00132.jpg | voter_id | BLUR | - | accepted |
| img_00134.jpg | aadhaar_back | TOO_BRIGHT | EAADHAAR_PAGE | accepted |
| img_00238.jpg | voter_id | BLUR | - | accepted |
| img_00038.jpg | aadhaar_front | CROPPED, GLARE | BLUR, CROPPED, GLARE | fixable |


## Honest limitations

- All data is synthetic (SPECIMEN cards rendered by us). Templates, fonts and degradations are our simulation, so these numbers say how well the checks separate *our* simulated failure modes.
- Scores near 100% (e.g. LOW_RESOLUTION, GLARE) mostly mean the simulated defect is easy to separate; real phone captures will be harder. The next step is a pilot with real-capture validation.
- Support per code is small (about 20-40 images), so each percentage point is roughly one image.
