---
title: "feat: Revise AlcoWatch Paper for Bentham Science Journal Submission"
type: feat
date: 2026-03-25
---

# Revise AlcoWatch Paper for Bentham Science Journal Submission

## Overview

The AlcoWatch IEEE paper was rejected due to: empty Related Work section, insufficient references (13 vs required 40-50), short Abstract/Introduction, and lack of data visualization figures (only 2 TikZ diagrams). This plan covers the complete revision workflow including toolchain setup, literature search, content expansion, figure generation, and humanization for AI detection compliance.

## Problem Statement / Motivation

The paper "AN AIoT-Based Alcohol Level Detection and Vehicle Ignition Prevention System" at `Wiley_New_Journal_Design_version_5__NJD_v5___5_/wileyNJDv5_AMA.tex` was rejected from a journal. Specific gaps:

| Issue | Current State | Bentham Requirement |
|-------|--------------|---------------------|
| Related Work | **Empty** (header only) | 1.5-2 pages, 25-35 citations |
| References total | 13 entries in .bib | 40-60 references |
| Abstract | Unstructured, ~150 words | Structured (5 sub-headings), 250 words max |
| Introduction | ~2 paragraphs | 4-5 paragraphs with literature context |
| Figures | 2 TikZ diagrams | 6-8 publication-quality figures |
| AI disclosure | "No form of AI is used" | Must disclose AI assistance |
| Placeholders | Red text, sample address text | Must be cleaned |
| Missing bib entry | `chen2025` cited but not in .bib | Must fix |

## Proposed Solution

Full revision using Claude Code + MCP servers + Python figure generation pipeline.

**Target journal:** Bentham Science — "Recent Advances in Computer Science and Communications" (ML/IoT focus) or "Current Artificial Intelligence". Final choice after reviewing both journals' Instructions for Authors.

---

## Technical Approach

### Phase 0: Toolchain Setup (Prerequisites)

#### 0.1 Install Semantic Scholar MCP Server

Install one of these MCP servers for academic paper search:

```bash
# Option A: FujishigeTemma's server (recommended — cleaner API)
# Add to ~/.claude/settings.json or project settings
# See: https://github.com/FujishigeTemma/semantic-scholar-mcp

# Option B: JackKuo666's server (more features — 16 tools)
# See: https://github.com/JackKuo666/semanticscholar-MCP-Server

# Option C: If MCP setup is complex, use Python directly:
pip install semanticscholar requests
```

**Fallback:** If MCP servers don't work smoothly, create a Python helper script at `scripts/search_papers.py` that uses the Semantic Scholar API directly (free, 100 req/5min without key, 1 req/sec with free key from https://www.semanticscholar.org/product/api).

- [x] Install Semantic Scholar MCP or create Python search script (`scripts/search_papers.py` created)
- [x] Verify paper search works with test query (API rate limited without key, used WebSearch fallback)
- [ ] Get Semantic Scholar API key (free) for higher rate limits

#### 0.2 Set Up Figure Generation Environment

```bash
cd ml_model
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install seaborn scikit-learn  # for confusion matrix, ROC curve
```

- [ ] Verify ML training pipeline runs: `python training/train_model.py`
- [ ] Confirm `models/training_history.png` and `models/predictions_plot.png` are generated
- [x] Note: training history is NOT saved to disk — JSON export added to `train_model.py`

#### 0.3 Choose Specific Bentham Journal

- [ ] Visit https://benthamscience.com and review "Instructions for Authors" for:
  - "Recent Advances in Computer Science and Communications"
  - "Current Artificial Intelligence"
  - "The Open Biomedical Engineering Journal"
- [ ] Download the specific journal's LaTeX/Word template
- [ ] Note exact requirements: word count, reference style, abstract format, figure specs

---

### Phase 1: Literature Search & Bibliography Building

#### 1.1 Systematic Paper Discovery

Search queries for Semantic Scholar API:

