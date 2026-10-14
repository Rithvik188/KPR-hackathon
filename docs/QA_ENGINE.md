# Engine Q&A cheat sheet (Person 1)

Short answers first; the detail is for follow-ups. Every number is from `engine/evaluation/results.json`
(held-out test split).

**How did you avoid overfitting?**
Thresholds were tuned on one split (300 images, backgrounds set A). Every number we show comes from a
separate split that was never used for tuning (300 images, completely different backgrounds, set B).
Among equally good thresholds, we picked the middle of the range for the most safety margin.
Limitation: it is all synthetic, so real-capture validation in a pilot is the next step.

**What's your false-invalid rate, and why does it matter?**
0.0% on the held-out set: no genuine card was called invalid. A false "invalid" tells an honest citizen
their ID is fake, which is the worst error we can make. So "can't read" always becomes "please retake",
and we only say "invalid" when a second, independent read of the card agrees.

**What happens if OCR misreads a real Aadhaar?**
Three safeguards:
1. Below the confidence gate (0.78, tuned), we ask for a retake instead of judging.
2. Above it, a checksum failure triggers a second read of the whole card at a different scale.
3. Only if both reads agree is the card invalid; if they disagree, it's a retake.
The Verhoeff checksum catches every single-digit error and every adjacent swap (we unit-test both).

**Why not a deep learning model?**
- **Explainable:** every rejection shows the measured value and its threshold (blur 41 vs 140).
- **Fast and cheap:** the quality gate takes 72 ms and full validation about 1.4 s on a laptop CPU, with no GPU.
- **No real ID images needed for training.**
A model could later replace any single check behind the same interface.

**How is the Aadhaar stored?**
It isn't, in full:
- The display shows `XXXX XXXX 1234`.
- For duplicate detection we store `HMAC-SHA256(server secret, number)`. A plain hash would be
  brute-forceable, since there are only 10¹² numbers.
- Card images are encrypted at rest (Fernet) and deleted when the officer decides.
Our privacy audit greps the database, logs and API responses for every generated number and finds none.

**What happens with a real Aadhaar card?**
We never used one. All cards are synthetic SPECIMENs without emblems or logos. The pipeline is
template-agnostic (card detection, keywords, number rules), but real-world accuracy is unmeasured; that
is exactly what the pilot is for.

**Why did BLUR score lowest (F1 0.85)?**
Most of its false flags are photos that also had another real defect (cropped, glare, low resolution),
so the citizen retakes either way. We report it honestly rather than tuning on the test set.

**Duplicates?**
Exact match on the Aadhaar HMAC across applications, shown only to the officer. We tested
perceptual-image hashing too and switched it off: different citizens' cards can have identical hashes,
which would flag innocent people.

**Names with initials?**
`R. KARTHIK` vs `KARTHIK RAJENDRAN`: the initial R expands to RAJENDRAN, so it's a `likely_match` for
the officer to confirm, and only if the dates of birth agree. If the DOB differs, it's a mismatch. On the
held-out sets, 34/34 tiers were correct.

**Tamil?**
All citizen messages are bilingual (Tamil + English). The fields we need are printed in English on these
cards; Tamil OCR is on the roadmap.
