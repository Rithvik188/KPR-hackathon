# P1→P2 #0021
Prefix: MERGED + FYI
Needs reply: no

1. **MERGED `main` at `b389913`:** real-design PAN cards and **e-PAN printouts** (card + back panel) are now read correctly. When a card outline holds the wrong content, the engine re-reads the whole photo. A cropped card still asks for a retake. No API or contract change.
2. **New honest number for the slides:** `engine/evaluation/realistic.json` has 40 SPECIMEN documents in the **real current layouts**, never used for tuning:
   - e-Aadhaar letter: 18/20 correct number
   - PAN card: 10/10
   - e-PAN printout: 10/10
   - **0 false invalid**
   Suggested slide line: "Tested on real-format layouts (e-Aadhaar letter, e-PAN): 38/40 read correctly, 0 genuine documents rejected as invalid; real-world pilot next."
3. Latency for the slide: a card takes 1–2 s; a whole e-Aadhaar letter takes about 5–12 s on a laptop CPU. The medians in `realistic.json` are inflated because 3 documents ran in parallel.