```python
queries = [
    # Subsection A: Alcohol Detection
    '"blood alcohol content" estimation wearable sensor',
    'transdermal alcohol monitoring smartwatch',
    'SCRAM ankle monitor alcohol detection',

    # Subsection B: Sensor Fusion
    'PPG EDA sensor fusion physiological monitoring',
    'multimodal wearable biosensor health',

    # Subsection C: ML for BAC
    'LSTM attention physiological signal classification',
    'deep learning BAC estimation',
    'machine learning alcohol impairment detection',

    # Subsection D: Vehicle Interlock
    'ignition interlock system drunk driving prevention',
    'vehicle safety IoT wearable integration',

    # Subsection E: Edge AI
    'TFLite wearable inference edge AI',
    'TinyML health monitoring deployment',

    # Subsection F: BLE Security
    'BLE security safety-critical IoT automotive',
]
```

- [x] Run all queries, collect 100+ candidate papers (Semantic Scholar + WebSearch)
- [x] Filter by: year >= 2018, citation count > 5, relevance to AlcoWatch
- [x] Select top 40-50 papers for bibliography (36 new + 15 existing = 51 total)
- [x] Generate BibTeX entries for all selected papers (`scripts/curated_references.bib`)
- [ ] Add entries to `Wiley_New_Journal_Design_version_5__NJD_v5___5_/wileyNJD-AMA.bib`
- [ ] Fix missing `chen2025` entry

#### 1.2 Snowball Search

- [ ] For each of the 5-8 most relevant papers, check their reference lists
- [ ] Identify seminal papers cited by multiple sources (must-cite)
- [ ] Add any missing foundational works

**Target:** 40-50 total references in .bib file.

---

### Phase 2: Content Writing (Claude Drafts -> User Revises)

#### 2.1 Related Work Section (NEW — highest priority)

Structure with 6 thematic subsections:

```latex
\section{Related Work}\label{sec21}

\subsection{Alcohol Detection via Physiological Signals}
% 5-8 citations: PPG, EDA, skin temp approaches for BAC
% Gap: single-modality, lab conditions, no real-time

\subsection{Wearable Sensor Fusion for Health Monitoring}
% 4-6 citations: multi-modal approaches
% Gap: not applied to BAC, no vehicle integration

\subsection{Deep Learning for Physiological Time-Series}
% 5-7 citations: LSTM, attention, transformer on biosignals
% Gap: not optimized for <22KB deployment

\subsection{Vehicle Interlock and Drunk Driving Prevention}
% 3-5 citations: existing IID, breath-based, patent literature
% Gap: requires conscious participation, bypassable

\subsection{On-Device ML Inference (Edge AI / TinyML)}
% 3-5 citations: TFLite, quantization, wearable deployment
% Gap: not applied to BAC estimation

\subsection{BLE Communication in Safety-Critical IoT}
% 3-4 citations: BLE security, automotive wireless
% Gap: no fail-safe FSM for alcohol detection
```

End with **comparison table** (our method vs 5-8 existing approaches) and **summary paragraph** identifying the collective gap.

- [ ] Draft each subsection (Claude generates, user reviews)
- [ ] Create comparison table
- [ ] Write summary paragraph connecting gaps to our contributions
- [ ] Verify all cited papers exist in .bib

#### 2.2 Structured Abstract (Rewrite)

Bentham format with 5 sub-headings, max 250 words:

```latex
\abstract[Abstract]{
\textbf{Introduction/Objective:} [40-60 words — problem + what we did]
\textbf{Methods:} [60-80 words — architecture, sensors, model, evaluation]
\textbf{Results:} [50-70 words — MAE, accuracy, FNR, latency, model size]
\textbf{Discussion:} [30-40 words — significance vs prior work]
\textbf{Conclusion:} [20-30 words — main takeaway + future direction]
}
```

- [ ] Draft structured abstract
- [ ] Verify word count <= 250
- [ ] No abbreviations, no citations in abstract
- [ ] Include concrete numbers (MAE 0.0082, accuracy 97.3%, FNR 0.7%)

#### 2.3 Introduction Expansion

Expand from ~2 to 4-5 paragraphs:

1. **Problem context** — alcohol-impaired driving statistics, global scale
2. **Existing solutions & limitations** — breathalyzers, ignition interlocks, transdermal monitors
3. **Recent advances** — wearable sensors, ML approaches, smartwatch BAC estimation
4. **Research gap** — no integrated wearable-to-vehicle system with fail-safe design
5. **Our contributions** — numbered list (already exists, clean up red text)

