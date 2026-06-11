---
date: 2026-06-12
topic: repo-cleanup-production-consolidation
---

# Repo Cleanup & Production Consolidation

## Summary

Reorganize the AlcoWatch repository so that `main` (production) contains **only the core alcohol-detection patent project**. The NTCC paper and the Stress Detection (Major Project) work — both built inside this repo — are preserved as frozen snapshots under a single `archive/` folder, the live alcohol-core improvements that currently exist only on `feat/stress-recognition` are carried onto `main`, the latest patent paper (Overleaf version A) is cleaned and stored as the canonical source, stray branches are deleted, and the guide/index docs are rewritten to describe one project.

---

## Problem Frame

This repository accumulated three overlapping bodies of work over time: the **AlcoWatch alcohol-detection patent** (the original and ongoing goal), an **NTCC university paper**, and a **Stress Detection "Major Project"** (WESAD-based BiLSTM classifier, defense deck, separate Wiley/report artifacts). All three were developed in the same tree and on the same `feat/stress-recognition` branch, so the working tree, branch history, top-level binaries, `docs/`, `scripts/`, `paper_figures/`, and the guide files (`README.md`, `CLAUDE.md`, `AGENTS.md`) now intermix all three.

Concretely this causes: an uncommitted working tree with deletions and untracked junk (`venv/`, `*_saved_model/`, `.pptx`, `.zip`, `.DS_Store`); a `CLAUDE.md` that points at an `overleaf_papers/` directory that does not exist; **three** Overleaf exports of the same patent paper at different word counts with no single source of truth; and alcohol-core code improvements (updated Wiley article, model/training edits) stranded on a feature branch named after stress. NTCC is finished and Stress Detection is no longer part of the patent's identity, so the cost is ongoing confusion about what "the project" even is — which blocks the next task the user wants to start on a clean base.

---

## Actors

- A1. **User (Anastasiia)** — owns the Overleaf projects and the GitHub repo; will delete the two superseded Overleaf projects after the canonical source is secured in-repo; will hand a new task once cleanup is done.
- A2. **Future contributors / agents** — read `README.md` / `CLAUDE.md` / `AGENTS.md` and `docs/` as the index to understand the project; must come away understanding it as the alcohol patent only.

---

## Requirements

**Preservation (no data loss)**
- R1. Before any deletion, freeze the full current state of `feat/stress-recognition` so all NTCC + Stress work remains recoverable. Mechanism: create an `archive/` folder in `main` containing the NTCC and Stress artifacts as static snapshots (chosen over git-only tags per Key Decisions).
- R2. Archive layout: `archive/ntcc-paper/` (NTCC paper sources, report, university PDF, NTCC pptx, NTCC `docs/superpowers` plan+spec) and `archive/stress-major-project/` (the `stress_detection/` project, `paper_figures/stress/`, stress firmware `arduino/stress_cabin_control/`, stress scripts, Major Project defense deck + zip, stress `docs/superpowers` plan+spec).
- R3. Each archive subfolder gets a short `README.md` stating what it is, that it is frozen/not maintained, and the date archived.

**Production `main` composition**
- R4. `main` retains: core AlcoWatch system (`ml_model/`, `wear_os_app/`, `arduino/firmware/`, `shared/`, `tests/`, `main.py`, `RUN_SIMULATION.sh`), the alcohol patent docs (`research_papers/` patent `.docx`), the canonical patent paper source (see R7), and the rewritten guides/`docs/`.
- R5. `paper_reproduction/` (LiPb ML) stays in production untouched (user decision; unrelated to alcohol but retained).
- R6. Carry the **alcohol-core improvements** that currently live only on `feat/stress-recognition` onto `main` via cherry-pick of the relevant changes — notably the updated Wiley journal article and the alcohol-relevant edits to `ml_model/training/bac_estimation_model.py`, `ml_model/training/train_model.py`, `ml_model/data/dataset_loader.py`, and the alcohol portions of `wear_os_app/.../SensorManager.kt`. Stress-only hunks (e.g. accelerometer-for-stress, DFPlayer) are excluded. `main`'s history must stay free of stress/NTCC code.

**Canonical patent paper**
- R7. Establish version **A** (`from_overleaf/AlcoWatch_New.zip`, ~8 283 words, headline metrics 0.0142 g/dL · 99.3% · 107 KB · 30×, the expanded version with Ablation / Confusion Matrix / Attention / Discussion / Limitations) as the single canonical patent paper, stored as a clean compilable source in the repo (proposed `overleaf_papers/` to match the guide, or a clearly named folder).
- R8. The canonical source must have **all latexdiff markup stripped** (`%DIF` lines, `\DIFadd{}`, `\DIFdel{}`, DIF preamble) into a clean `.tex` that compiles against `WileyNJDv5.cls`, with no reconstruction artifacts (e.g. no `\subsection{{`).
- R9. Remove the superseded patent exports from production: the on-`main` `Wiley_New_Journal_Design_version_5__NJD_v5___5_/` (version C/B), `ntcc_paper_overleaf.zip`, `major_project_overleaf.zip`, and the loose `from_overleaf/` zips once their content is extracted/placed. Tell the user which two Overleaf projects to delete (`AlcoWatch_New_06_04`, `Wiley_New_Journal_Design_version_5`) and which to keep (`AlcoWatch_New`).

