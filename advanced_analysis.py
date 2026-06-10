"""
=============================================================================
ADVANCED ANALYSIS: Category Slicing, Vote Efficiency, Temporal, CI Comparison
=============================================================================
Run this AFTER run_new.py has completed successfully.
Requires: arena_new.json, conformal_arena.py
=============================================================================
"""

import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import defaultdict, Counter
import time

from conformal_arena import (
    compute_elo_fast, ratings_to_ranks, bootstrap_ranks, conformal_prediction
)

# ============================================================================
# LOAD DATA
# ============================================================================

def load_battles():
    print("Loading battles...")
    battles = [json.loads(l) for l in open('arena_new.json')]
    battles = [b for b in battles if b['winner'] in ('model_a', 'model_b')]
    
    models = sorted(set(b['model_a'] for b in battles) | set(b['model_b'] for b in battles))
    m2i = {m: i for i, m in enumerate(models)}
    
    # Count votes per model
    vote_counts = Counter()
    for b in battles:
        vote_counts[b['model_a']] += 1
        vote_counts[b['model_b']] += 1
    
    # Filter to models with >= 500 votes
    MIN_VOTES = 500
    keep_models = {m for m in models if vote_counts[m] >= MIN_VOTES}
    battles = [b for b in battles if b['model_a'] in keep_models and b['model_b'] in keep_models]
    
    models = sorted(keep_models)
    m2i = {m: i for i, m in enumerate(models)}
    
    print(f"  {len(battles)} battles, {len(models)} models (>={MIN_VOTES} votes)")
    return battles, models, m2i


def battles_to_data(battles, models, m2i):
    """Convert battle list to the numpy format our CP pipeline expects."""
    idx_a = np.array([m2i[b['model_a']] for b in battles])
    idx_b = np.array([m2i[b['model_b']] for b in battles])
    a_wins = np.array([b['winner'] == 'model_a' for b in battles])
    return {'idx_a': idx_a, 'idx_b': idx_b, 'a_wins': a_wins, 
            'models': models, 'n_models': len(models)}


# ============================================================================
# ANALYSIS 1: SLICE BY CATEGORY
# ============================================================================
# 
# WHY THIS MATTERS:
# A single leaderboard assumes Model A is better than Model B at everything.
# But maybe Model A wins at coding and loses at creative writing.
# If prediction sets differ by category, a single ranking is misleading.
#
# THE FINDING WE'RE LOOKING FOR:
# "Models are clearly ranked on coding but indistinguishable on creative
#  writing" — or the reverse. Any category-dependent structure.
# ============================================================================

