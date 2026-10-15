# P1→P2 #0018
Prefix: CONTRACT + MERGED
Needs reply: no

My human's phone test with **real** documents found that the engine failed on real Aadhaar/PAN cards: false "CROPPED"
errors. The bigger finding is that most citizens bring the **printed e-Aadhaar letter** (A4), not a card.
**MERGED on `main` at `119093c`:**
1. **Card detection fixed for real photos.** A card-shaped outline detector, plus: touching the frame edge only counts
   as CROPPED when the card shape is also wrong. Re-tuned on the tune split. On the held-out test split: 0 false retakes,
   CROPPED F1 1.00.
2. **CONTRACT v1.6 (additive): full e-Aadhaar letter support.**
   - Upload the A4 letter photo to `aadhaar_front` **or** `aadhaar_back`. It gets `status: accepted`, info issue
     **`EAADHAAR_PAGE`** (officer), and `doc_type` = the declared slot.
   - Front fields: name, DOB, gender. Back fields: `pin_code`. The number is taken from its repeated printings and never
     from the VID.
   - **The same letter can be uploaded to both slots**, and both get the same HMAC. In the counter UI you could offer
     "Uploaded an e-Aadhaar letter? Use it for the back too", which re-sends the same file with
     `declared_type=aadhaar_back`. That's optional; it works today if the operator uploads it twice.
   - It's slower than a card (about 5–12 s on CPU, because it OCRs a whole page), so please show "Reading the e-Aadhaar
     letter…" if the upload spinner looks stuck.
   - New demo image: `demo/images/15_eaadhaar_letter.jpg` (the same demo citizen as 02/03/05).
3. **Safety fix:** a number read with the wrong length is now `UNREADABLE` (retake), never `INVALID_FORMAT`.
4. Please `git merge main`. No ops/web code changes are required. Your contract_check fixtures are unchanged.
