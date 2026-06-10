import json
import numpy as np
import time
from conformal_arena import (
    compute_elo_fast, ratings_to_ranks, bootstrap_ranks,
    conformal_prediction, analyze, plot_main, plot_calibration, plot_width_vs_votes
)

def load_real():
    battles = [json.loads(l) for l in open('arena_battles.json')]
    
    # Filter to clear winners only (no ties)
    battles = [b for b in battles if b['winner'] in ('model_a', 'model_b')]
    print(f"{len(battles)} battles after removing ties")
    
    # Build model index
    models = sorted(set(b['model_a'] for b in battles) | set(b['model_b'] for b in battles))
    m2i = {m: i for i, m in enumerate(models)}
    
    idx_a = np.array([m2i[b['model_a']] for b in battles])
    idx_b = np.array([m2i[b['model_b']] for b in battles])
    a_wins = np.array([b['winner'] == 'model_a' for b in battles])
    
    return {'idx_a': idx_a, 'idx_b': idx_b, 'a_wins': a_wins, 'models': models, 'n_models': len(models)}

data = load_real()
print(f"{data['n_models']} models, {len(data['idx_a'])} battles\n")

# Filter to models with at least 100 votes
votes = np.zeros(data['n_models'])
for i in range(len(data['idx_a'])):
    votes[data['idx_a'][i]] += 1
    votes[data['idx_b'][i]] += 1

keep = set(np.where(votes >= 100)[0])
mask = np.array([data['idx_a'][i] in keep and data['idx_b'][i] in keep for i in range(len(data['idx_a']))])

old = data['models']
new_models = [old[i] for i in sorted(keep)]
o2n = {oi: ni for ni, oi in enumerate(sorted(keep))}

data = {
    'idx_a': np.array([o2n[data['idx_a'][i]] for i in range(len(data['idx_a'])) if mask[i]]),
    'idx_b': np.array([o2n[data['idx_b'][i]] for i in range(len(data['idx_b'])) if mask[i]]),
    'a_wins': data['a_wins'][mask],
    'models': new_models,
    'n_models': len(new_models),
}
print(f"After filtering (>=100 votes): {data['n_models']} models, {len(data['idx_a'])} battles\n")

# Run CP at multiple levels
alphas = [0.20, 0.15, 0.10, 0.05]
all_results = []
for alpha in alphas:
    print(f"Running CP at {(1-alpha)*100:.0f}% coverage...")
    res = conformal_prediction(data, alpha=alpha, n_bootstraps=100, n_splits=10, seed=42)
    all_results.append(res)
    print(f"  Coverage: {res['empirical_coverage']*100:.1f}%, q_hat={res['mean_threshold']:.2f}\n")

main_res = all_results[2]
analyze(main_res)

print("\nGenerating figures...")
plot_main(main_res, "real_arena_rankings.png")
plot_calibration(all_results, "real_coverage_calibration.png")
plot_width_vs_votes(data, main_res, "real_width_vs_votes.png")
print("Done. Check real_arena_rankings.png")
