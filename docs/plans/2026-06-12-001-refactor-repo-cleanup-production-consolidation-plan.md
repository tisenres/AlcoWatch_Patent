---
title: "refactor: Repo Cleanup & Production Consolidation (alcohol patent only)"
type: refactor
status: active
date: 2026-06-12
origin: docs/brainstorms/2026-06-12-repo-cleanup-production-consolidation-requirements.md
deepened: 2026-06-12
---

# refactor: Repo Cleanup & Production Consolidation (alcohol patent only)

## Summary

Reorganize the repository on a dedicated `chore/repo-cleanup` branch taken off **`main`** (already alcohol-clean): **materialize** the NTCC and Stress-Detection files from `feat/stress-recognition` into an in-repo `archive/` folder (they do not exist on `main`, so they are pulled from the branch, not moved), cherry-pick the single alcohol-core commit, establish the latest patent paper (version A, latexdiff-cleaned) as the canonical source, force-add the gitignored binaries that production and the archive must retain, scrub junk and harden `.gitignore`, rewrite the guides, then merge to `main`, push, and delete the stress branch.

> **Doc-review round 1 (2026-06-12) corrected a P0 in the first draft:** the original plan tried to `git mv` NTCC/stress paths on a `main`-based branch where those paths do not exist. This version materializes branch-tracked content via `git checkout feat/stress-recognition -- <path>` (which stages the entry, preserving tracking even for gitignored extensions) and `git add -f` for untracked-origin binaries. See Key Technical Decisions.

---

## Problem Frame

Three overlapping bodies of work (alcohol patent, NTCC paper, Stress Detection "Major Project") were built in the same tree and on `feat/stress-recognition`, leaving the working tree, branch history, top-level binaries, `docs/`, and the guide files intermixed. NTCC is finished and Stress is no longer part of the patent's identity; the user wants a clean alcohol-only `main` before starting the next task. See origin for the full pain narrative and decisions.

---

## Requirements

- R1. Freeze all NTCC + Stress work recoverably before any deletion (in-repo `archive/` folder).
- R2. Archive layout: `archive/ntcc-paper/` and `archive/stress-major-project/`.
- R3. Each archive subfolder gets a short README (what it is, frozen, date).
- R4. `main` retains core AlcoWatch system, patent docs, canonical paper, rewritten guides.
- R5. `paper_reproduction/` (LiPb ML) stays untouched.
- R6. Carry alcohol-core improvements off `feat/stress-recognition` onto `main`; keep `main` history free of stress/NTCC code.
- R7. Canonical patent paper = version A (`AlcoWatch_New`), stored clean in repo.
- R8. Strip all latexdiff markup from the canonical paper; must compile against `WileyNJDv5.cls` with no artifacts.
- R9. Remove superseded patent exports from production; advise which two Overleaf projects to delete.
- R10. Clean the working tree (junk + pending deletions/modifications).
- R11. Update `.gitignore` to cover `*.pptx`, `*.zip`, `*_saved_model/`, keeping intentionally-tracked + force-added figures/binaries.
- R12. Delete `feat/stress-recognition` (local + origin) after work lands.
- R13. Rewrite `README.md`, `CLAUDE.md`, `AGENTS.md` for alcohol-only; fix dead `overleaf_papers/` reference.
- R14. Reorganize `docs/`; move NTCC/stress docs to archive.

**Origin actors:** A1 (User/Anastasiia — owns Overleaf + repo), A2 (future contributors/agents reading the index)

---

## Scope Boundaries

- No functional changes to the ML model, Wear OS app, or Arduino firmware — reorganization only.
- No editing of patent paper content/wording — only de-duplication and latexdiff cleanup.
- `paper_reproduction/` left as-is (not archived, not refactored).
- The next task (post-cleanup) is out of scope.
- Deleting the two superseded Overleaf projects is the user's manual action; we only secure the source and advise.

### Deferred to Follow-Up Work

