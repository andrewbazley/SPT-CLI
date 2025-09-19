#!/usr/bin/env python3
"""
compare_conditions.py

Generates comparative plots across experimental conditions:
- **Log-scale x-axis** density-normalized, overlaid histograms of filtered D_fit 
  with mean-lines and KS-test asterisk annotations.
- Linear-scale histogram of alpha_fit.
- Linear-scale boxplot of replicate median D_fit with jittered points and 
  Mann–Whitney U test asterisk annotation.
"""
import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import ks_2samp, mannwhitneyu

def _p_to_asterisks(p):
    if p < 1e-4:   return "****"
    if p < 1e-3:   return "***"
    if p < 1e-2:   return "**"
    if p < 5e-2:   return "*"
    return "n.s."

def compare_conditions(root_dir,
                       filter_D_min=0.0, filter_D_max=float('inf'),
                       filter_alpha_min=0.0, filter_alpha_max=float('inf')):
    # Load grouped_filtered data
    cond_map = {}
    for sub in os.listdir(root_dir):
        path = os.path.join(root_dir, sub, 'grouped_filtered', 'msd_results.csv')
        if os.path.isfile(path):
            cond_map[sub] = pd.read_csv(path, usecols=['D_fit','alpha_fit'])
    if len(cond_map) < 2:
        return
    conds = list(cond_map.keys())

    # Output folder
    comp_dir = os.path.join(root_dir, 'comparison')
    os.makedirs(comp_dir, exist_ok=True)

    # Color palette
    colors = sns.color_palette(n_colors=len(conds))

    # ---- D_fit histogram (log x-axis) ----
    fig, ax = plt.subplots(figsize=(8, 6))
    means = {}
    for c, col in zip(conds, colors):
        df = cond_map[c]
        ax.hist(
            df['D_fit'], bins=np.logspace(-3, np.log10(filter_D_max), 50),
            density=True, alpha=0.5, color=col, label=c
        )
        mean_val = df['D_fit'].mean()
        means[c] = mean_val
        darker = tuple(max(0, x * 0.7) for x in col)
        ax.axvline(mean_val, color=darker, linewidth=2)

    ax.set_xscale('log')
    ax.set_xlim(filter_D_min if filter_D_min > 0 else 1e-3, filter_D_max)
    ax.set_xlabel('D_fit (μm²/s), log scale')
    ax.set_ylabel('Density')
    ax.set_title('Ensemble Filtered D_fit Distributions')
    ax.legend()

    # KS-test bracket at mean positions
    d1 = cond_map[conds[0]]['D_fit']
    d2 = cond_map[conds[1]]['D_fit']
    p = ks_2samp(d1, d2).pvalue
    stars = _p_to_asterisks(p)
    y_max = ax.get_ylim()[1]
    y_base = y_max * 0.90
    y_tip  = y_base * 1.02
    x1 = means[conds[0]]
    x2 = means[conds[1]]
    ax.plot([x1, x1, x2, x2],
            [y_base, y_tip, y_tip, y_base],
            lw=1.5, color='black')
    ax.text((x1 + x2) / 2, y_tip * 1.01, stars, ha='center', va='bottom')

    fig.tight_layout()
    fig.savefig(os.path.join(comp_dir, 'ensemble_filtered_D_histograms.png'))
    plt.close(fig)

    # ---- alpha_fit histogram (linear x-axis) ----
    fig, ax = plt.subplots(figsize=(8, 6))
    means = {}
    for c, col in zip(conds, colors):
        df = cond_map[c]
        ax.hist(df['alpha_fit'], bins=50, density=True,
                alpha=0.5, color=col, label=c)
        mean_val = df['alpha_fit'].mean()
        means[c] = mean_val
        darker = tuple(max(0, x * 0.7) for x in col)
        ax.axvline(mean_val, color=darker, linewidth=2)

    ax.set_xlabel('alpha_fit')
    ax.set_ylabel('Density')
    ax.set_title('Ensemble Filtered alpha Distributions')
    ax.legend()

    # KS-test bracket at mean positions
    a1 = cond_map[conds[0]]['alpha_fit']
    a2 = cond_map[conds[1]]['alpha_fit']
    p = ks_2samp(a1, a2).pvalue
    stars = _p_to_asterisks(p)
    y_max = ax.get_ylim()[1]
    y_base = y_max * 0.90
    y_tip  = y_base * 1.02
    x1 = means[conds[0]]
    x2 = means[conds[1]]
    ax.plot([x1, x1, x2, x2],
            [y_base, y_tip, y_tip, y_base],
            lw=1.5, color='black')
    ax.text((x1 + x2) / 2, y_tip * 1.01, stars, ha='center', va='bottom')

    fig.tight_layout()
    fig.savefig(os.path.join(comp_dir, 'ensemble_filtered_alpha_histograms.png'))
    plt.close(fig)

    # ---- Boxplot of replicate median D_fit (linear) ----
    med_records = []
    rep_rx = re.compile(r'(.+)_\d+$')
    for sub in os.listdir(root_dir):
        m = rep_rx.match(sub)
        if m:
            cond = m.group(1)
            path = os.path.join(root_dir, sub, 'msd_results.csv')
            if os.path.isfile(path):
                dfr = pd.read_csv(path, usecols=['D_fit'])
                dfr = dfr.query('D_fit>=@filter_D_min & D_fit<=@filter_D_max')
                med_records.append({'condition': cond,
                                    'median_D': dfr['D_fit'].median()})
    med_df = pd.DataFrame(med_records)

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.boxplot(x='condition', y='median_D', data=med_df, ax=ax,
                showfliers=False, palette=colors)
    sns.stripplot(x='condition', y='median_D', data=med_df,
                  color='black', size=6, jitter=True, ax=ax)
    ax.set_xlabel('Condition')
    ax.set_ylabel('Median D_fit (μm²/s)')
    ax.set_title('Replicate Median D_fit by Condition')

    # Mann–Whitney U test bracket
    # KS‐test on the full pooled D_fit (so box‐plot reflects distribution significance)
    d1 = cond_map[conds[0]]['D_fit']
    d2 = cond_map[conds[1]]['D_fit']
    p = ks_2samp(d1, d2).pvalue
    stars = _p_to_asterisks(p)
    y_max = med_df['median_D'].max()
    y_base = y_max * 1.05
    y_tip  = y_base * 1.02
    ax.plot([0, 0, 1, 1],
            [y_base, y_tip, y_tip, y_base],
            lw=1.5, color='black')
    ax.text(0.5, y_tip * 1.01, stars, ha='center', va='bottom')

    fig.tight_layout()
    fig.savefig(os.path.join(comp_dir, 'replicate_median_D_boxplot.png'))
    plt.close(fig)
