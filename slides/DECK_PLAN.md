# SevaiCheck final deck: implementation plan

**Status:** plan for review. Nothing in Canva changes until the human approves this plan.
**Deck:** Canva "SevaiCheck Final Presentation (Beige)" (`DAHYAkfPXlQ`), currently 11 slides.
**Facts come only from:** `README.md` (e-Sevai research, with its sources), `docs/ENGINE.md` (engine, real-photo
findings, limitations), `engine/evaluation/results.json` (held-out numbers), and the code itself (security controls).
No fixture or invented numbers (CLAUDE.md rule 9).

## 1. Story arc

The audience may not know how e-Sevai works, so the deck first teaches the system, then shows where it breaks, then
what we built:

| Act | Slides | What the audience should leave with |
|---|---|---|
| **1. The system today** | 3–6 | What e-Sevai is, who applies and how, who runs the centres, what happens after you upload |
| **2. The problem** | 7–8 | Errors are found days later by the VAO, which costs every party time and money; catching them at the counter fixes it |
| **3. Our answer** | 9–13 | Solution, how the engine works, stack, and what each user sees on the website |
| **4. Trust** | 14–17 | Privacy, security (controls and honest limits), measured accuracy |
| **5. Close** | 18–19 | What we built, next steps, thank you |

19 slides at about 40 s each is about 13 minutes, plus the live demo. If the slot is shorter, see the trim options in §5.

## 2. Slide-by-slide content

Layout keys refer to the current template pages, reused so the whole deck keeps one look:
**T** title (p1) · **AG** agenda table (p2) · **LP** three numbered blocks + full-height photo + side title (p3/p6) ·
**TI** text + square image (p4) · **C3** three columns with icons (p5/p7/p9) · **PV** two framed images + text (p8) ·
**TL** four-step timeline (p10) · **TY** thank you (p11).

| # | Title | Layout | On-slide content (short; the detail goes in speaker notes) | Source |
|---|---|---|---|---|
| 1 | **SevaiCheck** · Final Presentation | T | Tagline: "Checking ID proofs and certificate applications at the e-Sevai counter, in Tamil and English". Team names. | as now |
| 2 | Agenda | AG | 8 rows (the table has 8): 01 The e-Sevai system today · 02 The application journey · 03 Where it breaks · 04 Our insight and solution · 05 How it works and tech stack · 06 Website features · 07 Privacy and security · 08 Results and what we built | — |
| 3 | **What is TN e-Sevai?** | C3 | **Who runs it:** TNeGA runs the e-Sevai portal; certificates are processed in e-District by Revenue staff. **What it offers:** 119+ services; the biggest are Revenue certificates (Community REV-101, Nativity REV-102, Income REV-103, Legal heir, OBC…). **Who applies:** students (admissions, scholarships), job seekers (TNPSC quotas), farmers (loans, subsidies), widows (pensions), families after a death (legal heir). | README §How TN e-Sevai works today |
| 4 | **How citizens apply** | TI | Two ways: **at an e-Sevai centre**, where an operator fills the form (how most people apply), or **online** through the citizen login. Steps: 1) register or log in (name, district, taluk, mobile, Aadhaar, OTP); 2) create or find the **CAN**, a lifelong profile whose name and address auto-fill every form and can't be edited there; 3) choose the service; 4) fill in the form and upload scans; 5) pay about ₹60 and get an acknowledgement number. | README |
| 5 | **Who are the e-Sevai centres?** | C3 | **About 33,000 centres** across Tamil Nadu. **Government-run, about 6,000.** **Private franchises, about 26,500.** At both, an **operator** fills the form for the citizen. Reality: franchise centres often have poor scanners and get no feedback on scan quality; centre staff reported 3 server outages in one week (July 2026). | README |
| 6 | **After you upload: the approval chain** | TL | 4 steps: **Submit** (₹60, acknowledgement no.) → **VAO** (downloads every attachment, checks each, field verification) → **Revenue Inspector** (first-level scrutiny) → **Tahsildar** (approves or rejects, digitally signs). Intro line: "Deputy Tahsildar step being removed (state announcement, July 2026). Any stage can return or reject. Published 7–15 days, often 15–30 in practice." | README §How it is approved |
| 7 | **The problem: errors found too late** | LP | 01 **Citizens:** a blurry scan, missing Aadhaar back, wrong document or a CAN typo is found days later by the VAO; each costs another visit, fee and wait, and "Returned" is confusing. 02 **Officials:** VAOs open every attachment by hand; queues have no priority and no flags; 4 levels. 03 **Leadership:** the CM's Office wrote to all Collectors about delays (July 2026); there is no data on *where* and *why* applications fail. | README §Where it breaks down |
| 8 | **Our insight** | TI | Catch errors while the citizen is still at the counter. Bad scans can be retaken in seconds, and a CAN typo can be fixed before it's printed. Design rule: **"can't read" is never "invalid"**. | as now (refresh) |
| 9 | **Our solution** | C3 | A pre-flight check that plugs into the existing counter and officer queue; it doesn't replace e-Sevai. **e-Sevai portal**, **Officer chain**, **Admin view** (current text). | as now |
| 10 | **How it works** | LP | 01 Quality gate (≈0.1 s, retake on blur/glare/crop/dark/low-res). 02 Read and check (OCR, Verhoeff for Aadhaar, PAN/EPIC formats, e-Aadhaar letter support). 03 Consistency (three-tier name match, DOB, CAN-vs-document check). | ENGINE.md |
| 11 | **Tech stack** | C3 | current text (React 19 / FastAPI / OpenCV + OCR) | as now |
| 12 | **Website features: citizen and operator** | C3 *(or TI with a screenshot)* | **Citizen portal:** OTP sign-in, 5 open schemes (DEMO-01 first), CAN step, instant document checks, Track with timeline and bilingual SMS. **Operator portal (govt / private):** applies for citizens at the counter from their CAN, centre fixed to their own, **Notices** for their centre. **For everyone:** Tamil/English toggle, works on a phone, "Report a problem". | web/ (shipped) |
| 13 | **Website features: officers and district** | C3 *(or TI with a screenshot)* | **Officer queue:** staff-ID sign-in, role locked (VAO → RI → Tahsildar), per-stage SLA, ready cases first. **Review drawer:** card images, extracted fields, issues with evidence, CAN, name/DOB and form checks; forward, approve, request fix, reject. **District view:** map, KPIs, alerts computed from data (blur spike, SLA breach, duplicate Aadhaar, user reports), accuracy metrics page. | web/ (shipped) |
| 14 | **Privacy by design** | PV | current text (Aadhaar masked, keyed HMAC for Aadhaar and phone, encrypted images deleted on decision, synthetic SPECIMEN cards only) | as now |
| 15 | **Security: what is enforced today** | C3 | See §3. | code |
| 16 | **Security: honest limits and the path to production** | LP or C3 | See §3. | code |
| 17 | **Results on held-out data** | C3 | Current numbers from `results.json` (0/282 false invalids, doc type 100%, Aadhaar 98.1%, PAN 100%, name 96.8%, 34/34 name tiers, quality 0.12 s, full 1.7 s, weakest: blur recall 0.81), plus the real-photo lesson: a phone test with real cards exposed false "cropped" errors and showed most people bring the A4 e-Aadhaar letter; both fixed. **Known limit:** synthetic data, pilot next. | results.json, ENGINE.md |
| 18 | **What we built** | TL | Status line (contract v1.7, 114 tests, contract check 10/10, smoke test passing, privacy audit clean, 90 browser checks) + the 4 phases | as now (refresh) |
| 19 | **Thank you** | TY | one-liner, the ask (pilot feedback), "Live demo next" | as now |