def analysis_category_slice(battles, models, m2i):
    print("\n" + "="*70)
    print("ANALYSIS 1: CATEGORY SLICING")
    print("="*70)
    
    # Check what categories exist
    categories = Counter()
    for b in battles:
        # category_tag might be a string or a dict — check
        cat = b.get('category_tag', None)
        if cat is None:
            categories['unknown'] += 1
        elif isinstance(cat, dict):
            # Might have nested categories
            for k, v in cat.items():
                if v:
                    categories[k] += 1
        elif isinstance(cat, str):
            categories[cat] += 1
    
    print(f"\nCategories found: {dict(categories.most_common(20))}")
    
    # Also check is_code field
    code_counts = Counter(b.get('is_code', None) for b in battles)
    print(f"is_code values: {dict(code_counts)}")
    
    # Split by is_code (simplest, cleanest split)
    code_battles = [b for b in battles if b.get('is_code') == True]
    noncode_battles = [b for b in battles if b.get('is_code') == False]
    
    print(f"\nCode battles: {len(code_battles)}")
    print(f"Non-code battles: {len(noncode_battles)}")
    
    results = {}
    
    for label, subset in [("Code", code_battles), ("Non-Code", noncode_battles)]:
        if len(subset) < 1000:
            print(f"  Skipping {label}: too few battles ({len(subset)})")
            continue
        
        # Filter to models that appear in this subset
        sub_models_set = set()
        for b in subset:
            sub_models_set.add(b['model_a'])
            sub_models_set.add(b['model_b'])
        
        # Only keep models with enough votes in this category
        sub_vote_counts = Counter()
        for b in subset:
            sub_vote_counts[b['model_a']] += 1
            sub_vote_counts[b['model_b']] += 1
        
        sub_models = sorted(m for m in sub_models_set if m in set(models) and sub_vote_counts[m] >= 50)
        if len(sub_models) < 5:
            print(f"  Skipping {label}: too few qualifying models ({len(sub_models)})")
            continue
        
        sub_m2i = {m: i for i, m in enumerate(sub_models)}
        sub_battles = [b for b in subset if b['model_a'] in sub_m2i and b['model_b'] in sub_m2i]
        
        data = battles_to_data(sub_battles, sub_models, sub_m2i)
        print(f"\n  Running CP on {label}: {len(sub_battles)} battles, {len(sub_models)} models...")
        
        res = conformal_prediction(data, alpha=0.10, n_bootstraps=80, n_splits=8, seed=42)
        results[label] = res
        
        # Count indistinguishable adjacent pairs
        order = np.argsort(res['point_ranks'])
        n_adj = 0
        n_indist = 0
        for idx in range(len(order) - 1):
            i, j = order[idx], order[idx + 1]
            n_adj += 1
            if res['cp_lo'][i] <= res['cp_hi'][j] and res['cp_lo'][j] <= res['cp_hi'][i]:
                n_indist += 1
        
        pct = n_indist / max(n_adj, 1) * 100
        print(f"  {label}: {n_indist}/{n_adj} adjacent pairs indistinguishable ({pct:.0f}%)")
        print(f"  Coverage: {res['empirical_coverage']*100:.1f}%, q_hat: {res['mean_threshold']:.2f}")
    
    # Plot comparison if we have both
    if len(results) >= 2:
        plot_category_comparison(results)
    
    return results


