# SevaiCheck

**Catch document errors at the e-Sevai counter in seconds, before an application spends weeks in the queue.**

SevaiCheck validates citizen ID proofs (Aadhaar, PAN, Voter ID) and service documents the moment they are
photographed at the counter. It explains every problem in Tamil and English, gives officers a clean, pre-checked
queue, and shows district administrators where and why applications fail across Coimbatore district.

---

## How TN e-Sevai works today

**Who runs it.** The e-Sevai portal ([tnesevai.tn.gov.in](https://www.tnesevai.tn.gov.in/)) is operated by the Tamil
Nadu e-Governance Agency (TNeGA). Certificates are processed in a separate back-office system, **e-District**,
used by Revenue Department staff.

**Who applies.** Ordinary citizens who need a government certificate:
- **Students:** admissions and scholarships.
- **Job seekers:** TNPSC exams and reservation quotas.
- **Farmers:** loans and subsidies.
- **Widows and deserted women:** pensions.
- **Families after a death:** legal heir certificates.

They apply in one of two ways:
- **At one of about 33,000 e-Sevai centres** (about 6,000 government-run, about 26,500 private franchises), where an
  **operator** fills in the application for them. This is how most people apply.
- **Online**, through the citizen login.

**The services.** The portal lists 119+ services. The highest-volume ones are the Revenue Department certificates:

| Code | Certificate |
|---|---|
| REV-101 | Community |
| REV-102 | Nativity |
| REV-103 | Income |
| REV-104 | First graduate |
| REV-105 / 109 | Deserted woman / widow |
| REV-114 | Legal heir |
| REV-115 | OBC |
| REV-116 | Residence |
| REV-117 / 118 | Small or marginal farmer / solvency |

**How an application is made**
1. **Register or log in** with name, district, taluk, mobile and Aadhaar, verified by an OTP.
2. **Create or find the CAN** (Citizen Access Number), a lifelong citizen profile. Its name and address **auto-fill
   every application and cannot be edited on the form**, so a typo in the CAN is printed on the final certificate.
3. **Choose the service**, for example Services → Revenue Department → REV-101 Community Certificate.
4. **Fill in the service form and upload scanned documents.** Each service needs different documents. For example:
   - **Community:** photo, address proof, a parent's or sibling's community certificate, a self-declaration.
   - **Nativity:** birth certificate and proof of 5 years' residence.
   - **Income:** salary, land and ration-card details.
5. **Pay about ₹60** and receive an **acknowledgement number**. Unpaid applications sit unnoticed under "Saved
   Application".

**How it is approved (e-District)**
1. **Village Administrative Officer (VAO):** downloads every attachment, checks it, and does field verification.
2. **Revenue Inspector (RI):** first-level scrutiny of the VAO's report.
3. **Deputy Tahsildar:** further scrutiny. In July 2026 the state announced it plans to remove this step to reduce
   delays and corruption.
4. **Tahsildar:** approves or rejects, and digitally signs the certificate.

At any stage an application can be **returned for correction** or **rejected** (appeals go to the Revenue Divisional
Officer). Published timelines are 7 days for nativity and 15 days for income, but in practice it often takes
15–30 days. The citizen tracks the status on e-District and downloads a digitally signed PDF.

**Where it breaks down**
- **Citizens:**
  - Problems are discovered **days later at the VAO**: a blurry scan, a missing Aadhaar back side, the wrong
    document, names that differ between documents.
  - Each one means another visit, another fee and another wait.
  - "Returned" is confusing, and a CAN typo ends up on the certificate.
- **Operators:** franchise centres often have poor scanners and get no feedback on scan quality. Server outages are
  common; centre staff reported three in a single week in July 2026.
- **Officials:**
  - VAOs and RIs open every attachment by hand.
  - Queues have no prioritisation and no flags explaining what is wrong.
  - Every application passes through four levels.
- **Leadership:** in July 2026 the Chief Minister's Office wrote to all District Collectors about processing delays.
  Collectors have no data on *where* and *why* applications fail.

## How SevaiCheck improves it

SevaiCheck does not replace e-Sevai. It is a **pre-flight check** that plugs into the existing counter and officer
queue, so fixable mistakes are caught while the citizen is still at the counter.

| Problem today | What SevaiCheck does |
|---|---|
| Bad scans are found days later by the VAO | **Instant quality checks** (blur, glare, crop, darkness, low resolution) with a Tamil + English "retake" message, in about 0.1 s |
| Wrong document, or a fake / mistyped ID number | **Document-type check and ID-number rules** (Aadhaar Verhoeff checksum, PAN and EPIC formats). "Can't read" is never treated as "invalid" |
| Names and dates of birth differ across documents | **Three-tier name matching** that understands Tamil initials (`R. KARTHIK` ↔ `KARTHIK RAJENDRAN`), with date of birth as the tie-breaker |
| The name typed into the application doesn't match the documents (the CAN typo problem) | **Form-vs-document check:** the typed name and DOB are compared with the ID documents before submission |
| Each service needs different documents | **Service-aware checklist** (community, nativity, income, ration card) with quality checks on every supporting document |
| VAOs open every attachment by hand | **Pre-checked officer queue:** extracted fields, flags with evidence, card images, sorted by SLA |
| Four approval levels with no visibility | **Stage-aware queue:** VAO → RI → Tahsildar, with an SLA for each stage, matching the 2026 simplification |
| Citizens confused by "Returned" | **Plain bilingual SMS** that says exactly what to fix |
| Collectors can't see where or why things fail | **District dashboard:** map, KPIs, and alerts computed from data (e.g. a scanner fault at one centre, an SLA breach at a taluk office, a duplicate Aadhaar across centres) |

**Privacy by design**
- Full Aadhaar numbers are never shown, logged or stored: we show `XXXX XXXX 1234` and keep only a keyed HMAC for
  duplicate checks.
- Card images are encrypted at rest and deleted when the officer decides.
- All cards in this project are synthetic `SPECIMEN` cards. No real ID images are used.

**Measured honestly.** Thresholds were tuned on one synthetic dataset and evaluated on a separate held-out one. On
that held-out set, **0% of genuine cards were wrongly marked invalid**. Full numbers, method and limitations are in
[docs/ENGINE.md](docs/ENGINE.md).

---

<!-- Person 2: add Screenshots, Quick Start, Architecture, Features and Team sections below. -->

## Engine and evaluation

See [docs/ENGINE.md](docs/ENGINE.md) for the validation pipeline, threshold tuning, held-out results and
limitations.

## Sources

- [TNeGA e-Sevai portal](https://www.tnesevai.tn.gov.in/)
- [TNeSevai citizen guide: services, CAN, documents, status](https://anantamias.com/tnesevai/)
- [DT Next: TN to simplify revenue certificate process (July 2026)](https://www.dtnext.in/news/tamilnadu/tn-to-simplify-revenue-certificate-process-lesser-steps-faster-process-lower-corruption)
- [DT Next: Ensure hassle-free services at e-Seva centres (July 2026)](https://www.dtnext.in/news/tamilnadu/ensure-hassle-free-services-at-e-seva-centres-tamil-nadu-government)
- [NIC: e-District revenue services launch in Tamil Nadu](https://informaticsweb.nic.in/news/launch-e-district-revenue-services-government-tamilnadu-15th-october-2010)
- [Puducherry caste certificate workflow (VAO → RI → Tahsildar), for comparison](https://revenue.py.gov.in/downloads/EODB/EODB-Caste%20Certificate.pdf)