Every slide also gets **speaker notes** (the detail that doesn't fit on the slide, plus timing).

## 3. The security slides (15–16)

We **cannot claim a "guaranteed secure" website**: the sign-ins are prototype mocks. The slides make the case by
showing which controls are real, the evidence for them, and what changes before any pilot. Judges trust this more
than a claim.

**Slide 15: what is enforced today** (three columns, each item true in the code on `main`):
- **Data protection:**
  - full Aadhaar never returned, logged or stored (`XXXX XXXX 1234` only);
  - keyed HMAC-SHA256 fingerprints for Aadhaar and for CAN phone numbers (no plain hashes);
  - card images Fernet-encrypted at rest and deleted when the application is decided.
- **Input and upload safety:**
  - uploads capped at 10 MB, JPG/PNG verified by actually decoding the file (a renamed file is rejected);
  - every request and response validated by Pydantic;
  - file-id path-traversal guard;
  - uniform error bodies with no stack traces.
- **Access rules on the server:**
  - an officer action must match the application's current stage, and only the Tahsildar approves or rejects
    (409 otherwise);
  - CORS limited to the dev origin; production serves UI and API from one origin over the HTTPS tunnel;
  - secrets only in `.env`, never committed.
- **Evidence strip:**
  - privacy audit CLEAN (5,469 applications + logs scanned; no raw phone number in DB or logs);
  - 114 automated tests and contract check 10/10;
  - all data synthetic, watermarked SPECIMEN, no government emblems.

**Slide 16: honest limits and the path to production:**
- **Prototype today:**
  - citizen OTP, staff-ID + CAPTCHA and operator sign-ins run in the browser for the demo;
  - the API does not yet authenticate callers.
- **Before a pilot:**
  - real OTP via an SMS gateway;
  - server-side sessions/tokens, with role-based access checked on every API call;
  - rate limits and lockouts;
  - an audit log of every officer action;
  - keys in a managed vault with rotation;
  - an external penetration test.
- **Always:**
  - minimum data (masked, fingerprinted, deleted on decision), so a breach exposes as little as possible.

## 4. How it will be built in Canva

1. **Backup:** `copy-design` the current deck → "SevaiCheck Final Presentation (backup, pre-restructure)".
2. **Duplicate layouts:**
   - The edit tool can't duplicate a slide, so `merge-designs` (modify the deck) inserts extra copies of template
     pages from the backup: C3 ×5, TI ×1, TL ×1, LP ×1.
   - Then `move_pages` into the §2 order, ending with 19 pages.
   - This step needs your explicit approval at the time (Canva requires it).
3. **Rewrite text** slide by slide with `edit-design` (replace text, slide numbers "NN/19"), checking each preview
   for overflow, as last time. Add speaker notes per slide.
4. **Images:**
   - Reused template photos stay where they fit (queue photo on Problem, counter photo on How citizens apply,
     card+phone on How it works).
   - **Optional:** real app screenshots on slides 12–13 (citizen portal, officer drawer), uploaded to Canva; they
     come from our fixture-mode screenshots, all synthetic data.
5. **Preview all 19 slides → your approval → save.** Then a read-through for number accuracy against
   `results.json`.

Effort: about 60–90 minutes of tool work, most of it text fitting.

## 5. Decisions needed before building

1. **Length:** 19 slides (≈13 min). Trim options, if needed:
   - merge 3+5 (What is e-Sevai + centres);
   - merge 12+13 (features);
   - merge 15+16 (security).
2. **Where:** restructure the current deck in place (backup kept), or build the 19-slide version as a new design?
3. **Screenshots** of the real app on the feature slides: yes or no?
4. **Security wording:** OK with slide 16 stating plainly that the sign-ins are prototype mocks? It's the honest
   version, and it avoids a judge catching it during the demo.
