# ATAR verification — 2026-09-26

> Produced by re-fetching every course URL in `src/courses.js` and reading what the
> page currently publishes. **Nothing in `courses.js` was changed.**

**54 courses checked** — confirmed **2** · a different figure published **5** · no threshold readable **16** · blocked **31**

Only `confirmed` and `differs` say anything about whether a stored number is right.
`differs` is deliberately flat — the fetch can see a published threshold that is not
the stored one, but it cannot tell a course page from a listing page quoting other
degrees. Which of them matter is judged below, from the quoted text.

The stored values come from the BEAM workbook, whose own update stamps stop in 2024
and whose ATAR figures are labelled in-sheet as *"2020 score … reference for 2022"*.
They were never current for a 2026 intake.

---

## What could and could not be checked

**31 of 54 sites refuse automated requests (HTTP 403).** That is bot protection, not an outage:

- `Monash University Malaysia` (9)
- `Deakin University` (8)
- `International Medical University (IMU)` (7)
- `Monash University (Australia)` (3)
- `James Cook University` (2)
- `Macquarie University` (1)
- `University of Notre Dame` (1)

These cannot be verified without a browser. Evading the block is not an option;
check them by hand or accept them as unverified.

## Confirmed still published

- **Curtin University — Medicine** · stored `95.0`
  > 95 Minimum ATAR or equivalent See all entry requirements and course prerequisites Duration Duration The time it will take to complete the course if you study full-time.
- **Royal College of Surgeons in Ireland — Medicine** · stored `95.0`
  > Australia Five-year track (exempt from Foundation Year) ATAR required: minimum 95.

## A different figure is published

Read these with the caveat above. `RMIT — Pharmacy` is a clean single threshold on
the course page. `RMIT — Biomedical sciences` is also the course page, quoting two
recent years. The three `University of Western Australia` rows resolve to one general
engineering page whose ATAR 88 / 98 belong to *other* degree combinations, so they are
**not** evidence that the stored 80.0 is wrong.

- **RMIT University — Biomedical sciences** · stored `70.95`
  > page publishes 70 || Not an international student? Switch to local content Student type: Domestic International Learning mode: On campus Entry score: 2027 Guaranteed ATAR 70.
- **RMIT University — Pharmacy** · stored `75.75`
  > page publishes 81 || Not an international student? Switch to local content Student type: Domestic International Learning mode: On campus Entry score: ATAR 81.
- **University of Western Australia — Biomedical Engineering** · stored `80.0`
  > page publishes 88, 98 || Duration: 5 years* ATAR: 88 Bachelor of Engineering (Honours) and Bachelor of Philosophy (Honours) Ideal for high-achievers with a passion for engineering, this combined degree gives you the
- **University of Western Australia — Chemical engineering** · stored `80.0`
  > page publishes 88, 98 || Duration: 5 years* ATAR: 88 Bachelor of Engineering (Honours) and Bachelor of Philosophy (Honours) Ideal for high-achievers with a passion for engineering, this combined degree gives you the
- **University of Western Australia — Civil engineering** · stored `80.0`
  > page publishes 88, 98 || Duration: 5 years* ATAR: 88 Bachelor of Engineering (Honours) and Bachelor of Philosophy (Honours) Ideal for high-achievers with a passion for engineering, this combined degree gives you the

## Two things worth a human decision

1. **`RMIT University — Pharmacy`**: stored `75.75`, but the course page currently
   shows `Entry score: ATAR 81` for the international view. If 81 is current, the
   stored figure understates the requirement by ~5 points.

2. **`RMIT University — Biomedical sciences`**: stored `70.95`. That is *exactly*
   `history.js`'s cohort `atarMean` (70.95) — an odd coincidence for an admissions
   threshold. RMIT currently publishes a **Guaranteed ATAR of 70** (2027) and
   **70.40** (2026 lowest selection rank), neither of which is 70.95.
   I tried to recompute the cohort mean independently from the workbook's
   `Historical data` sheet and **could not reproduce it** (my flattened-text column
   heuristic yields max 86.5 / mean ~64, against the claimed max 99.65 / mean 70.95),
   so I am **not** asserting the mean is wrong and **not** asserting a copy error.
   The exact equality is a fact; what it means is unproven. Worth 5 minutes by hand.

## A pathway the data is missing

`Royal College of Surgeons in Ireland — Medicine` is stored as a single value `95.0`,
which the page does confirm — but the same page also states:

> Five-year track (exempt from Foundation Year) **ATAR required: minimum 95**
> Six-year track **ATAR required: 85**

A 10-point-lower route to the same degree is absent from `courses.js`.

## Also worth knowing

- All six `Sunway University` rows point at the same generic homepage — the fetched bytes are identical for courses 46–51 — so the page carries no course information at all. Sunway is the home institution and these are the lowest-threshold options (ATAR 55–65), yet **none of those numbers has any public source on the linked page**.
- `National University of Singapore` returns a 212-byte JavaScript stub — the ATAR cannot be read without running the page.
- `University of Western Australia`'s three engineering links all resolve to one general engineering page quoting ATAR 88 / 98 for *other* degree combinations, so the stored 80.0 is neither confirmed nor contradicted.

## Recommended next step

Do not bulk-refresh. Only **7** of 54 courses publish a readable threshold at all, so a bulk refresh would replace
47 unverified numbers with guesses. The two rows above are the concrete problems. A useful
addition to `courses.js` would be per-row provenance — `verified_on` + `source` — so a
2020-era number can never again be read as current.

