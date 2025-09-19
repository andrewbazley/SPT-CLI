#!/usr/bin/env python3
# gemspa/step_size_analysis.py

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import to_rgba
from scipy.stats import ks_2samp

plt.rcParams['font.size'] = 16

def load_step_data(path):
    """
    Load the tab-delimited step-size file.  
    Expect columns [group, tlag, <step-col>], where <step-col> is any name.
    Rename that third column to 'step_size'.
    """
    df = pd.read_csv(path, sep='\t')
    # drop any rows missing group or tlag
    df = df.dropna(subset=['group','tlag'])
    # find the one “step” column
    step_cols = [c for c in df.columns if c not in ('group','tlag')]
    if not step_cols:
        raise ValueError(f"No step-size column found in {path}")
    df = df.rename(columns={step_cols[0]: 'step_size'})
    return df

def calc_alpha2(obs):
    """
    Non-Gaussian parameter α₂ = ⟨r⁴⟩ / (3⟨r²⟩²) – 1
    """
    m2 = np.mean(obs**2)
    if m2 == 0:
        return np.nan
    return np.mean(obs**4) / (3 * m2**2) - 1

def plot_step_kde(df, results_dir):
    """
    For each group and each tlag, plot a log-scaled KDE of step_size.
    """
    for group, gdf in df.groupby('group'):
        fig, ax = plt.subplots(figsize=(8,6))
        plotted = False
        alpha2_vals = {}

        # determine maximum Tlag for fading
        max_t = gdf['tlag'].max()

        for t, sub in gdf.groupby('tlag'):
            data = sub['step_size'].dropna().to_numpy()
            if data.size == 0:
                continue
            plotted = True
            alpha2_vals[t] = calc_alpha2(data)
            fade = 1 - (t / max_t)
            color = to_rgba("#9573e5", fade)
            sns.kdeplot(
                data,
                ax=ax,
                label=f"Tlag {t}",
                color=color,
                linewidth=2
            )

        if not plotted:
            print(f"[step_size] → no non-empty step_size for group {group!r}, skipping")
            plt.close(fig)
            continue

        ax.set_title(f"{group}")
        ax.set_xlabel("Step Size (μm)")
        ax.set_yscale('log')
        ax.legend(loc='upper right', fontsize=8)

        # inset α₂ values
        txt = "\n".join(f"Tlag {t}: α₂={a2:.2f}" for t,a2 in alpha2_vals.items())
        ax.text(
            0.98, 0.02, txt,
            transform=ax.transAxes,
            ha='right', va='bottom',
            bbox=dict(facecolor='white', alpha=0.8),
            fontsize=8
        )

        plt.tight_layout()
        outfile = os.path.join(results_dir, f"step_kde_{group}.png".replace(" ","_"))
        fig.savefig(outfile)
        plt.close(fig)
        print(f"[step_size] → wrote KDE plot for {group!r} to {outfile}")

def ks_comparison(df, g1, g2, results_dir):
    """
    Perform a KS test of the step_size distributions for each Tlag
    between two groups, and plot p-value vs Tlag.
    """
    results = []
    for t, sub in df.groupby('tlag'):
        d1 = sub.loc[sub['group']==g1, 'step_size'].dropna().to_numpy()
        d2 = sub.loc[sub['group']==g2, 'step_size'].dropna().to_numpy()
        if d1.size<1 or d2.size<1:
            p = np.nan
        else:
            _, p = ks_2samp(d1, d2)
        results.append((t, p))

    # plot
    tlags, pvals = zip(*results)
    fig, ax = plt.subplots(figsize=(7,5))
    ax.scatter(tlags, pvals, edgecolors='green', facecolors='none', label='KS p')
    ax.axhline(0.05, ls='--', color='gray')
    ax.set_yscale('log')
    ax.set_xlabel('Tlag')
    ax.set_ylabel('p-value')
    ax.set_title(f"KS Test: {g1} vs {g2}")
    ax.legend()
    plt.tight_layout()
    out = os.path.join(results_dir, f"ks_volcano_{g1}_vs_{g2}.png".replace(" ","_"))
    fig.savefig(out)
    plt.close(fig)
    print(f"[step_size] → wrote KS volcano to {out}")

def run_step_size_analysis_if_requested(results_dir):
    step_file = os.path.join(results_dir, "all_data_step_sizes.txt")
    if not os.path.exists(step_file):
        print(f"[step_size] file not found: {step_file}")
        return

    try:
        df = load_step_data(step_file)
        print(f"[step_size] loaded {len(df)} rows from {step_file}")

        # KDE plots
        plot_step_kde(df, results_dir)

        # KS test if at least 2 groups
        groups = df['group'].unique()
        if len(groups) >= 2:
            ks_comparison(df, groups[0], groups[1], results_dir)

    except Exception as e:
        print(f"Step-size analysis failed: {e}")