- Disposition of archived heavy binaries (track in-repo vs. Git LFS vs. drop) — default: keep in `archive/` now; revisit if clone size becomes a problem.

---

## Context & Research

### Verified Facts (doc-review round 1, against the live repo)

- `main` (`732b054e`) contains **no** stress/NTCC files (`git ls-tree -r main` → 0 for `ntcc/`, `stress_detection/`, `paper_figures/stress/`, `arduino/stress_cabin_control/`, `research_papers/`, `docs/superpowers/`). **Consequence:** archive content must be sourced from `feat/stress-recognition`, not moved on a main-based branch.
- Alcohol-core improvement = single commit `691e3857` (`feat(ml): rewrite training pipeline with Widmark curves`). Its parent is exactly `main` (`732b054e`), touches only `ml_model/training/bac_estimation_model.py`, `ml_model/training/train_model.py`, `ml_model/data/dataset_loader.py`. Clean cherry-pick, no stress hunks possible.
- `SensorManager.kt`'s only branch change is in `6c1675e8` (stress accelerometer/BLE) → **confirmed stress-only, not ported** (resolves origin R6's "alcohol portions of SensorManager.kt" — there are none).
- **Branch-tracked stress files OUTSIDE the first draft's inventory** (must be materialized into archive): `tests/stress_detection/**` (4), `wear_os_app/app/src/main/java/com/alcowatch/wearos/stress/**` (3) + `ble/StressBLECharacteristic.kt` + `assets/STRESS_MODEL_README.txt`, and `research_papers/Anastasiia_Major_Project/**` (21 tracked `.tex`/`.pdf`/`.bib` files — **tracked**, not untracked as first drafted).
- **Gitignored binaries** (confirmed via `git check-ignore`): the two patent `.docx`, NTCC `.pdf`/`.docx`, all `.pptx`, `.zip`, paper `.pdf`/`.jpg` figures, and `ml_model/models/*.json` are ignored. Plain `git add` skips them silently → they need `git add -f`.
- Untracked alcohol artifacts in the working tree: `ml_model/models/{ablation_metrics,attention_weights,evaluation_metrics,predictions_data,scaler_params,tflite_evaluation_metrics,training_history}.json` and `ml_model/models/{bac_model,test_model}_saved_model/`. The ported `train_model.py` writes `models/scaler_params.json` (deployment-critical).
- `ntcc_paper_overleaf.zip` is tracked only on the branch (not main), `D`-status in the current working tree → materialize from branch; it appeared in two dispositions in the first draft (archive vs remove) — **archive only**.

### Materialization mechanic (key)

`git checkout feat/stress-recognition -- <path>` stages the branch's version of `<path>` into the index at its original location, **bypassing `.gitignore`** (explicit checkout overrides ignore). A subsequent `git mv <path> archive/...` moves the tracked index entry into the archive, **preserving tracking even for `.pdf`/`.png` extensions** — no force-add needed for branch-tracked content. `git add -f` is required only for **untracked-origin** binaries (the loose `.pptx`/`.zip`, `from_overleaf/` assets, the alcohol `.json`s, the patent `.docx`s, the NTCC `.pdf`/`.docx`).

### Institutional Learnings

- No `docs/solutions/` directory — no prior learnings to carry.
- Memory: canonical version verdict in `project_paper_revision.md` / `project_repo_cleanup_2026_06.md`.

### External References

- None needed; git/filesystem reorganization, not new code against an unfamiliar framework.

---

## Key Technical Decisions