def plot_category_comparison(results):
    """Side-by-side prediction sets for Code vs Non-Code."""
    fig, axes = plt.subplots(1, len(results), figsize=(8 * len(results), 12))
    fig.patch.set_facecolor('white')
    
    if len(results) == 1:
        axes = [axes]
    
    for ax, (label, res) in zip(axes, results.items()):
        models = res['models']
        n = res['n_models']
        order = np.argsort(res['point_ranks'])
        
        y_pos = list(range(n, 0, -1))
        max_width = max(res['cp_hi'][i] - res['cp_lo'][i] + 1 for i in range(n))
        
        for pos, idx in enumerate(order):
            y = y_pos[pos]
            lo, hi = res['cp_lo'][idx], res['cp_hi'][idx]
            rank = res['point_ranks'][idx]
            width = hi - lo + 1
            intensity = width / max(max_width, 1)
            color = plt.cm.RdYlGn(1.0 - intensity * 0.8)
            
            ax.barh(y, width, left=lo, color=color, alpha=0.75,
                    edgecolor='#555', linewidth=0.8, height=0.7)
            ax.plot(rank, y, 'D', color='black', markersize=4, zorder=5)
            ax.text(0.3, y, models[idx], ha='right', va='center', fontsize=7, fontweight='bold')
        
        ax.set_xlim(0, n + 2)
        ax.set_xlabel("Rank", fontsize=11)
        ax.set_yticks([])
        ax.set_title(f"{label}\n({res['empirical_coverage']*100:.0f}% coverage)", 
                     fontsize=13, fontweight='bold')
        ax.invert_xaxis()
        for s in ['top', 'right', 'left']:
            ax.spines[s].set_visible(False)
    
    plt.suptitle("Conformal Prediction Sets: Code vs Non-Code Tasks", 
                 fontsize=15, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig("category_comparison.png", dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  → Saved: category_comparison.png")


# ============================================================================
# ANALYSIS 2: VOTE EFFICIENCY
# ============================================================================
#
# WHY THIS MATTERS:
# How many votes does a model need before its ranking is trustworthy?
# If the answer is 5,000 and some models have 500, Arena is publishing
# unreliable rankings for those models.
#
# THE FINDING WE'RE LOOKING FOR:
# A clear knee point — "after N votes, prediction sets stabilize"
# ============================================================================

def analysis_vote_efficiency(battles, models, m2i):
    print("\n" + "="*70)
    print("ANALYSIS 2: VOTE EFFICIENCY")
    print("="*70)
    
    # For different vote thresholds, measure average prediction set width
    thresholds = [100, 200, 500, 1000, 2000, 3000, 5000]
    
    # Count votes per model
    vote_counts = Counter()
    for b in battles:
        vote_counts[b['model_a']] += 1
        vote_counts[b['model_b']] += 1
    
    avg_widths = []
    n_models_list = []
    
    for thresh in thresholds:
        qualifying = sorted(m for m in models if vote_counts[m] >= thresh)
        if len(qualifying) < 5:
            print(f"  Threshold {thresh}: only {len(qualifying)} models, skipping")
            avg_widths.append(None)
            n_models_list.append(len(qualifying))
            continue
        
        q_m2i = {m: i for i, m in enumerate(qualifying)}
        sub = [b for b in battles if b['model_a'] in q_m2i and b['model_b'] in q_m2i]
        data = battles_to_data(sub, qualifying, q_m2i)
        
        print(f"  Threshold {thresh}: {len(qualifying)} models, {len(sub)} battles...")
        res = conformal_prediction(data, alpha=0.10, n_bootstraps=60, n_splits=6, seed=42)
        
        widths = res['cp_hi'] - res['cp_lo'] + 1
        avg_w = np.mean(widths)
        avg_widths.append(avg_w)
        n_models_list.append(len(qualifying))
        print(f"    Avg set width: {avg_w:.1f}, coverage: {res['empirical_coverage']*100:.1f}%")
    
    # Also: per-model analysis at the 100-vote threshold
    # Show each model's votes vs its prediction set width
    qualifying = sorted(m for m in models if vote_counts[m] >= 100)
    q_m2i = {m: i for i, m in enumerate(qualifying)}
    sub = [b for b in battles if b['model_a'] in q_m2i and b['model_b'] in q_m2i]
    data = battles_to_data(sub, qualifying, q_m2i)
    res = conformal_prediction(data, alpha=0.10, n_bootstraps=80, n_splits=8, seed=42)
    
    model_votes = np.array([vote_counts[m] for m in qualifying])
    model_widths = res['cp_hi'] - res['cp_lo'] + 1
    
    # Plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    fig.patch.set_facecolor('white')
    
    # Left: average width vs vote threshold
    valid = [(t, w) for t, w in zip(thresholds, avg_widths) if w is not None]
    if valid:
        ts, ws = zip(*valid)
        ax1.plot(ts, ws, 'o-', color='#2196F3', markersize=10, linewidth=2)
        ax1.set_xlabel("Minimum Vote Threshold", fontsize=12)
        ax1.set_ylabel("Average Prediction Set Width (ranks)", fontsize=12)
        ax1.set_title("How Many Votes for Reliable Rankings?", fontsize=13, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        for s in ['top', 'right']:
            ax1.spines[s].set_visible(False)
    
    # Right: per-model scatter
    sc = ax2.scatter(model_votes, model_widths, s=60, c=model_widths, cmap='RdYlGn_r',
                     edgecolors='#333', linewidths=0.5, zorder=5)
    
    # Label outliers (widest sets and most-voted)
    for i in range(len(qualifying)):
        if model_widths[i] >= np.percentile(model_widths, 90) or model_votes[i] >= np.percentile(model_votes, 90):
            ax2.annotate(qualifying[i], (model_votes[i], model_widths[i]),
                        textcoords="offset points", xytext=(5, 3), fontsize=6, color='#444')
    
    ax2.set_xlabel("Number of Votes", fontsize=12)
    ax2.set_ylabel("Prediction Set Width (ranks)", fontsize=12)
    ax2.set_title("Per-Model: Votes vs Uncertainty", fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    for s in ['top', 'right']:
        ax2.spines[s].set_visible(False)
    plt.colorbar(sc, ax=ax2, label="Set width", shrink=0.8)
    
    plt.tight_layout()
    plt.savefig("vote_efficiency.png", dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  → Saved: vote_efficiency.png")


# ============================================================================
# ANALYSIS 3: TEMPORAL ANALYSIS
# ============================================================================
#
# WHY THIS MATTERS:
# Votes collected over months. Do rankings shift? Are early votes
# consistent with late votes? If not, exchangeability is violated
# and that's both a finding AND a bridge to adaptive CP methods.
# ============================================================================

def analysis_temporal(battles, models, m2i):
    print("\n" + "="*70)
    print("ANALYSIS 3: TEMPORAL ANALYSIS")
    print("="*70)
    
    # Check timestamp format
    sample_ts = battles[0].get('timestamp', battles[0].get('tstamp', None))
    print(f"  Sample timestamp: {sample_ts} (type: {type(sample_ts)})")
    
    # Get all timestamps
    timestamps = []
    for b in battles:
        ts = b.get('timestamp', b.get('tstamp', None))
        if ts is not None:
            if isinstance(ts, str):
                # Try parsing
                from datetime import datetime
                try:
                    ts = datetime.fromisoformat(ts.replace('Z', '+00:00')).timestamp()
                except:
                    ts = float(ts)
            timestamps.append(float(ts))
        else:
            timestamps.append(0)
    
    timestamps = np.array(timestamps)
    
    if timestamps.max() == 0:
        print("  No timestamps found, skipping temporal analysis")
        return
    
    # Sort battles by time and split into thirds
    sorted_idx = np.argsort(timestamps)
    n = len(sorted_idx)
    third = n // 3
    
    periods = {
        "Early": sorted_idx[:third],
        "Middle": sorted_idx[third:2*third],
        "Late": sorted_idx[2*third:]
    }
    
    period_results = {}
    
    for period_name, indices in periods.items():
        period_battles = [battles[i] for i in indices]
        
        # Filter to models with enough votes in this period
        period_votes = Counter()
        for b in period_battles:
            period_votes[b['model_a']] += 1
            period_votes[b['model_b']] += 1
        
        period_models = sorted(m for m in models if period_votes[m] >= 30)
        if len(period_models) < 5:
            print(f"  Skipping {period_name}: only {len(period_models)} qualifying models")
            continue
        
        p_m2i = {m: i for i, m in enumerate(period_models)}
        sub = [b for b in period_battles if b['model_a'] in p_m2i and b['model_b'] in p_m2i]
        data = battles_to_data(sub, period_models, p_m2i)
        
        print(f"  {period_name}: {len(sub)} battles, {len(period_models)} models")
        res = conformal_prediction(data, alpha=0.10, n_bootstraps=60, n_splits=6, seed=42)
        period_results[period_name] = res
        
        avg_width = np.mean(res['cp_hi'] - res['cp_lo'] + 1)
        print(f"    Avg set width: {avg_width:.1f}, coverage: {res['empirical_coverage']*100:.1f}%")
    
    if len(period_results) >= 2:
        # Find models common to all periods
        common = None
        for res in period_results.values():
            s = set(res['models'])
            common = s if common is None else common & s
        
        if common and len(common) >= 5:
            print(f"\n  Models in all periods: {len(common)}")
            
            # Check rank stability: does model X have the same rank across periods?
            rank_shifts = []
            for model in sorted(common):
                ranks = {}
                for period_name, res in period_results.items():
                    if model in res['models']:
                        idx = res['models'].index(model)
                        ranks[period_name] = res['point_ranks'][idx]
                if len(ranks) >= 2:
                    vals = list(ranks.values())
                    shift = max(vals) - min(vals)
                    rank_shifts.append((model, ranks, shift))
            
            rank_shifts.sort(key=lambda x: -x[2])
            print(f"\n  BIGGEST RANK SHIFTS ACROSS TIME:")
            for model, ranks, shift in rank_shifts[:10]:
                rank_str = ", ".join(f"{p}: #{r}" for p, r in ranks.items())
                print(f"    {model}: {rank_str} (shift: {shift})")
        
        # Plot
        fig, ax = plt.subplots(figsize=(10, 7))
        fig.patch.set_facecolor('white')
        
        period_names = list(period_results.keys())
        avg_widths = [np.mean(period_results[p]['cp_hi'] - period_results[p]['cp_lo'] + 1) 
                      for p in period_names]
        coverages = [period_results[p]['empirical_coverage'] for p in period_names]
        
        x = range(len(period_names))
        bars = ax.bar(x, avg_widths, color=['#4CAF50', '#FFC107', '#F44336'], 
                      edgecolor='#333', linewidth=0.8, width=0.6)
        
        for i, (w, c) in enumerate(zip(avg_widths, coverages)):
            ax.text(i, w + 0.2, f"Width: {w:.1f}\nCov: {c*100:.0f}%", 
                    ha='center', va='bottom', fontsize=10)
        
        ax.set_xticks(x)
        ax.set_xticklabels(period_names, fontsize=12)
        ax.set_ylabel("Average Prediction Set Width (ranks)", fontsize=12)
        ax.set_title("Do Rankings Change Over Time?\n(Wider sets = less stable rankings)", 
                     fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        for s in ['top', 'right']:
            ax.spines[s].set_visible(False)
        
        plt.tight_layout()
        plt.savefig("temporal_analysis.png", dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()
        print("  → Saved: temporal_analysis.png")


# ============================================================================
# ANALYSIS 4: COMPARE TO ARENA'S EXISTING BOOTSTRAP CIs
# ============================================================================
#
# WHY THIS MATTERS:
# Arena already reports ±5-8 point Elo CIs using standard bootstrap.
# Those assume the Bradley-Terry model is correct (it might not be)
# and use asymptotic arguments (approximate, not exact).
# Our CP sets are distribution-free and finite-sample exact.
# If our sets are wider, Arena's CIs are over-confident.
# ============================================================================

def analysis_ci_comparison(battles, models, m2i):
    print("\n" + "="*70)
    print("ANALYSIS 4: CP SETS vs BOOTSTRAP CONFIDENCE INTERVALS")
    print("="*70)
    
    data = battles_to_data(battles, models, m2i)
    n_models = len(models)
    
    # Standard bootstrap CIs on Elo ratings (what Arena currently does)
    print("  Computing bootstrap CIs (Arena's method)...")
    n_boot = 200
    rng = np.random.RandomState(42)
    n_battles = len(data['idx_a'])
    
    boot_ratings = np.zeros((n_models, n_boot))
    boot_ranks = np.zeros((n_models, n_boot), dtype=int)
    
    for b in range(n_boot):
        idx = rng.choice(n_battles, size=n_battles, replace=True)
        ratings = compute_elo_fast(data['idx_a'][idx], data['idx_b'][idx],
                                   data['a_wins'][idx], n_models)
        boot_ratings[:, b] = ratings
        boot_ranks[:, b] = ratings_to_ranks(ratings)
    
    # Bootstrap 95% CI on ranks
    boot_lo = np.percentile(boot_ranks, 2.5, axis=1).astype(int)
    boot_hi = np.percentile(boot_ranks, 97.5, axis=1).astype(int)
    boot_widths = boot_hi - boot_lo + 1
    
    # Our conformal prediction sets (90% coverage for fair comparison — 
    # CP at 90% should be tighter than bootstrap at 95%)
    print("  Computing conformal prediction sets...")
    cp_res = conformal_prediction(data, alpha=0.10, n_bootstraps=100, n_splits=10, seed=42)
    cp_widths = cp_res['cp_hi'] - cp_res['cp_lo'] + 1
    
    # Also run CP at 95% for direct comparison
    cp95_res = conformal_prediction(data, alpha=0.05, n_bootstraps=100, n_splits=10, seed=42)
    cp95_widths = cp95_res['cp_hi'] - cp95_res['cp_lo'] + 1
    
    # Compare
    order = np.argsort(cp_res['point_ranks'])
    
    print(f"\n  {'Model':<30} {'Boot 95%':>10} {'CP 90%':>10} {'CP 95%':>10} {'CP wider?':>10}")
    print("  " + "-"*75)
    
    n_cp_wider = 0
    for i in order[:30]:  # Top 30
        m = models[i]
        bw = boot_widths[i]
        cw = cp95_widths[i]
        wider = "YES" if cw > bw else "no"
        if cw > bw:
            n_cp_wider += 1
        bset = "[{}-{}]".format(boot_lo[i], boot_hi[i])
        cpset = "[{}-{}]".format(cp_res['cp_lo'][i], cp_res['cp_hi'][i])
        cp95set = "[{}-{}]".format(cp95_res['cp_lo'][i], cp95_res['cp_hi'][i])
        print(f"  {m:<30} {bset:>10} {cpset:>10} {cp95set:>10} {wider:>10}")
    
    n_compared = min(30, n_models)
    print(f"\n  CP 95% sets wider than Bootstrap 95% CIs: {n_cp_wider}/{n_compared} models")
    if n_cp_wider > n_compared // 2:
        print("  → Arena's bootstrap CIs may be OVERCONFIDENT")
    else:
        print("  → Arena's bootstrap CIs are reasonably calibrated")
    
    # Plot
    fig, ax = plt.subplots(figsize=(14, 10))
    fig.patch.set_facecolor('white')
    
    y_pos = list(range(min(25, n_models), 0, -1))
    top_n = min(25, n_models)
    
    for pos, idx in enumerate(order[:top_n]):
        y = y_pos[pos]
        
        # Bootstrap CI (red, semi-transparent)
        ax.barh(y + 0.15, boot_widths[idx], left=boot_lo[idx], 
                color='#FF5252', alpha=0.5, height=0.3, 
                edgecolor='#C62828', linewidth=0.8, label='Bootstrap 95% CI' if pos == 0 else '')
        
        # CP 95% set (blue, semi-transparent)  
        ax.barh(y - 0.15, cp95_widths[idx], left=cp95_res['cp_lo'][idx],
                color='#2196F3', alpha=0.5, height=0.3,
                edgecolor='#1565C0', linewidth=0.8, label='Conformal 95%' if pos == 0 else '')
        
        # Point rank
        ax.plot(cp_res['point_ranks'][idx], y, 'D', color='black', markersize=4, zorder=5)
        
        # Label
        ax.text(0.3, y, models[idx], ha='right', va='center', fontsize=7, fontweight='bold')
    
    ax.set_xlim(0, top_n + 3)
    ax.set_xlabel("Rank (1 = best)", fontsize=12)
    ax.set_yticks([])
    ax.set_title("Bootstrap CIs (Arena's method) vs Conformal Prediction Sets\n"
                 "Blue wider than red = Arena is overconfident",
                 fontsize=13, fontweight='bold')
    ax.invert_xaxis()
    ax.legend(fontsize=11, loc='lower left')
    for s in ['top', 'right', 'left']:
        ax.spines[s].set_visible(False)
    
    plt.tight_layout()
    plt.savefig("ci_comparison.png", dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  → Saved: ci_comparison.png")


# ============================================================================
# RUN ALL ANALYSES
# ============================================================================

def main():
    t0 = time.time()
    battles, models, m2i = load_battles()
    
    analysis_category_slice(battles, models, m2i)
    analysis_vote_efficiency(battles, models, m2i)
    analysis_temporal(battles, models, m2i)
    analysis_ci_comparison(battles, models, m2i)
    
    print(f"\n{'='*70}")
    print(f"ALL ANALYSES COMPLETE in {time.time()-t0:.0f}s")
    print(f"{'='*70}")
    print(f"\nFigures generated:")
    print(f"  1. category_comparison.png  — Code vs Non-Code ranking differences")
    print(f"  2. vote_efficiency.png      — How many votes for reliable rankings")
    print(f"  3. temporal_analysis.png    — Do rankings shift over time")
    print(f"  4. ci_comparison.png        — Our CP sets vs Arena's bootstrap CIs")
    print(f"\nEach figure = a section in your paper.")

if __name__ == "__main__":
    main()
