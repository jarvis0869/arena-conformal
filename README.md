# Conformal Arena

**Distribution-free uncertainty quantification for LLM leaderboard rankings.**

> *When the Arena says GPT-4o is ranked #2 and Claude is ranked #3, is that difference real — or just noise?*

[![Live Demo](https://img.shields.io/badge/Live%20Demo-arena--conformal.vercel.app-blue)](https://arena-conformal.vercel.app)
[![GitHub](https://img.shields.io/badge/GitHub-jarvis0869%2Farena--conformal-black)](https://github.com/jarvis0869/arena-conformal)

## Live Demo

**[arena-conformal.vercel.app](https://arena-conformal.vercel.app)**

Interactive leaderboard with conformal prediction sets, model comparison, bootstrap CI comparison, and methodology explanation.

---

## What Is This?

[Chatbot Arena (LMArena)](https://lmarena.ai) is the most influential LLM evaluation platform. Its Elo-based rankings drive deployment decisions, investment theses, and research priorities across the AI industry.

But those rankings are **point estimates** — a single number with no uncertainty attached. When Arena says Model A is #3 and Model B is #5, it doesn't tell you if that gap is real or noise.

We applied **split conformal prediction** to 135,634 real human preference votes to construct prediction sets over model rankings with formal coverage guarantees:

> P(true rank ∈ prediction set) ≥ 1 − α

No distributional assumptions. No model assumptions. Finite-sample exact. Built on [Angelopoulos & Bates (2021)](https://arxiv.org/abs/2107.07511).

---

## Key Findings

| Finding | Result |
|---------|--------|
| Adjacent pairs indistinguishable | **100%** at 90% coverage |
| Top model (Gemini 2.5 Pro) prediction set | **[1, 8]** — could be anywhere in top 8 |
| Code rankings more uncertain than non-code | **55%** wider (q̂: 9.88 vs 6.38) |
| Ranking drift early → late period | **+47%** set width |
| Arena bootstrap CIs overconfident | **80%** of models |

**In plain English:** The AI community treats Arena rankings as ground truth. They're not. Most ranking differences are within the noise floor, and Arena's existing confidence intervals systematically underestimate this uncertainty.

---

## Method

**1. Split** — 98,348 real Arena battles (ties removed) into training (60%) and calibration (40%).

**2. Bootstrap** — Resample training data 100× with replacement, compute Elo rankings each time. Predicted rank = median across bootstraps.

**3. Calibrate** — Compute nonconformity scores on held-out data: score = |true rank − predicted rank|.

**4. Threshold** — q̂ = ⌈(1−α)(1+1/n)⌉-th quantile of scores. The (1+1/n) correction makes the guarantee finite-sample exact.

**5. Predict** — Prediction set = [predicted rank − q̂, predicted rank + q̂] clipped to [1, 48].

The coverage guarantee holds regardless of how good or bad the Elo model is. The only assumption is exchangeability of the calibration data, which holds by random splitting.

---

## Results

### Main Finding: Leaderboard Rankings Are Noise

At 90% coverage, **47/47 adjacent model pairs are statistically indistinguishable**. The top model's prediction set spans 8 positions. The middle of the leaderboard (ranks 10–35) is one undifferentiated blob.

### Category Slicing

Splitting battles by `is_code` reveals code rankings are 55% more uncertain than non-code rankings. A single combined leaderboard blends different signal-to-noise ratios.

### Temporal Analysis

Prediction set width grows 47% from early to late periods. Individual models drift dramatically:

| Model | Early | Late | Shift |
|-------|-------|------|-------|
| llama-4-maverick-17b | #26 | #42 | ↓16 |
| claude-3.7-sonnet | #31 | #44 | ↓13 |
| claude-3.5-haiku | #33 | #45 | ↓12 |

### Arena Is Overconfident

For **80% of models**, our distribution-free CP sets are wider than Arena's bootstrap 95% CIs. Example: Gemini 2.5 Pro bootstrap CI is [1–2] but our CP set is [1–9].

---

## Files

```
conformal_arena.py          Core pipeline (Elo + bootstrap + CP)
run_new.py                  Run on LMArena 140K dataset
advanced_analysis.py        Category, vote efficiency, temporal, CI analyses
conformal_data.json         Exported results for all 48 models
models_data.js              JavaScript-ready data for the UI
src/App.jsx                 React interactive dashboard
*.png                       Publication-quality figures
```

---

## Figures

| Figure | Description |
|--------|-------------|
| `new_arena_rankings.png` | Main: point estimates vs conformal prediction sets |
| `new_coverage_calibration.png` | Coverage guarantee holds at all levels |
| `category_comparison.png` | Code vs non-code ranking uncertainty |
| `vote_efficiency.png` | Prediction set width vs vote count |
| `temporal_analysis.png` | Ranking stability over time |
| `ci_comparison.png` | Arena bootstrap CIs vs conformal sets |

---

## Data

[LMArena Human Preference 140K](https://huggingface.co/datasets/lmarena-ai/arena-human-preference-140k) — 135,634 pairwise battles, 48 models, real human votes.

---

## References

- Angelopoulos, A.N. and Bates, S. (2021). [A Gentle Introduction to Conformal Prediction.](https://arxiv.org/abs/2107.07511)
- Chiang, W.-L. et al. (2024). [Chatbot Arena: An Open Platform for Evaluating LLMs by Human Preference.](https://arxiv.org/abs/2403.04132)
- Gibbs, I. and Candès, E. (2021). [Adaptive Conformal Inference Under Distribution Shift.](https://arxiv.org/abs/2106.00170)

---

## Author

**Pingash Vohra** — University of Waterloo (CS, Class of 2030)

CEO & Co-founder, Aeyron Health

---

## Paper

Draft in progress. Targeting COPA 2026 / NeurIPS workshop on Reliable ML.

*If you're working on conformal prediction, LLM evaluation, or leaderboard methodology — reach out.*
