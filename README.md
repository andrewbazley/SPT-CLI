GEMspa Analysis Pipeline Guide
Command Line Interface based on the GEMspa analysis pipeline originally written by Sarah Keegan
https://www.biorxiv.org/content/10.1101/2023.06.26.546612v1

Quickrun
cd /Users/andrewbazley/Desktop/GEMspa-CLI
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install -e .
 ./venv/bin/GEMspa-CLI.py --work-dir "/Users/andrewbazley/Desktop/20250716 RLTPSC ER GEM"

1. Introduction
This document describes the components of the GEMspa single-particle tracking (SPT) analysis pipeline, explains what each script does, and shows how to run the entire analysis from the CLI. It also explains the outputs generated and their interpretation.

2. Script Components
2.1 trajectory_analysis.py
Per-replicate MSD and diffusion coefficient analysis:
- Reads a Traj_<condition>_<rep>.csv file containing tracked x,y coordinates and frame numbers.
- Computes mean-squared displacement (MSD) per track (Numba JIT accelerated) and fits to MSD = 4·D·t^α.
- Saves `msd_results.csv` with columns: track_id, condition, D_fit, alpha_fit, r2_fit.
- Plots:
  • D_fit_distribution.png: log‑spaced histogram of D (μm²/s).
  • alpha_vs_logD.png: scatter of α vs. log10(D).
- Optionally overlays colored tracks on the MAX_*.tif image using rainbow colormap.
2.2 msd_diffusion.py
Core MSD computation and fitting utilities:
- `_msd2d_jit`: fast Numba‐parallel function computing 2D MSD up to max lag.
- `fit_msd`: non‐linear least squares (SciPy) to fit MSD to power-law, returns D, α, R².
- `fit_msd_linear`: fallback linear fit for purely diffusive tracks.
- Step‐size export:
  • `set_track_data` and `step_sizes_and_angles` compute step‐size matrices and angles.
  • `save_step_sizes` writes a “long” table with tlag & step_size columns.
2.3 rainbow_tracks.py
Overlay raw tracks on background TIFF images, color‐coded by diffusion coefficient:
- Reads MAX_<condition>_<rep>.tif, converts to RGB canvas.
- Normalizes each track’s D_fit to [min_D, max_D], maps to specified colormap.
- Draws line segments for each track on the image, saves high-resolution PNG.
2.4 step_size_analysis.py
Per-replicate and per-ensemble step-size analysis:
- Expects `all_data_step_sizes.txt` with columns [group, tlag, step_size].
- For each group and each tlag, plots log‑scale KDE of step_size:
  • step_kde_<group>.png (fade by tlag, inset α₂ parameter).
- If two groups present, computes KS test per tlag and plots volcano plot:
  • ks_volcano_<group1>_vs_<group2>.png
2.5 ensemble_analysis.py
Pools replicate `msd_results.csv` by condition and applies filtering:
- Groups folders named <condition>_<rep> and concatenates their x `msd_results.csv`.
- Writes `grouped_raw/msd_results.csv` and `grouped_filtered/msd_results.csv`.
- Generates the same distribution & scatter plots for raw and filtered ensembles.
2.6 compare_conditions.py
Cross-condition comparison on filtered ensemble data:
- Overlaid, density-normalized histograms of D_fit on log x-axis with mean lines and KS-test asterisks.
- Overlaid, density-normalized histograms of α_fit on linear x-axis with mean lines and KS-test asterisks.
- Boxplot of replicate median D_fit with jittered points and Mann–Whitney U (or KS) test asterisk.
2.7 GEMspa-CLI.py
Command-line entry point gluing everything together:
- Discovers Traj_*.csv in --work-dir; processes each in parallel (--n-jobs).
- Runs trajectory_analysis, exports step sizes, runs step_size_analysis if requested.
- After replicates, runs ensemble_analysis and compare_conditions.
- Arguments control filtering, rainbow parameters, and parallelism.
3. CLI Usage
From your activated virtual environment, install and run:
```
pip install -e .
gemspa-cli \
  --work-dir /path/to/data \
  --n-jobs 4 \
  --rainbow-tracks \
  --rainbow-min-D 0 \
  --rainbow-max-D 2 \
  --rainbow-colormap plasma \
  --rainbow-scale 2 \
  --rainbow-dpi 300 \
  --step-size-analysis
```
4. Outputs & Interpretation
- **msd_results.csv**: per-track diffusion (D), anomalous exponent (α), fit quality (R²).
- **D_fit_distribution.png**: shows spread of diffusion coefficients on log scale.
- **alpha_vs_logD.png**: relation between α and D across tracks.
- **rainbow_tracks.png**: raw image with tracks color-coded by D.
- **all_data_step_sizes.txt**: long-form step-size data (group, tlag, step_size).
- **step_kde_<group>.png**: KDE curves of step sizes per tlag, log‐y.
- **ks_volcano_*.png**: p-value vs. tlag comparison between two groups.
- **grouped_raw/msd_results.csv** & plots: pooled per-condition before filtering.
- **grouped_filtered/msd_results.csv** & plots: pooled per-condition within filter bounds.
- **ensemble_filtered_D_histograms.png** & **ensemble_filtered_alpha_histograms.png**: overlaid histograms comparing conditions.
- **replicate_median_D_boxplot.png**: boxplot of median D per replicate with significance.
