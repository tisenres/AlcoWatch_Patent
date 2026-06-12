# Insertion Guide — ACN1408 CAP AI Disclosure Package

**Audience:** the patent agent (primary) / applicant filing the Complete-After-Provisional
(CAP) specification for **ACN1408** before **2026-06-27**. This package supplies the AI
disclosure (text + drawings); it does not draft claims, the abstract, or the full legal
specification.

## What is in `patent_cap/`

| File | Purpose | Where it goes in the Form-2 Complete Specification |
|---|---|---|
| `Drawings_ACN1408_CAP.docx` | 5 figures, one per labelled A4 sheet (1-bit line art) | The **Drawings** sheets (replaces the provisional's photo-based Figure 1; the provisional sequence figure is redrawn as compliant line art) |
| `disclosure_ai_section.md` | Enablement-level AI/model disclosure, cites reference numerals | The **Detailed Description** (AI framework, model, training, deployment, operation, state machine) |
| `reference_numerals.md` | Numeral → component lookup (21 numerals) | The **reference-numeral list** / merge into the description's numeral usage |
| `provisional_reconciliation.md` | 6 code-vs-provisional deltas to resolve | **Read first** — decide claim/description framing before filing |
| `figures/*.pdf` | Vector versions of each figure | Use if the office prefers vector line art on the sheets (see note below) |

## Order of work

1. **Read `provisional_reconciliation.md` first.** Six points where the as-built embodiment
   is narrower than / differs from the provisional (EDA estimated vs sensed; no transdermal
   sensor; synthetic vs large-scale data; fixed vs dynamic thresholds; biometric auth shown
   but absent; AES-256 specified vs implemented). Decide, per item, whether to keep the
   code-faithful framing in `disclosure_ai_section.md` or amend the provisional/claims.
2. Insert `disclosure_ai_section.md` into the Detailed Description; adjust voice to match
   the rest of the specification.
3. Place the five sheets from `Drawings_ACN1408_CAP.docx` into the Drawings section; renumber
   if the filing already contains other figures.
4. Confirm the reference-numeral list matches `reference_numerals.md`.

## Compliance & format notes

- All five figures are **pure 1-bit black-on-white line art** (verified by
  `check_compliance.py`: zero mid-grey shading), meeting the office's "2D line diagrams only"
  requirement (no photographs, no greyscale, no colour).
- `Drawings_ACN1408_CAP.docx` embeds the **PNG** rasters. If the office requires **vector**
  line art on the sheets, substitute the matching `figures/<name>.pdf` (python-docx cannot
  embed PDF directly, so the vectors are delivered separately). **Confirm the accepted format
  with the office.**
- Sheet headers are reconstructed per page (Applicant, Total no. of sheets: 05, Sheet no: 0N).
  The provisional's drawings packed two figures on one sheet; this package uses one figure per
  sheet, which is the conventional patent layout.

## Regenerating the package

Everything is reproducible (no manual image editing):

```bash
cd patent_cap
for f in gen/fig*.py; do python3 "$f"; done        # render all 5 figures (PDF + 1-bit PNG)
python3 - <<'PY'                                    # regenerate the numeral table
import sys; sys.path.insert(0, '.'); import patent_style as ps
open('reference_numerals.md','w').write(
  "# Reference Numerals\n\n" + ps.numeral_table() + "\n")
PY
python3 gen/assemble_drawings.py                    # rebuild Drawings_ACN1408_CAP.docx
python3 check_compliance.py                         # must print COMPLIANCE: PASS
```

Reference-numeral definitions and component descriptions live in one place
(`patent_style.py`), so a numeral change propagates to every figure, the table, and the
compliance check.