- **Branch `chore/repo-cleanup` off `main`, materialize archive content from `feat/stress-recognition`** — keeps `main`'s history linear and free of stress/NTCC commits by construction (origin R6), while still sourcing the files that only exist on the branch. Fixes the round-1 P0 (`git mv` on a base lacking the sources).
- **`git checkout feat -- <path>` + `git mv` for branch-tracked content; `git add -f` for untracked-origin binaries** — single coherent mechanic that survives the `.gitignore` rules. A pre-merge gate (`git ls-files` enumerates every expected archived + retained binary) guarantees nothing was silently skipped.
- **Port core via cherry-pick of `691e3857` only** — sole pure-alcohol improvement; its parent is `main`, so it applies cleanly with no stress content.
- **Archive = in-repo folder (user decision); annotated tag `archive/stress-ntcc-snapshot` is a secondary history net only** — the tag preserves *committed* history at the branch tip but does **not** preserve untracked files; the browsable `archive/` folder (with force-added binaries) is the sole preservation path for untracked artifacts. Kept as cheap insurance, not a substitute for the folder (reconciles origin's "folder, not tags").
- **Canonical paper cleaned with latexdiff reverse, fallback scripted unwrap** — produces a faithful clean master without brace artifacts; gated on a successful compile.
- **The cleanup's own brainstorm + plan docs stay tracked in `docs/`** — they are this repo's operational history, not a project domain, so they are committed (not archived, not deleted).

---

## Open Questions

### Resolved During Planning

- Base branch + move mechanic? → Branch off `main`; materialize branch content via `git checkout feat -- <path>` then `git mv`; force-add untracked binaries (see mechanic above).
- Which core changes to port? → Only `691e3857`. `SensorManager.kt`/sim/firmware changes are stress (verified).
- Where does the canonical paper live? → `overleaf_papers/` (matches the guide reference U7 fixes).
- Where do the cleanup's own docs go? → Stay tracked in `docs/` as operational history.

### Deferred to Implementation

- Exact latexdiff-reverse invocation vs. scripted unwrap if the diff file resists reverse — confirm the cleaned `.tex` compiles before deleting the source zip.
- Whether to **force-add** the current untracked alcohol `*.json` (incl. deployment `scaler_params.json`) or **regenerate** them via a `train_model.py` run — default: force-add the existing ones for reproducibility, note regeneration as the alternative (U4).
- Disposition of `research_papers/photo_2025-06-26_13-03-02.jpg` and the second patent docx `Smartwatch Alcohol Prevention Patent (1).docx` (keep on main vs archive) — default: keep both patent docx on main, drop the loose photo unless the user wants it (U6).

---

## Output Structure

    archive/
      ntcc-paper/            # frozen NTCC: ntcc/** sources, overleaf zip+dir, report docx, university pdf, deck, NTCC docs
        README.md
      stress-major-project/  # frozen stress: stress_detection/**, tests/stress_detection/**, wear_os stress sources,
        README.md            #   paper_figures/stress/**, arduino/stress_cabin_control/**, scripts, Major Project report+zip, deck, docs
    overleaf_papers/         # canonical patent paper (version A, latexdiff-cleaned) + force-added assets
      wileyNJDv5_AMA.tex
      ...
    research_papers/         # force-added: patent .docx (+ kept alcohol-only artifacts)
    ml_model/  wear_os_app/  arduino/  shared/  tests/  paper_reproduction/   # alcohol core (tests/stress_detection removed)
    docs/                    # alcohol-only guides + cleaned index + this cleanup's own brainstorm/plan

---

## Implementation Units

### U1. Set up cleanup branch and safety snapshot

**Goal:** Create the working branch on the correct base and a recoverability net before any destructive step.

**Requirements:** R1, R6, R12

**Dependencies:** None

**Files:**
- No file changes (git refs only)

**Approach:**
- Create annotated tag `archive/stress-ntcc-snapshot` at `feat/stress-recognition` tip (`40a38b78`) and push it — preserves committed NTCC/stress history. Note in the tag message that it does **not** cover untracked files.
- Branch `chore/repo-cleanup` off **`main`** (`732b054e`).
- Note for implementers: untracked working-tree files (loose `.pptx`/`.zip`, `from_overleaf/`, `ml_model/models/*.json`, ignored patent docx/pdf) persist across the branch switch and remain available; branch-*tracked* stress/NTCC files will leave the working tree on switch and must be materialized from the branch in U2/U3.

**Test expectation:** none — git-ref setup.

**Verification:**
- `chore/repo-cleanup` exists off `main`; `git tag` lists `archive/stress-ntcc-snapshot` at the branch tip and it is on `origin`.

---

### U2. Materialize and archive NTCC → `archive/ntcc-paper/`

**Goal:** Freeze all NTCC artifacts into a labeled archive folder, sourcing branch-tracked content correctly.

**Requirements:** R1, R2, R3

**Dependencies:** U1

**Files (branch-tracked → `git checkout feat -- <path>` then `git mv` into `archive/ntcc-paper/`):**
- `ntcc/**`, `ntcc_paper_overleaf.zip`
**Files (untracked-origin in working tree → move + `git add -f`):**
- `ntcc_paper_overleaf/`, `Anastasiia_NTCC (2).pptx`, `research_papers/Anastasiia_NTCC_University.pdf`, `research_papers/NTCC_Project_Report_Alcohol_Detection_Software.docx`
**Create:** `archive/ntcc-paper/README.md`

**Approach:**
- Materialize branch-tracked NTCC paths, then relocate under `archive/ntcc-paper/`.
- Move the untracked NTCC binaries into the same folder and force-add (they match `*.pdf`/`*.docx`/`*.pptx` ignores).
- README: completed NTCC university submission, frozen 2026-06-12, not maintained; points to the snapshot tag for history.
- `ntcc_paper_overleaf.zip` is archived here only (not also "removed" — corrects the round-1 double-listing).

**Patterns to follow:** mirror U3's README tone.

**Test expectation:** none — file relocation.

**Verification:**
- `git ls-files archive/ntcc-paper/` lists every NTCC source, the overleaf zip+dir, report docx, university pdf, deck, and README (i.e., force-adds actually landed).
- No NTCC files remain in live locations.

---

### U3. Materialize and archive Stress → `archive/stress-major-project/`

**Goal:** Freeze the **complete** Stress project (incl. the paths the first draft missed) into a labeled archive folder.

**Requirements:** R1, R2, R3

**Dependencies:** U1

**Files (branch-tracked → `git checkout feat -- <path>` then `git mv` into `archive/stress-major-project/`):**
- `stress_detection/**` (tracked files only), `paper_figures/stress/**`, `arduino/stress_cabin_control/**`
- `scripts/generate_stress_figures.py`, `scripts/generate_defense_diagrams.py`, `scripts/build_major_project_pptx.py`
- `tests/stress_detection/**`
- `wear_os_app/app/src/main/java/com/alcowatch/wearos/stress/**`, `.../ble/StressBLECharacteristic.kt`, `.../assets/STRESS_MODEL_README.txt`
- `research_papers/Anastasiia_Major_Project/**` (tracked — 21 files)
**Files (untracked-origin → move + `git add -f`):**
- `Anastasiia_Major_Project_Defense.pptx`, `major_project_overleaf.zip`, `research_papers/Anastasiia_Major_Project.zip`
**Create:** `archive/stress-major-project/README.md`

**Approach:**
- Materialize all branch-tracked stress paths (note the wear_os/tests/Major-Project paths added after round-1 review) and relocate under `archive/stress-major-project/`.
- Exclude `venv/`, `__pycache__/`, `*_saved_model/`, `*.npy` model outputs inside `stress_detection/` — those are not archived (covered by the snapshot tag if needed; scrubbed in U6). State this explicitly so the freeze scope is unambiguous.
- README: WESAD-based "Major Project", frozen 2026-06-12, not maintained; points to the snapshot tag.

**Test expectation:** none — file relocation.

**Verification:**
- `git ls-files archive/stress-major-project/` lists the stress project, `tests/stress_detection`, wear_os stress sources, the Major Project report (21 files), figures, firmware, scripts, deck+zip, README.
- No stress files remain in any live location.

---

### U4. Port alcohol-core improvement and alcohol artifacts

**Goal:** Carry the one genuine alcohol-core improvement plus the deployment artifacts it depends on; keep `main` clean of stress.

**Requirements:** R4, R6

**Dependencies:** U1

**Files:**
- Modify (via `git cherry-pick 691e3857`): `ml_model/training/bac_estimation_model.py`, `ml_model/training/train_model.py`, `ml_model/data/dataset_loader.py`
- Add (untracked alcohol artifacts, `git add -f` as needed): `ml_model/models/scaler_params.json` (deployment-critical) and the alcohol metric JSONs (`ablation_metrics`, `attention_weights`, `evaluation_metrics`, `predictions_data`, `tflite_evaluation_metrics`, `training_history`)

**Approach:**
- `git cherry-pick 691e3857` (parent is `main`; verified pure-alcohol, no stress hunks).
- **Record the verified conclusion** that `6c1675e8`'s `SensorManager.kt` change is stress accelerometer/BLE only → not ported (traceability for origin R6).
- Decide on the untracked alcohol JSONs: default **force-add the current files** (so the deployment scaler + metrics ride to `main`); alternative is to **regenerate** via a `train_model.py` run. Do not expect them inside the cherry-pick — they are working-tree outputs, not in `691e3857`.
- `*_saved_model/` dirs are regenerable inference outputs → scrubbed in U6, not committed.

**Test expectation:** none here — porting already-tested code. Functional behavior is covered by existing simulation/tests, not this reorg.

**Verification:**
- The three ML files on `chore/repo-cleanup` match the branch's improved versions; no stress identifiers introduced.
- `git ls-files` shows `ml_model/models/scaler_params.json` (and chosen metric JSONs) tracked, OR a note records they will be regenerated.

---

### U5. Establish canonical patent paper (version A, latexdiff-cleaned)

**Goal:** Make version A the single canonical patent source, clean and compilable.

**Requirements:** R7, R8, R9

**Dependencies:** U1

**Files:**
- Create: `overleaf_papers/` populated from `from_overleaf/AlcoWatch_New.zip` (cls, fonts, bib, tikz, figures) with a cleaned `wileyNJDv5_AMA.tex`; force-add binary assets (`*.pdf`, `rhlogo.jpg`) since those extensions are ignored
- Remove (loose, **gated** — see Approach): `from_overleaf/` zips after a successful compile

**Approach:**
- Extract `AlcoWatch_New.zip`; strip latexdiff markup (latexdiff reverse, fallback scripted unwrap) → no `%DIF`/`\DIFadd`/`\DIFdel`, no `\subsection{{` artifacts.
- **Verify the cleaned `.tex` compiles against the bundled `WileyNJDv5.cls`** producing the ~8.3k-word expanded content (Ablation / Confusion Matrix / Attention / Discussion / Limitations).
- **Confirm the zip supersedes the branch Wiley files** before relying on it: diff `AlcoWatch_New.zip`'s tex against `feat/stress-recognition:Wiley_New_Journal_Design_version_5__NJD_v5___5_/wileyNJDv5_AMA.tex`; the zip (8.3k words, corrected metrics) must be the superset. The branch Wiley dir is not on `main`, so nothing to "remove" — it simply is not materialized.
- **Zip deletion is a separate step performed only after the compile succeeds** (so a corrupted clean `.tex` never leaves the project source-less).

**Test expectation:** none (LaTeX); compilation is the gate.

**Verification:**
- `overleaf_papers/wileyNJDv5_AMA.tex` has zero `%DIF`/`\DIFadd`/`\DIFdel` tokens and no brace artifacts; compiles to the expanded PDF.
- `git ls-files overleaf_papers/` includes the force-added figure assets.
- `from_overleaf/` zips removed only after a confirmed compile.

---

### U6. Retain patent docs, scrub junk, harden `.gitignore`

**Goal:** Ensure production keeps its promised binaries, remove junk, prevent recurrence — in the correct order.

**Requirements:** R4, R10, R11

**Dependencies:** U2, U3, U4, U5

**Files:**
- Force-add (gitignored, must land on `main`): `research_papers/ACN1408 Prov._Patent_130625.docx`, `research_papers/Smartwatch Alcohol Prevention Patent (1).docx`
- Delete (junk): `venv/`, `**/__pycache__/`, `ml_model/models/*_saved_model/`, `.DS_Store`, stray `.pytest_cache/`
- Modify: `.gitignore`

**Approach:**
- **Force-add the retained patent docx first** (R4 promises them; `*.docx` is ignored). Decide the loose `photo_2025-06-26_13-03-02.jpg` and second docx per the Open Question default (keep both docx; drop the photo unless wanted).
- Delete build/cache/env artifacts and the regenerable `*_saved_model/` dirs.
- **Then** extend `.gitignore` with `*.pptx`, `*.zip`, `*_saved_model/` (confirm `venv/`, `__pycache__/`, `.DS_Store` covered). Correct the round-1 false claim — archived/retained binaries are protected because they were **force-added** in U2/U3/U5/U6, not because they were "already committed"; the new ignores only stop *future* strays.

**Test expectation:** none — hygiene/ignore change.

**Verification:**
- `git ls-files` lists the patent docx and every expected archived/overleaf binary (the consolidated force-add gate).
- `git status` clean; a new stray `*.pptx`/`*.zip`/`*_saved_model/` is ignored; previously force-added figures/binaries remain tracked.

---

### U7. Rewrite guides and reorganize `docs/`

**Goal:** Make the index read as a single alcohol-patent project.

**Requirements:** R4, R9, R13, R14

**Dependencies:** U2, U3, U5

**Files:**
- Modify: `README.md`, `CLAUDE.md`, `AGENTS.md`
- Materialize-then-move into `archive/*/`: NTCC/stress planning docs tracked on the branch (`docs/superpowers/**`), and the on-`main`-or-branch paper-regeneration docs (`docs/brainstorms/2026-04-05-*`, `docs/plans/2026-04-0{6,7}-*`) that pertain to NTCC/stress
- Keep tracked in `docs/`: `docs/IMPLEMENTATION_GUIDE.md`, `docs/QUICK_START.md`, `docs/SYSTEM_SUMMARY.md`, `docs/diagrams/`, and **this cleanup's own** `docs/brainstorms/2026-06-12-*` + `docs/plans/2026-06-12-001-*` (operational history)

**Approach:**
- `CLAUDE.md`: fix the dead `overleaf_papers/` reference (now real after U5), drop NTCC/IEEE-humanized rows, point the paper table at the canonical source, add a one-line `archive/` pointer.
- `README.md` / `AGENTS.md`: remove NTCC/stress from the live narrative; describe the alcohol patent only; correct the research-papers list.
- Move NTCC/stress planning docs into their archive folders; explicitly keep the cleanup's own docs in `docs/`.

**Test expectation:** none — documentation.

**Verification:**
- No live guide references NTCC or stress except an explicit `archive/` pointer; `overleaf_papers/` reference resolves.
- `docs/` top level holds only alcohol-relevant guides + index + this cleanup's own brainstorm/plan.

---

### U8. Merge to `main`, push, delete stress branch

**Goal:** Land production and remove the obsolete branch — only after preservation is proven.

**Requirements:** R12

**Dependencies:** U2, U3, U4, U5, U6, U7

**Files:**
- No new file changes (git operations)

**Approach:**
- **Pre-merge preservation gate (blocks deletion):** run a checklist that `git ls-files` on `chore/repo-cleanup` enumerates every expected archived binary (decks, zips, NTCC pdf/docx, Major Project report), every retained production binary (patent docx, overleaf figures), and the alcohol JSONs — confirming the `.gitignore` rules did not silently drop anything. If any expected file is missing, stop and force-add it before proceeding.
- Confirm `git status` clean and U1–U7 verifications pass.
- Merge `chore/repo-cleanup` → `main` (no-ff). If `main` has branch protection, open a PR instead of a direct push (note for implementer).
- Push `main`. Delete `feat/stress-recognition` locally and on `origin` — committed history safe via the `archive/stress-ntcc-snapshot` tag; untracked artifacts safe because they were force-added into `archive/` and verified by the gate above.
- Surface to the user: keep Overleaf project **`AlcoWatch_New`**; delete **`AlcoWatch_New_06_04`** and **`Wiley_New_Journal_Design_version_5`**.

**Test expectation:** none — git operations.

**Verification:**
- `main` contains `archive/` (complete per U2/U3 inventories), `overleaf_papers/`, ported ML core + alcohol JSONs, retained patent docx, cleaned guides; no live stress/NTCC.
- The pre-merge gate passed: every enumerated binary is in `git ls-files`.
- `feat/stress-recognition` gone locally and on `origin`; `archive/stress-ntcc-snapshot` tag remains.
- A fresh clone of `main` reads as an alcohol-only project and contains the patent docx + canonical paper.

---

## System-Wide Impact

- **Interaction graph:** No runtime code paths change behavior. Production `wear_os_app`/`arduino` = `main`'s versions (never had stress refs), so removing stress sources from production is automatic (they are simply not on `main`); only the ML training files advance via U4.
- **State lifecycle risks:** Destructive steps (branch delete, junk removal, zip deletion) are each gated: branch deletion behind the U8 preservation gate + tag; zip deletion behind a successful compile (U5); junk removal after force-adds (U6).
- **API surface parity:** None — BLE protocol, model I/O, firmware pins unchanged.
- **Unchanged invariants:** `paper_reproduction/`, core `ml_model` architecture/`shared` protocols, all app/firmware behavior explicitly not changed.

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Archive sources absent on a main-based branch (round-1 P0) | Materialize branch-tracked content via `git checkout feat -- <path>` + `git mv`; force-add untracked binaries (Key Decisions) |
| `.gitignore` silently drops archived/retained binaries on `git add` | Explicit `git add -f` for every untracked ignored binary; U8 pre-merge `git ls-files` gate enumerates them all before deletion |
| Inventory misses branch-tracked stress files (tests, wear_os stress, Major Project report) | Inventory extended in U3 after review; verification checks `git ls-files archive/...` counts |
| Branch deletion loses untracked artifacts the tag can't hold | Untracked binaries force-added into `archive/` and verified by the U8 gate; tag is history-only insurance |
| latexdiff cleanup corrupts the canonical `.tex` | latexdiff reverse + gate on a successful compile against `WileyNJDv5.cls` **before** deleting the source zip (U5) |
| Deployment `scaler_params.json` lost on branch deletion | Force-added (or regenerated) in U4, not assumed inside the cherry-pick |
| `main` branch protection blocks direct push | Fall back to a PR for the merge (U8 note) |
| Archived heavy binaries bloat clone size | Accepted for now; LFS/drop deferred (Scope Boundaries) |

---

## Sources & References

- **Origin document:** docs/brainstorms/2026-06-12-repo-cleanup-production-consolidation-requirements.md
- Doc-review round 1 (2026-06-12): feasibility P0 (base-branch/`git mv`), adversarial P1 (inventory gaps, gitignore drop, tag-only recovery), scope-guardian P1 (R6 trace), coherence (clean)
- Clean base branch: `main` @ `732b054e`; core-port commit `691e3857` (parent == `main`)
- Canonical paper: `from_overleaf/AlcoWatch_New.zip`
- Memory: `project_paper_revision.md`, `project_repo_cleanup_2026_06.md`
