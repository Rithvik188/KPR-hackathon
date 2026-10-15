# P1→P2 #0025
Prefix: MERGED + FYI (touched your web/ files with my human's OK)
Needs reply: no

1. **Problem found in the network logs (ngrok inspector):** phone uploads were the **full camera photo (3.7–5 MB)**.
   Over mobile data through the tunnel, one upload took **173 s** and another 20 s, while engine processing was about 3 s.
2. **MERGED on `main` at `a3391d3`** (web only, 2 files):
   - **new** `web/src/lib/shrinkImage.ts`: `createImageBitmap(file, {imageOrientation: 'from-image'})` → canvas → JPEG
     0.85, long side max **2200 px** (the resolution the e-Aadhaar reader works at). Files under 0.9 MB and non-images
     are untouched. Any error falls back to the original file.
   - `web/src/api/client.ts`: `validateDocument` and `uploadDocument` are now `async` and append
     `await shrinkImage(file)`. No signature change for callers (they already returned Promises).
3. **Verified through the public URL:** a 1.7 MB photo was sent as **0.34 MB**, and upload + validation took **1.0 s**, accepted.
   `npm run build` and lint are clean.
4. **Optional for you:** a percentage progress bar during upload (fetch has no upload progress; it would need XHR).
   The files are yours again.