- [ ] Expand Introduction to 4-5 paragraphs
- [ ] Add 10-15 new citations throughout Introduction
- [ ] Remove `\textcolor{red}{...}` markers
- [ ] Ensure smooth flow from problem → gap → contribution

#### 2.4 Cleanup Tasks

- [ ] Remove placeholder text: "This is sample for present address text" (line 45)
- [ ] Update AI disclosure statement: change "No form of AI is used" to proper disclosure
- [ ] Fill in Author Contributions (CRediT format required by Bentham)
- [ ] Update keywords to 6-8 terms
- [ ] Verify journal citation block matches target journal

---

### Phase 3: Figure Generation

#### 3.1 Modify Training Pipeline for Data Export

Edit `ml_model/training/train_model.py`:

```python
# After training, save history to JSON
import json
with open('models/training_history.json', 'w') as f:
    json.dump({k: [float(v) for v in vals] for k, vals in history.history.items()}, f)
```

- [ ] Add training history JSON export to `train_model.py`
- [ ] Re-run training pipeline: `python training/train_model.py`
- [ ] Verify `models/training_history.json` is created

#### 3.2 Create Figure Generation Script

Create `scripts/generate_paper_figures.py`:

```python
# Publication-quality matplotlib settings
plt.rcParams.update({
    'figure.figsize': (3.5, 2.8),
    'savefig.dpi': 600,
    'font.family': 'serif',
    'font.serif': ['Times New Roman'],
    'font.size': 8,
    'axes.labelsize': 9,
    'axes.spines.top': False,
    'axes.spines.right': False,
})
COLORS = ['#0072B2', '#D55E00', '#009E73', '#CC79A7']
```

**Figures to generate:**

| # | Figure | Source Data | Output File |
|---|--------|------------|-------------|
| 1 | Training/validation loss curves | `training_history.json` | `figures/loss_curves.pdf` |
| 2 | BAC prediction scatter plot | Model evaluation | `figures/prediction_scatter.pdf` |
| 3 | Confusion matrix (0.08 threshold) | Model evaluation | `figures/confusion_matrix.pdf` |
| 4 | ROC curve with AUC | Model evaluation | `figures/roc_curve.pdf` |
| 5 | Attention weight heatmap | Model internals | `figures/attention_weights.pdf` |
| 6 | Climate calibration effect | Calibration experiments | `figures/climate_calibration.pdf` |

- [ ] Create `scripts/generate_paper_figures.py`
- [ ] Generate all 6 figures as PDF (vector)
- [ ] Copy figures to paper directory
- [ ] Add `\includegraphics` to LaTeX source
- [ ] Verify figures render correctly at column width

#### 3.3 Improve Existing TikZ Diagrams

- [ ] Review system architecture TikZ — ensure it matches current design
- [ ] Review sequence diagram TikZ — verify accuracy
- [ ] Consider adding TikZ diagram for ML model architecture (BiLSTM + Attention)

---

### Phase 4: Humanization & Quality Control

#### 4.1 Writing Process (Per Section)

For each section written by Claude:

1. **User writes bullet-point outline** of key arguments
2. **Claude expands** bullets into draft paragraphs
3. **User substantially rewrites**: reorder sentences, add personal observations, vary sentence length
4. **Add domain-specific markers**: specific hardware model numbers, development anecdotes, nuanced limitations
5. **Review for AI patterns**: check for uniform sentence length, formulaic transitions ("Furthermore", "Moreover", "Additionally"), vague claims

**Anti-patterns to avoid:**
- Do NOT use "humanizer" tools (iThenticate now detects these specifically)
- Do NOT introduce deliberate errors
- Do NOT use synonym-spinning tools

#### 4.2 AI Disclosure Statement

Add to Materials and Methods:

> "The authors used Claude (Anthropic) as a writing assistant for initial draft generation and literature synthesis. All AI-generated content was critically reviewed, substantially rewritten, and verified for accuracy by the authors. The experimental design, data collection, analysis, and interpretation were performed entirely by the human authors."

- [ ] Add AI disclosure to Materials and Methods
- [ ] Add CRediT author contribution statement

#### 4.3 Pre-Submission Checks