**Working tree, ignore rules, branches**
- R10. Clean the working tree: remove untracked junk (`venv/`, `__pycache__/`, `*_saved_model/`, `.DS_Store`) and resolve the pending `ntcc/` deletions and stress-figure modifications coherently with the archive move.
- R11. Update `.gitignore` to also cover `*.pptx` and `*.zip` (and keep `*_saved_model/`, `venv/`), so large binaries don't re-enter the tree; keep intentionally-tracked figures working (they are currently force-added against the `*.png`/`*.pdf` ignore).
- R12. After R1–R11 land on `main`, delete the `feat/stress-recognition` branch locally and on `origin`.

**Guides / index**
- R13. Rewrite `README.md`, `CLAUDE.md`, and `AGENTS.md` to describe the alcohol patent project only: fix the dead `overleaf_papers/` reference, point at the canonical paper (R7), remove NTCC/stress from the live narrative (with a one-line pointer to `archive/`), and correct the research-papers table.
- R14. Reorganize `docs/`: keep alcohol-relevant guides (`IMPLEMENTATION_GUIDE.md`, `QUICK_START.md`, `SYSTEM_SUMMARY.md`), move NTCC/stress brainstorms, plans, and `docs/superpowers/` specs into the archive, and leave a clean `docs/` index.

---

## Success Criteria

- A fresh clone of `main` reads, top to bottom, as a single alcohol-detection patent project; nothing NTCC or stress appears in the live code/guides except an explicit `archive/` pointer.
- No NTCC or Stress work is lost — every artifact is either in `archive/` or recoverable from history; `feat/stress-recognition`'s alcohol-core improvements are present on `main`.
- The repo holds exactly **one** canonical patent paper source, clean (no latexdiff markup), compiling against `WileyNJDv5.cls`; the user knows which single Overleaf project to keep.
- `git status` is clean; `.gitignore` prevents the previous junk from returning; only `main` (and any new work branch) remains — `feat/stress-recognition` is gone.
- The user can immediately start the next task on a clean base.

---

## Scope Boundaries

- No functional changes to the alcohol detection ML model, Wear OS app, or Arduino firmware — this is reorganization, not development.
- No editing of the patent paper's content/wording — only de-duplication and latexdiff-cleanup to establish the canonical source.
- `paper_reproduction/` (LiPb ML) is left as-is, not archived, not refactored.
- The new task the user will give after cleanup is out of scope here.
- Deleting the two superseded Overleaf projects is the user's manual action (we only secure the source and advise); we do not touch Overleaf directly.

---

## Key Decisions

- **Archive as an in-repo `archive/` folder, not git tags**: user wants the NTCC/Stress work visible and browsable in the tree, clearly separated from live code, rather than hidden behind refs.
- **"Carry only the core" for production, not "merge then strip"**: `main` is already free of stress/NTCC; cherry-picking the alcohol-core improvements keeps `main`'s history clean instead of importing stress/NTCC commits and deleting them.
- **Canonical patent = version A (`AlcoWatch_New`)**: content analysis showed A is a strict superset of versions B and C (all of B's sections plus Ablation/Confusion Matrix/Attention/Discussion/Limitations; same corrected headline metrics), confirmed by the user as the latest after word-count expansion.

---

## Dependencies / Assumptions

- The three Overleaf exports under `from_overleaf/` are the latest sources; version A's content (currently a latexdiff file) is the authoritative newest and is fully recoverable by stripping markup.
- Heavy binaries from NTCC/stress (`.pptx`, `.zip`, large `.pdf`) move into `archive/` rather than staying at top level; whether to additionally route them through Git LFS or drop them from tracking is a planning-level call (see Outstanding Questions).
- Operations touch git branches and `origin`; pushing branch deletions and the cleaned `main` is assumed authorized as part of "merge everything to production."

---

## Outstanding Questions

### Deferred to Planning

- [Affects R6][Technical] Exact commit/hunk selection for the alcohol-core cherry-pick vs. stress-only changes on `feat/stress-recognition` (per-file, possibly per-hunk for `SensorManager.kt`).
- [Affects R8][Technical] Cleanest way to strip latexdiff markup to a faithful clean master (reverse via latexdiff tooling vs. careful scripted unwrap) without losing the expanded content.
- [Affects R7][Technical] Final folder name/location for the canonical paper (`overleaf_papers/` to match the guide vs. existing `research_papers/`).
- [Affects R2, R11][Needs research] Whether archived heavy binaries should be tracked in-repo, dropped, or moved to Git LFS to keep clone size sane.
