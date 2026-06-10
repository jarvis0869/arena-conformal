# Conformal Arena

**Distribution-free uncertainty quantification for LLM leaderboard rankings.**

Applied split conformal prediction to 135,634 real human preference votes from LMArena across 48 models.

## Key Findings

- **100% of adjacent model pairs are statistically indistinguishable** at 90% coverage
- **Code rankings are 55% more uncertain** than non-code (q̂: 9.88 vs 6.38)
- **Rankings shift over time** — prediction set width grows 47% from early to late periods
- **Arena's bootstrap CIs are overconfident** for 80% of models vs our distribution-free sets
- The #1 model (Gemini 2.5 Pro) has a prediction set of [1, 8] — it could be anywhere in the top 8

## Method

Split conformal prediction on bootstrapped Elo rankings. No distributional assumptions, no model assumptions. Finite-sample coverage guarantee: P(true rank ∈ set) ≥ 1-α.

Based on Angelopoulos & Bates (2021), "A Gentle Introduction to Conformal Prediction."

## Files

- `conformal_arena.py` — Core pipeline (Elo + bootstrap + conformal prediction)
- `run_new.py` — Run on the 140K LMArena dataset
- `advanced_analysis.py` — Category slicing, vote efficiency, temporal, CI comparison
- `conformal_data.json` — Exported results for all 48 models
- `*.png` — Publication-quality figures

## Data

LMArena Human Preference 140K dataset: [huggingface.co/datasets/lmarena-ai/arena-human-preference-140k](https://huggingface.co/datasets/lmarena-ai/arena-human-preference-140k)

## Author

Pingash Vohra — University of Waterloo

## Paper

Draft in progress. Targeting COPA 2026 / NeurIPS workshop.
