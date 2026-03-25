# Brainstorm: Revision of AlcoWatch Paper for Bentham Science Journal

**Date:** 2026-03-25
**Status:** Design captured
**Participants:** User + Claude Code

---

## What We're Building

A comprehensive workflow and toolchain for revising the rejected AlcoWatch IEEE paper to meet Bentham Science journal standards. The paper was rejected due to: insufficient Related Work section, short Abstract/Introduction, insufficient references (15 vs required 40-60), and lack of detailed figures/diagrams.

### Target State
- **Abstract:** Structured (Background/Objective/Methods/Results/Conclusion), 200-250 words
- **Introduction:** 4-5 paragraphs with comprehensive literature context
- **Related Work:** New dedicated section (1.5-2 pages), organized thematically
- **References:** 40-50 citations (currently 15)
- **Figures:** 6-8 publication-quality figures (currently 2)
- **Total length:** 6,000-7,000 words
- **AI detection:** Text must pass iThenticate (<20% similarity) and AI detection tools

---

## Why This Approach

**Approach chosen:** Full toolchain via MCP servers + Claude Code Skills

**Rationale:**
1. Semantic Scholar API provides free, structured access to millions of papers with BibTeX export
2. Claude Code can write LaTeX directly and generate TikZ/matplotlib figures
3. Iterative workflow (Claude writes → user reviews) matches the user's preferred process
4. Reproducible — same toolchain can be used for future papers

---

## Key Decisions

### 1. Target Journal
- **Not yet decided** — recommend "Recent Advances in Computer Science and Communications" (ML/IoT focus) or "The Open Biomedical Engineering Journal" (biomedical device focus)
- Need to check specific journal's "Instructions for Authors" before formatting

### 2. Toolchain Components

| Tool | Purpose | Setup Required |
|------|---------|---------------|
| **Semantic Scholar MCP** | Find papers, get citations, build Related Work | Install MCP server |
| **Claude Code (direct)** | Write LaTeX sections, generate figures | Already available |
| **WebSearch/WebFetch** | Verify DOIs, find specific papers | Already available |
| **Python/matplotlib** | Generate data visualization figures | Already available |
| **TikZ (LaTeX)** | Architecture/flow diagrams | Already in paper |
| **Context7 MCP** | Library documentation lookup | Already connected |

### 3. Humanization Strategy
- Write each section in multiple passes with varied sentence structure
- Mix short and long sentences naturally
- Add domain-specific jargon and nuanced phrasing
- Reference specific implementation details (shows human expertise)
- Run through AI detection tools between drafts
- Disclose AI assistance in Acknowledgments (Bentham requires this)

### 4. Paper Structure (Revised)

```
1. Abstract (structured, 250 words)
2. Introduction (expanded, 4-5 paragraphs)
3. Related Work (NEW — 4 subsections)
   3.1 Alcohol Detection Methods
   3.2 Wearable Sensor Fusion for Physiological Monitoring
   3.3 Machine Learning for BAC Estimation
   3.4 Vehicle Interlock Systems
4. Methodology (existing, minor updates)
5. Experimental Results and Discussion (existing + new figures)
6. Conclusions (existing, minor updates)
7. List of Abbreviations (NEW)
8. References (expanded to 40-50)
```

### 5. New Figures Needed

1. System architecture (existing, improve quality)
2. Sequence diagram (existing, improve quality)
3. **NEW:** ML model architecture diagram (BiLSTM + Attention visual)
4. **NEW:** Training/validation loss curves
5. **NEW:** BAC prediction scatter plot (predicted vs actual)
6. **NEW:** Confusion matrix or ROC curve
7. **NEW:** Comparison table visualization (our method vs baselines)
8. **NEW:** Climate calibration effect visualization

---

## Open Questions

1. **Which specific Bentham Science journal?** — Need to read "Instructions for Authors" for exact formatting
2. **LaTeX template:** Bentham prefers Word but accepts LaTeX — do we switch or stay with LaTeX?
3. **Semantic Scholar MCP:** Need to find/install a working MCP server, or use API directly via Python
4. **Real data:** Reviewers will flag synthetic data — how to strengthen this limitation section?
5. **Self-plagiarism:** How much overlap with NTCC paper is acceptable?

---

## Next Steps

1. Install/configure Semantic Scholar MCP server (or set up API access)
2. Choose specific Bentham Science journal and download author guidelines
3. Run `/workflows:plan` to create detailed implementation plan for paper revision
4. Begin with Related Work section (biggest gap)