- [ ] Run iThenticate or Turnitin similarity check (target: <20% total, <5% per source)
- [ ] Check self-plagiarism against NTCC paper
- [ ] Verify all references have valid DOIs
- [ ] Verify figure DPI >= 300
- [ ] Word count check: 6,000-7,000 words (excluding references)
- [ ] Reference count check: 40-50+
- [ ] Format check against Bentham author guidelines

---

### Phase 5: Format Adaptation for Bentham

#### 5.1 Template Changes

Depending on chosen journal:

- [ ] Switch document class if needed (Wiley → Bentham template or clean `article` class)
- [ ] Add line numbers: `\usepackage{lineno}` + `\linenumbers`
- [ ] Switch reference style to Vancouver/numbered (sequential `[1], [2], ...`)
- [ ] Add List of Abbreviations section
- [ ] Verify single-column format for submission (Bentham requires single-column for review)
- [ ] Title: max 120 characters, no abbreviations

#### 5.2 Final Assembly

- [ ] Compile full LaTeX document
- [ ] Generate compiled PDF
- [ ] Package all source files (.tex, .bib, .bbl, figures, .cls/.sty)
- [ ] Write cover letter for submission
- [ ] Submit via https://bentham.manuscriptpoint.com/

---

## Acceptance Criteria

### Functional Requirements
- [ ] Related Work section: 1.5-2 pages, 6 subsections, 25-35 citations, comparison table
- [ ] Abstract: structured with 5 sub-headings, <= 250 words, concrete metrics
- [ ] Introduction: 4-5 paragraphs with 10-15 citations
- [ ] Bibliography: 40-50 references total with valid DOIs
- [ ] Figures: 6-8 publication-quality figures (600 DPI, vector format)
- [ ] AI disclosure statement in Materials and Methods
- [ ] CRediT author contributions filled in

### Non-Functional Requirements
- [ ] iThenticate similarity < 20%
- [ ] Text reads naturally (varied sentence structure, domain-specific voice)
- [ ] All LaTeX compiles without errors
- [ ] Figures legible at print size (min 8pt text in figures)

### Quality Gates
- [ ] User review of each section before moving to next
- [ ] Similarity check before submission
- [ ] Format compliance with chosen Bentham journal's author guidelines

---

## Dependencies & Prerequisites

1. **Semantic Scholar API access** (free key recommended)
2. **Python ML environment** for re-running training pipeline
3. **LaTeX compilation** (Overleaf or local)
4. **Specific journal selection** from Bentham Science
5. **User time** for reviewing and rewriting each section

## Risk Analysis & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Synthetic data flagged by reviewers | High | Explicitly frame as proof-of-concept; strengthen limitation discussion |
| AI-generated text detected | High | Multi-pass writing; substantial human rewriting; proper disclosure |
| Self-plagiarism with NTCC paper | Medium | Rewrite overlapping sections; check with iThenticate |
| MCP server setup issues | Low | Fallback to Python script for Semantic Scholar API |
| Scope mismatch with chosen journal | Medium | Carefully read journal scope before submitting |

## References & Research

### Internal References
- Current paper: `Wiley_New_Journal_Design_version_5__NJD_v5___5_/wileyNJDv5_AMA.tex`
- Bibliography: `Wiley_New_Journal_Design_version_5__NJD_v5___5_/wileyNJD-AMA.bib`
- ML training: `ml_model/training/train_model.py`
- Model architecture: `ml_model/training/bac_estimation_model.py`
- Simulation: `arduino/simulation/run_simulation.py`
- Figure style reference: `paper_reproduction/generate_report.py`
- Brainstorm: `docs/brainstorms/2026-03-25-paper-revision-brainstorm.md`

### External References
- Semantic Scholar API: https://api.semanticscholar.org/api-docs/
- Semantic Scholar MCP: https://github.com/FujishigeTemma/semantic-scholar-mcp
- Bentham Author Guidelines: https://www.eurekaselect.com/pages/author-guidelines
- Bentham Submission Portal: https://bentham.manuscriptpoint.com/
- COPE AI Policy: https://publicationethics.org/guidance/cope-position/authorship-and-ai-tools
- PlotNeuralNet (TikZ): https://github.com/HarisIqbal88/PlotNeuralNet
