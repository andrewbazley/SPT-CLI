#!/usr/bin/env python3
"""
ensemble_analysis.py

Optimized ensemble grouping and filtering for replicate MSD results.
Parallelized per-condition processing for speed.
"""
import os
import re
import pandas as pd
from joblib import Parallel, delayed
from .trajectory_analysis import trajectory_analysis


def _process_condition(cond_dirs_tuple, root_dir,
                       filter_D_min, filter_D_max,
                       filter_alpha_min, filter_alpha_max):
    cond, dirs = cond_dirs_tuple
    # Load and concatenate raw results with minimal columns
    paths = [os.path.join(d, 'msd_results.csv') for d in dirs]
    dfs = [pd.read_csv(p, usecols=['track_id','D_fit','alpha_fit'])
           for p in paths if os.path.isfile(p)]
    if not dfs:
        return
    raw_ens = pd.concat(dfs, ignore_index=True)

    # Write raw ensemble
    out_raw = os.path.join(root_dir, cond, 'grouped_raw')
    os.makedirs(out_raw, exist_ok=True)
    raw_ens.to_csv(os.path.join(out_raw, 'msd_results.csv'), index=False)
    # Plot raw ensemble
    ta = trajectory_analysis.__new__(trajectory_analysis)
    ta.results_df = raw_ens
    ta.condition = cond
    ta.results_dir = out_raw
    ta.results_df = raw_ens
    ta.make_plot()
    ta.make_scatter()

    # Filter and write filtered ensemble
    filt = raw_ens.query(
        'D_fit >= @filter_D_min and D_fit <= @filter_D_max and '
        'alpha_fit >= @filter_alpha_min and alpha_fit <= @filter_alpha_max'
    )
    out_filt = os.path.join(root_dir, cond, 'grouped_filtered')
    os.makedirs(out_filt, exist_ok=True)
    filt.to_csv(os.path.join(out_filt, 'msd_results.csv'), index=False)
    # Plot filtered
    ta.results_df = filt
    ta.results_dir = out_filt
    ta.results_df = raw_ens
    ta.make_plot()
    ta.make_scatter()


def run_ensemble(root_dir,
                 filter_D_min=0.0, filter_D_max=float('inf'),
                 filter_alpha_min=0.0, filter_alpha_max=float('inf')):
    """
    Parallel grouping and filtering of replicate MSD results by condition.

    Parameters
    ----------
    root_dir : str
        Root directory containing replicate subfolders named <cond>_<replicate>.
    filter_D_min, filter_D_max : float
        Bounds for Diffusion coefficient filtering applied to filtered ensemble.
    filter_alpha_min, filter_alpha_max : float
        Bounds for alpha filtering applied to filtered ensemble.
    """
    # Build condition-to-replicate map
    cond_map = {}
    for sub in os.listdir(root_dir):
        path = os.path.join(root_dir, sub)
        if os.path.isdir(path) and re.match(r'.+_[0-9]+$', sub):
            cond = re.sub(r'_[0-9]+$', '', sub)
            cond_map.setdefault(cond, []).append(path)
    # Parallel processing
    Parallel(n_jobs=-1)(
        delayed(_process_condition)(item, root_dir,
                                    filter_D_min, filter_D_max,
                                    filter_alpha_min, filter_alpha_max)
        for item in cond_map.items()
    )
