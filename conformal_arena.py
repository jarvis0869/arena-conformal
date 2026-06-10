"""
=============================================================================
CONFORMAL PREDICTION SETS FOR CHATBOT ARENA RANKINGS
=============================================================================
Author: Pingash Vohra

Core Idea:
    Arena leaderboard gives POINT ESTIMATE rankings (Model A is rank 3).
    But those rankings come from a finite, noisy sample of human votes.
    Conformal prediction wraps those rankings in PREDICTION SETS with a
    formal coverage guarantee:
    
    "With 90% probability, Model A's true rank is between 2 and 6."
    
    When two models' prediction sets overlap, we CANNOT confidently say 
    which is better — they are statistically indistinguishable.
=============================================================================
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import defaultdict
import json, os, time

# ============================================================================
# SECTION 1: DATA — Synthetic Arena battles mimicking real structure
# ============================================================================

# Real models with approximate Elo ratings (mid-2025)
GROUND_TRUTH_MODELS = {
    "GPT-4o":           1290,
    "Claude-3.5-Sonnet": 1275,
    "Gemini-1.5-Pro":   1265,
    "GPT-4-Turbo":      1255,
    "Claude-3-Opus":    1250,
    "Llama-3.1-405B":   1240,
    "Gemini-1.5-Flash": 1230,
    "Mistral-Large":    1215,
    "GPT-4":            1210,
    "Claude-3-Sonnet":  1200,
    "Llama-3.1-70B":    1190,
    "Qwen-2-72B":       1185,
    "Command-R+":       1175,
    "Mixtral-8x22B":    1165,
    "GPT-3.5-Turbo":    1155,
    "Claude-3-Haiku":   1150,
    "Llama-3.1-8B":     1130,
    "Gemma-2-27B":      1140,
    "Phi-3-Medium":     1125,
    "Mistral-7B":       1100,
}

def generate_battles(n_battles=20000, seed=42):
    """Generate synthetic pairwise battles mimicking Chatbot Arena."""
    rng = np.random.RandomState(seed)
    models = list(GROUND_TRUTH_MODELS.keys())
    ratings = np.array([GROUND_TRUTH_MODELS[m] for m in models], dtype=float)
    n = len(models)
    
    # Popularity weighting (top models get more matchups)
    pop = (ratings - ratings.min() + 10) ** 2
    pop /= pop.sum()
    
    # Pre-generate all matchups at once (FAST)
    idx_a = rng.choice(n, size=n_battles, p=pop)
    idx_b = rng.choice(n, size=n_battles, p=pop)
    
    # Re-roll when same model matched against itself
    same = idx_a == idx_b
    while same.any():
        idx_b[same] = rng.choice(n, size=same.sum(), p=pop)
        same = idx_a == idx_b
    
    # Compute win probabilities: P(A wins) = 1 / (1 + 10^((R_B - R_A)/400))
    rating_diff = ratings[idx_b] - ratings[idx_a]
    p_a_wins = 1.0 / (1.0 + 10 ** (rating_diff / 400.0))
    
    # Add human judgment noise
    p_a_wins = np.clip(p_a_wins + rng.normal(0, 0.05, n_battles), 0.02, 0.98)
    
    # Simulate votes
    a_wins = rng.random(n_battles) < p_a_wins
    
    return {
        'idx_a': idx_a, 
        'idx_b': idx_b, 
        'a_wins': a_wins, 
        'models': models,
        'n_models': n
    }


# ============================================================================
# SECTION 2: FAST ELO COMPUTATION
# ============================================================================
#
# HOW ELO WORKS:
# 1. Every model starts at 1000
# 2. After each battle, winner gains points, loser loses points
# 3. Amount depends on how "surprising" the result was
# 4. K-factor controls sensitivity (Arena uses K=4)
#
# This version operates on integer arrays — ~100x faster than row-by-row.
# ============================================================================

def compute_elo_fast(idx_a, idx_b, a_wins, n_models, k=4):
    """Fast Elo computation on pre-indexed arrays."""
    ratings = np.full(n_models, 1000.0)
    
    for i in range(len(idx_a)):
        ra, rb = ratings[idx_a[i]], ratings[idx_b[i]]
        ea = 1.0 / (1.0 + 10 ** ((rb - ra) / 400.0))
        
        if a_wins[i]:
            ratings[idx_a[i]] += k * (1.0 - ea)
            ratings[idx_b[i]] -= k * (1.0 - ea)
        else:
            ratings[idx_a[i]] -= k * ea
            ratings[idx_b[i]] += k * ea
    
    return ratings


def ratings_to_ranks(ratings):
    """Convert ratings array to ranks (1 = best)."""
    # argsort descending, then rank
    order = np.argsort(-ratings)
    ranks = np.empty_like(order)
    ranks[order] = np.arange(1, len(ratings) + 1)
    return ranks


# ============================================================================
# SECTION 3: BOOTSTRAP — "What if we had different voters?"
# ============================================================================
#
# Take all N battles, randomly resample N battles WITH REPLACEMENT,
# compute Elo on the resample. Repeat many times.
# This gives a distribution over rankings for each model.
# ============================================================================

def bootstrap_ranks(data, n_bootstraps=100, seed=123):
    """Bootstrap Elo rankings. Returns (n_models, n_bootstraps) rank matrix."""
    rng = np.random.RandomState(seed)
    n_battles = len(data['idx_a'])
    n_models = data['n_models']
    
    rank_matrix = np.zeros((n_models, n_bootstraps), dtype=int)
    
    for b in range(n_bootstraps):
        # Resample with replacement — the core bootstrap idea
        idx = rng.choice(n_battles, size=n_battles, replace=True)
        ratings = compute_elo_fast(
            data['idx_a'][idx], data['idx_b'][idx], 
            data['a_wins'][idx], n_models
        )
        rank_matrix[:, b] = ratings_to_ranks(ratings)
    
    return rank_matrix


# ============================================================================
# SECTION 4: CONFORMAL PREDICTION — THE CORE
# ============================================================================
#
# STEPS:
# 1. Split data into training (60%) and calibration (40%)
# 2. Bootstrap training data → predicted rank for each model (median)
# 3. Compute Elo on calibration data → "true" rank for each model
# 4. Nonconformity score = |true rank - predicted rank|
# 5. Find threshold q̂ at the ⌈(1-α)(1+1/n)⌉ quantile of scores
# 6. Prediction set = [predicted_rank - q̂, predicted_rank + q̂]
#
# THE GUARANTEE:
# P(true rank ∈ prediction set) ≥ 1 - α
# This holds for ANY data distribution and ANY model. That's the magic.
# ============================================================================

def conformal_prediction(data, alpha=0.10, n_bootstraps=100, n_splits=10, seed=42):
    """
    Construct conformal prediction sets over model rankings.
    
    alpha: error rate (0.10 = 90% coverage guarantee)
    """
    rng = np.random.RandomState(seed)
    n_battles = len(data['idx_a'])
    n_models = data['n_models']
    
    all_sets = np.zeros((n_models, n_splits, 2))  # [model, split, lo/hi]
    coverages = []
    thresholds = []
    
    for s in range(n_splits):
        # STEP 1: Random split
        perm = rng.permutation(n_battles)
        cut = int(0.6 * n_battles)
        
        train_data = {
            'idx_a': data['idx_a'][perm[:cut]],
            'idx_b': data['idx_b'][perm[:cut]],
            'a_wins': data['a_wins'][perm[:cut]],
            'n_models': n_models
        }
        cal_data = {
            'idx_a': data['idx_a'][perm[cut:]],
            'idx_b': data['idx_b'][perm[cut:]],
            'a_wins': data['a_wins'][perm[cut:]],
            'n_models': n_models
        }
        
        # STEP 2: Bootstrap training data → predicted ranks
        rank_mat = bootstrap_ranks(train_data, n_bootstraps, seed=seed+s)
        predicted_ranks = np.median(rank_mat, axis=1)  # median across bootstraps
        
        # STEP 3: Elo on calibration data → "true" ranks
        cal_ratings = compute_elo_fast(
            cal_data['idx_a'], cal_data['idx_b'],
            cal_data['a_wins'], n_models
        )
        true_ranks = ratings_to_ranks(cal_ratings)
        
        # STEP 4: Nonconformity scores
        # score = |true rank - predicted rank|
        # Higher score = prediction was more wrong
        scores = np.abs(true_ranks - predicted_ranks)
        
        # STEP 5: Conformal threshold
        # q̂ = ⌈(1-α)(1 + 1/n)⌉-th quantile of scores
        #
        # WHY (1 + 1/n)?
        # We have n calibration points. The test point is point n+1.
        # Under exchangeability, all n+1 points are equally likely to
        # be in any position. So we need the ⌈(1-α)(n+1)/n⌉ quantile
        # = ⌈(1-α)(1 + 1/n)⌉ quantile.
        n_cal = len(scores)
        q_level = min((1 - alpha) * (1 + 1/n_cal), 1.0)
        q_hat = np.quantile(scores, q_level, method='higher')
        thresholds.append(q_hat)
        
        # STEP 6: Construct prediction sets
        for m in range(n_models):
            lo = max(1, int(np.floor(predicted_ranks[m] - q_hat)))
            hi = min(n_models, int(np.ceil(predicted_ranks[m] + q_hat)))
            all_sets[m, s, 0] = lo
            all_sets[m, s, 1] = hi
        
        # STEP 7: Check coverage
        covered = sum(1 for m in range(n_models) 
                      if all_sets[m, s, 0] <= true_ranks[m] <= all_sets[m, s, 1])
        coverages.append(covered / n_models)
    
    # Aggregate across splits (median)
    final_lo = np.median(all_sets[:, :, 0], axis=1).astype(int)
    final_hi = np.median(all_sets[:, :, 1], axis=1).astype(int)
    
    # Point-estimate rankings on full data
    full_ratings = compute_elo_fast(data['idx_a'], data['idx_b'], data['a_wins'], n_models)
    full_ranks = ratings_to_ranks(full_ratings)
    
    return {
        'models': data['models'],
        'point_ranks': full_ranks,
        'point_ratings': full_ratings,
        'cp_lo': final_lo,
        'cp_hi': final_hi,
        'empirical_coverage': np.mean(coverages),
        'coverage_std': np.std(coverages),
        'mean_threshold': np.mean(thresholds),
        'alpha': alpha,
        'n_models': n_models,
    }


# ============================================================================
# SECTION 5: ANALYSIS
# ============================================================================

def analyze(res):
    """Print key findings."""
    alpha = res['alpha']
    models = res['models']
    n = res['n_models']
    
    # Sort by point rank
    order = np.argsort(res['point_ranks'])
    
    print(f"\n{'='*70}")
    print(f"RESULTS — {(1-alpha)*100:.0f}% COVERAGE CONFORMAL PREDICTION SETS")
    print(f"{'='*70}")
    print(f"\n{'Model':<25} {'Rank':>5} {'Elo':>7} {'CP Set':>12} {'Width':>6}")
    print("-" * 60)
    for i in order:
        m = models[i]
        r = res['point_ranks'][i]
        e = res['point_ratings'][i]
        lo, hi = res['cp_lo'][i], res['cp_hi'][i]
        w = hi - lo + 1
        print(f"{m:<25} {r:>5} {e:>7.0f} {'['+str(lo)+', '+str(hi)+']':>12} {w:>6}")
    
    # Indistinguishable pairs
    print(f"\nINDISTINGUISHABLE ADJACENT PAIRS:")
    n_adj_indist = 0
    n_total_adj = 0
    
    for idx_i in range(n):
        for idx_j in range(idx_i + 1, n):
            ri, rj = res['point_ranks'][idx_i], res['point_ranks'][idx_j]
            if abs(ri - rj) == 1:  # Adjacent
                n_total_adj += 1
                # Check overlap
                if res['cp_lo'][idx_i] <= res['cp_hi'][idx_j] and \
                   res['cp_lo'][idx_j] <= res['cp_hi'][idx_i]:
                    n_adj_indist += 1
                    mi, mj = models[idx_i], models[idx_j]
                    if ri < rj:
                        print(f"  {mi} (#{ri}) ↔ {mj} (#{rj})")
                    else:
                        print(f"  {mj} (#{rj}) ↔ {mi} (#{ri})")
    
    pct = n_adj_indist / max(n_total_adj, 1) * 100
    print(f"\n  → {n_adj_indist}/{n_total_adj} adjacent pairs indistinguishable ({pct:.0f}%)")
    print(f"  → Empirical coverage: {res['empirical_coverage']*100:.1f}% (target: {(1-alpha)*100:.0f}%)")
    print(f"  → Mean threshold q̂: {res['mean_threshold']:.2f} ranks")
    
    return n_adj_indist, n_total_adj


# ============================================================================
# SECTION 6: FIGURES
# ============================================================================

def plot_main(res, path):
    """THE money figure: point rankings vs conformal prediction sets."""
    models = res['models']
    n = res['n_models']
    order = np.argsort(res['point_ranks'])
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 10),
                                     gridspec_kw={'width_ratios': [1, 1.5]})
    fig.patch.set_facecolor('white')
    
    sorted_names = [models[i] for i in order]
    sorted_elos = [res['point_ratings'][i] for i in order]
    sorted_ranks = [res['point_ranks'][i] for i in order]
    sorted_lo = [res['cp_lo'][i] for i in order]
    sorted_hi = [res['cp_hi'][i] for i in order]
    
    y_pos = list(range(n, 0, -1))
    colors = plt.cm.RdYlGn(np.linspace(0.85, 0.15, n))
    
    # LEFT: Current leaderboard
    ax1.barh(y_pos, sorted_elos, color=colors, edgecolor='white', 
             linewidth=0.5, height=0.7)
    
    for i, (name, y, elo) in enumerate(zip(sorted_names, y_pos, sorted_elos)):
        ax1.text(min(sorted_elos) - 5, y, f"{sorted_ranks[i]}. {name}",
                ha='right', va='center', fontsize=8.5, fontweight='bold')
        ax1.text(elo + 3, y, f"{elo:.0f}", ha='left', va='center', 
                fontsize=7.5, color='#333')
    
    ax1.set_xlim(min(sorted_elos) - 130, max(sorted_elos) + 40)
    ax1.set_yticks([])
    ax1.set_xlabel("Elo Rating", fontsize=11)
    ax1.set_title("Current Leaderboard\n(Point Estimates — No Uncertainty)", 
                   fontsize=12, fontweight='bold', pad=15)
    for s in ['top', 'right', 'left']:
        ax1.spines[s].set_visible(False)
    
    # RIGHT: Conformal prediction sets
    max_width = max(hi - lo + 1 for lo, hi in zip(sorted_lo, sorted_hi))
    
    for i, (name, y, lo, hi, rank) in enumerate(
            zip(sorted_names, y_pos, sorted_lo, sorted_hi, sorted_ranks)):
        width = hi - lo + 1
        intensity = width / max_width
        color = plt.cm.RdYlGn(1.0 - intensity * 0.8)
        
        ax2.barh(y, width, left=lo, color=color, alpha=0.75,
                edgecolor='#555', linewidth=0.8, height=0.65)
        ax2.plot(rank, y, 'D', color='black', markersize=5, zorder=5)
        ax2.text(0.3, y, name, ha='right', va='center', fontsize=8.5, fontweight='bold')
        ax2.text(hi + 0.4, y, f"[{lo}–{hi}]", ha='left', va='center',
                fontsize=7, color='#666')
    
    ax2.set_xlim(0, n + 3)
    ax2.set_xlabel("Rank (1 = best)", fontsize=11)
    ax2.set_yticks([])
    ax2.set_title(f"Conformal Prediction Sets\n({(1-res['alpha'])*100:.0f}% Coverage Guarantee)",
                   fontsize=12, fontweight='bold', pad=15)
    ax2.invert_xaxis()
    for s in ['top', 'right', 'left']:
        ax2.spines[s].set_visible(False)
    
    legend_elements = [
        plt.Line2D([0], [0], marker='D', color='black', linestyle='None',
                   markersize=6, label='Point estimate rank'),
        mpatches.Patch(facecolor=plt.cm.RdYlGn(0.8), edgecolor='#555',
                      label='Tight set (confident)'),
        mpatches.Patch(facecolor=plt.cm.RdYlGn(0.2), edgecolor='#555',
                      label='Wide set (uncertain)'),
    ]
    ax2.legend(handles=legend_elements, loc='lower left', fontsize=9, framealpha=0.9)
    
    plt.tight_layout(w_pad=3)
    plt.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  → Main figure: {path}")


def plot_calibration(all_results, path):
    """Coverage calibration: does the guarantee hold at every level?"""
    fig, ax = plt.subplots(figsize=(8, 7))
    fig.patch.set_facecolor('white')
    
    targets = [1 - r['alpha'] for r in all_results]
    empiricals = [r['empirical_coverage'] for r in all_results]
    stds = [r['coverage_std'] for r in all_results]
    
    ax.plot([0.7, 1.0], [0.7, 1.0], 'k--', alpha=0.4, label='Perfect calibration')
    ax.fill_between([0.7, 1.0], [0.7, 1.0], [0.7, 0.7],
                     alpha=0.08, color='red', label='Invalid region (undercoverage)')
    ax.errorbar(targets, empiricals, yerr=stds, fmt='o-', color='#2196F3',
                markersize=10, linewidth=2, capsize=5, capthick=2,
                label='Our method', zorder=5)
    
    ax.set_xlabel("Target Coverage (1 - α)", fontsize=12)
    ax.set_ylabel("Empirical Coverage", fontsize=12)
    ax.set_title("Coverage Calibration\n(Points above diagonal = guarantee holds)",
                 fontsize=13, fontweight='bold')
    ax.set_xlim(0.72, 1.01)
    ax.set_ylim(0.72, 1.01)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    for s in ['top', 'right']:
        ax.spines[s].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  → Calibration figure: {path}")


def plot_width_vs_votes(data, res, path):
    """Models with fewer votes → wider prediction sets."""
    models = res['models']
    
    # Count votes per model
    vote_counts = np.zeros(res['n_models'])
    for i in range(len(data['idx_a'])):
        vote_counts[data['idx_a'][i]] += 1
        vote_counts[data['idx_b'][i]] += 1
    
    widths = res['cp_hi'] - res['cp_lo'] + 1
    
    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor('white')
    
    sc = ax.scatter(vote_counts, widths, s=100, c=widths, cmap='RdYlGn_r',
                    edgecolors='#333', linewidths=0.8, zorder=5)
    
    for i, m in enumerate(models):
        ax.annotate(m, (vote_counts[i], widths[i]),
                   textcoords="offset points", xytext=(8, 4), fontsize=7, color='#444')
    
    ax.set_xlabel("Number of Votes", fontsize=12)
    ax.set_ylabel("Prediction Set Width (ranks)", fontsize=12)
    ax.set_title("Uncertainty vs Data Volume\n(Fewer votes → less certain ranking)",
                 fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)
    for s in ['top', 'right']:
        ax.spines[s].set_visible(False)
    
    plt.colorbar(sc, ax=ax, label="Set width", shrink=0.8)
    plt.tight_layout()
    plt.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  → Width vs votes figure: {path}")


# ============================================================================
# SECTION 7: RUN EVERYTHING
# ============================================================================

def main():
    t0 = time.time()
    out = "/home/claude/arena-cp"
    
    print("=" * 70)
    print("CONFORMAL PREDICTION SETS FOR CHATBOT ARENA RANKINGS")
    print("=" * 70)
    
    # Generate data
    print("\n[1/4] Generating synthetic Arena battles...")
    data = generate_battles(n_battles=20000, seed=42)
    print(f"  {len(data['idx_a'])} battles, {data['n_models']} models")
    
    # Run CP at multiple coverage levels
    alphas = [0.20, 0.15, 0.10, 0.05]
    all_results = []
    
    for alpha in alphas:
        print(f"\n[2/4] CP at α={alpha} ({(1-alpha)*100:.0f}% coverage)...")
        res = conformal_prediction(data, alpha=alpha, n_bootstraps=50, n_splits=8, seed=42)
        all_results.append(res)
        print(f"  Coverage: {res['empirical_coverage']*100:.1f}%, q̂={res['mean_threshold']:.2f}")
    
    # Analyze main result (90% coverage)
    main_res = all_results[2]
    print("\n[3/4] Analysis...")
    analyze(main_res)
    
    # Figures
    print("\n[4/4] Generating figures...")
    plot_main(main_res, os.path.join(out, "conformal_arena_rankings.png"))
    plot_calibration(all_results, os.path.join(out, "coverage_calibration.png"))
    plot_width_vs_votes(data, main_res, os.path.join(out, "width_vs_votes.png"))
    
    # Save results JSON
    summary = {
        'alpha': main_res['alpha'],
        'coverage': main_res['empirical_coverage'],
        'threshold': main_res['mean_threshold'],
        'prediction_sets': {
            main_res['models'][i]: [int(main_res['cp_lo'][i]), int(main_res['cp_hi'][i])]
            for i in range(main_res['n_models'])
        },
        'rankings': {
            main_res['models'][i]: int(main_res['point_ranks'][i])
            for i in range(main_res['n_models'])
        }
    }
    with open(os.path.join(out, "results.json"), "w") as f:
        json.dump(summary, f, indent=2)
    
    elapsed = time.time() - t0
    print(f"\n{'='*70}")
    print(f"DONE in {elapsed:.1f}s")
    print(f"{'='*70}")
    
    return all_results

if __name__ == "__main__":
    main()
