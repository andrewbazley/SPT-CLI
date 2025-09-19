# GEMspa Analysis Pipeline Guide


Command Line Interface based on the GEMspa analysis pipeline originally written by Sarah Keegan
https://www.biorxiv.org/content/10.1101/2023.06.26.546612v1

## Table of Contents

- [Requirements](#requirements)
- [Overview](#overview)
- [Input file format & folder organization](#input-file-format--folder-organization)
- [CLI Usage](#cli-usage)
- [CLI Argument Reference](#cli-argument-reference)
- [Outputs & Interpretation](#outputs--interpretation)
- [Script Components](#script-components)

GEMspa Analysis Pipeline Guide
Command Line Interface based on the GEMspa analysis pipeline originally written by Sarah Keegan
https://www.biorxiv.org/content/10.1101/2023.06.26.546612v1

## Requirements


------------
```
numpy>=1.21.0,<1.25.0
pandas>=1.3.0,<2.0.0
scipy>=1.7.0,<2.0.0
matplotlib>=3.4.0,<4.0.0
seaborn>=0.11.0,<1.3.0
scikit-image>=0.19.0,<0.21.0
tifffile>=2020.12.8,<2022.0.0
nd2reader>=3.0.0,<4.0.0
joblib>=1.2.0,<2.0.0
numba>=0.55.0,<0.60.0
```


## Overview


--------
Create and activate a virtual environment, install required dependencies, and set the working directory to the analysis folder.

```
cd /Users/andrewbazley/Desktop/GEMspa-CLI
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install -e .
./venv/bin/GEMspa-CLI.py --work-dir "/Users/andrewbazley/Desktop/20250716 RLTPSC ER GEM"
```

Then you can run the GEMspa-CLI.py script, which executes the analysis with the following arguments/parameters:
```
pip install -e .
gemspa-cli   --work-dir /path/to/data   --n-jobs 4   --rainbow-tracks   --rainbow-min-D 0   --rainbow-max-D 2   --rainbow-colormap plasma   --rainbow-scale 2   --rainbow-dpi 300   --step-size-analysis
```


## Input file format & folder organization

1) File location
   - Place all tracking CSVs in a single (non‑recursive) working folder; the CLI searches only that folder for files matching: Traj_*.csv

2) Required CSV schema (case‑insensitive headers)
   - Columns: track_id, frame, x, y
     • 'trajectory' is accepted as an alias for 'track_id'.
     • Extra columns are ignored.
   - Delimiters: comma or tab; auto‑detected.
   - Types:
     • track_id: integer or string label per trajectory
     • frame: integer frame index (0‑ or 1‑based both OK)
     • x, y: positions in pixels (the script converts to μm using --micron-per-px)

3) File naming → condition & replicate parsing
   - Expected filename pattern: Traj_<condition>_<rep>.csv
     • Examples: Traj_DMSO_001.csv, Traj_Tg_002.csv, Traj_ssGFP_03.csv
   - The replicate name is the filename stem without the 'Traj_' prefix.
   - The condition is inferred by stripping a trailing _<rep> number from the stem.
     • Example: 'Traj_DMSO_001.csv' → replicate='DMSO_001', condition='DMSO'

4) Pairing with images (optional; for --rainbow-tracks)
   - Place a corresponding TIFF in the same folder; default prefix is MAX_
     • Example names searched: MAX_<condition>_<rep>.tif, MAX_<condition>.tif, or any MAX_<condition>* .tif
   - Control behavior with --img-prefix (default: MAX_).

5) Example folder layout
   /data/spa_runs/
   ├── Traj_DMSO_001.csv
   ├── Traj_DMSO_002.csv
   ├── Traj_Tg_001.csv
   ├── Traj_Tg_002.csv
   ├── MAX_DMSO_001.tif        (optional, rainbow overlay)
   ├── MAX_DMSO_002.tif        (optional)
   ├── MAX_Tg_001.tif          (optional)
   └── MAX_Tg_002.tif          (optional)

## Using TrackMate outputs

GEMspa can ingest TrackMate’s **“Spots in tracks”** CSV exports with a simple header map.

**Export from TrackMate**
- In Fiji/TrackMate, export the table **Spots in tracks** as CSV.

**Header mapping (case‑insensitive)**
- `TRACK_ID` → `track_id`
- `FRAME` → `frame`
- `POSITION_X` → `x`
- `POSITION_Y` → `y`

Extra columns are ignored. Delimiter can be comma or tab.

**Units**
- GEMspa assumes `x, y` are in **pixels** and converts using `--micron-per-px`.
- If your TrackMate export is already in **microns**, run with `--micron-per-px 1.0` (or convert back to pixels).

**File names / discovery**
- **Option A (no renaming needed, if your CLI supports `--csv-pattern`)**  
  Use a glob that matches your TrackMate files:
  ```bash
  gemspa-cli     --work-dir /path/to/folder     --csv-pattern "*Spots in tracks*.csv"     --micron-per-px 1.0     --n-jobs 4
  ```
- **Option B (rename or batch‑convert to `Traj_<condition>_<rep>.csv`)**  
  If your CLI doesn’t have `--csv-pattern`, either rename files or run this quick Python helper in the folder with TrackMate CSVs:
  ```python
  import pandas as pd, glob, os, re
  for f in glob.glob("*.csv"):
      df = pd.read_csv(f)
      # normalize headers to lower
      df.columns = [c.lower() for c in df.columns]
      rename = {}
      for src, dest in [('track_id','track_id'), ('trajectory','track_id'),
                        ('frame','frame'),
                        ('position_x','x'), ('x','x'),
                        ('position_y','y'), ('y','y')]:
          if src in df.columns: rename[src] = dest
      df = df.rename(columns=rename)
      req = {'track_id','frame','x','y'}
      if not req.issubset(set(df.columns)): 
          print("Skip", f, "missing", req - set(df.columns)); 
          continue
      stem = os.path.splitext(os.path.basename(f))[0]
      m = re.match(r"(.*)_(\d+)$", stem)
      condition, rep = (m.group(1), m.group(2)) if m else ("COND", "001")
      out = f"Traj_{condition}_{rep}.csv"
      df.to_csv(out, index=False)
      print("Wrote", out)
  ```

**Example folder** (after Option B conversion)
```
/data/spa_runs/
├── Traj_DMSO_001.csv
├── Traj_DMSO_002.csv
├── Traj_Tg_001.csv
└── Traj_Tg_002.csv
```

## CLI Usage


------------
From your activated virtual environment, install and run:
```
pip install -e .
gemspa-cli   --work-dir /path/to/data   --n-jobs 4   --rainbow-tracks   --rainbow-min-D 0   --rainbow-max-D 2   --rainbow-colormap plasma   --rainbow-scale 2   --rainbow-dpi 300   --step-size-analysis
```


## CLI Argument Reference

## Basic usage

python GEMspa-CLI.py -d /path/to/TrajCSVs [options]

## Required

- -d, --work-dir PATH — Folder containing Traj_*.csv files; empty files are skipped.
  Replicate name = filename without 'Traj_' and extension; condition is auto-parsed
  by stripping a trailing _<rep#> (e.g., DMSO_001 → condition 'DMSO').

## Input file format & folder organization

1) File location
   - Place all tracking CSVs in a single (non‑recursive) working folder; the CLI searches only that folder for files matching: Traj_*.csv

2) Required CSV schema (case‑insensitive headers)
   - Columns: track_id, frame, x, y
     • 'trajectory' is accepted as an alias for 'track_id'.
     • Extra columns are ignored.
   - Delimiters: comma or tab; auto‑detected.
   - Types:
     • track_id: integer or string label per trajectory
     • frame: integer frame index (0‑ or 1‑based both OK)
     • x, y: positions in pixels (the script converts to μm using --micron-per-px)

3) File naming → condition & replicate parsing
   - Expected filename pattern: Traj_<condition>_<rep>.csv
     • Examples: Traj_DMSO_001.csv, Traj_Tg_002.csv, Traj_ssGFP_03.csv
   - The replicate name is the filename stem without the 'Traj_' prefix.
   - The condition is inferred by stripping a trailing _<rep> number from the stem.
     • Example: 'Traj_DMSO_001.csv' → replicate='DMSO_001', condition='DMSO'

4) Pairing with images (optional; for --rainbow-tracks)
   - Place a corresponding TIFF in the same folder; default prefix is MAX_
     • Example names searched: MAX_<condition>_<rep>.tif, MAX_<condition>.tif, or any MAX_<condition>* .tif
   - Control behavior with --img-prefix (default: MAX_).

5) Example folder layout
   /data/spa_runs/
   ├── Traj_DMSO_001.csv
   ├── Traj_DMSO_002.csv
   ├── Traj_Tg_001.csv
   ├── Traj_Tg_002.csv
   ├── MAX_DMSO_001.tif        (optional, rainbow overlay)
   ├── MAX_DMSO_002.tif        (optional)
   ├── MAX_Tg_001.tif          (optional)
   └── MAX_Tg_002.tif          (optional)

## Parallelism

- -j, --n-jobs INT — Number of parallel processes across replicates (default: CPU cores).
- --threads-per-rep INT — Threads per replicate (default: max(1, cores / n_jobs)).
  Tip: keep n_jobs × threads_per_rep ≤ cores.

## Core SPT / MSD fit parameters

- --time-step FLOAT — Frame interval in seconds (default: 0.010).
- --micron-per-px FLOAT — Pixel size in μm/px (default: 0.11).
- --ts-resolution FLOAT — Time resolution used internally for plots/labels (default: 0.005).
- --min-track-len INT — Minimum frames per track to fit (default: 11).
- --tlag-cutoff INT — Max lag for MSD fitting (default: 10).

## Optional “rainbow tracks” overlay

- --rainbow-tracks — Enable diffusion-colored track overlays.
  Looks for a TIFF with prefix given by --img-prefix near the CSVs (e.g., MAX_<cond>_<rep>.tif,
  MAX_<cond>.tif, or MAX_<cond>* .tif).
- --img-prefix STR — Image filename prefix (default: MAX_).
- --rainbow-min-D FLOAT (default: 0.0)
- --rainbow-max-D FLOAT (default: 2.0)
- --rainbow-colormap STR (default: viridis)
- --rainbow-scale FLOAT (default: 1.0)
- --rainbow-dpi INT (default: 200)

## Ensemble filtering & cross-condition comparisons

- --filter-D-min FLOAT (default: 0.001)
- --filter-D-max FLOAT (default: 2.0)
- --filter-alpha-min FLOAT (default: 0.0)
- --filter-alpha-max FLOAT (default: 2.0)
These bounds are applied when the script aggregates replicate results per condition
and when it generates comparison plots across conditions.

## Step-size analysis (optional)

- --step-size-analysis — After MSD fits, export step sizes per group/lag and run KDE plots
  and KS tests (if ≥2 groups present).

## Outputs (what runs/appears)

- Per-replicate: MSD fits, D/α CSV, histogram & scatter plots (+ optional rainbow overlay).
- Post-processing: per-condition grouped raw and grouped filtered ensembles + plots; comparison
  folder with histograms and a boxplot with significance annotations.

## Minimal examples

# 1) Fast default run on all Traj_*.csv in a folder
python GEMspa-CLI.py -d /data/spa_runs

# 2) Controlled parallelism on a 16-core machine
python GEMspa-CLI.py -d /data/spa_runs -j 4 --threads-per-rep 4

# 3) Custom pixel size & timestep + rainbow overlays
python GEMspa-CLI.py -d /data/spa_runs --micron-per-px 0.108 --time-step 0.05   --rainbow-tracks --img-prefix MAX_ --rainbow-min-D 0.001 --rainbow-max-D 1.5

# 4) Tight filtering + step-size analysis
python GEMspa-CLI.py -d /data/spa_runs --filter-D-min 0.005 --filter-D-max 1.0   --filter-alpha-min 0.7 --filter-alpha-max 1.3 --step-size-analysis

## Notes for your README

- Input CSVs must contain columns: track_id, frame, x, y (tabs or commas are OK).
- The Python API exposes the same functionality via modules such as trajectory_analysis
  and ensemble_analysis, so you can include Python usage examples alongside the CLI docs.

## Outputs & Interpretation

---------------------------
- msd_results.csv: per-track diffusion (D), anomalous exponent (α), fit quality (R²).
- D_fit_distribution.png: shows spread of diffusion coefficients on log scale.
- alpha_vs_logD.png: relation between α and D across tracks.
- rainbow_tracks.png: raw image with tracks color-coded by D.
- all_data_step_sizes.txt: long-form step-size data (group, tlag, step_size).
- step_kde_<group>.png: KDE curves of step sizes per tlag, log‐y.
- ks_volcano_*.png: p-value vs. tlag comparison between two groups.
- grouped_raw/msd_results.csv & plots: pooled per-condition before filtering.
- grouped_filtered/msd_results.csv & plots: pooled per-condition within filter bounds.
- ensemble_filtered_D_histograms.png & ensemble_filtered_alpha_histograms.png: overlaid histograms comparing conditions.
- replicate_median_D_boxplot.png: boxplot of median D per replicate with significance.

## Script Components

--------------------
2.1 trajectory_analysis.py
- Per-replicate MSD and diffusion coefficient analysis:
  - Reads a Traj_<condition>_<rep>.csv file containing tracked x,y coordinates and frame numbers.
  - Computes mean-squared displacement (MSD) per track (Numba JIT accelerated) and fits to MSD = 4·D·t^α.
  - Saves msd_results.csv with columns: track_id, condition, D_fit, alpha_fit, r2_fit.
  - Plots:
    • D_fit_distribution.png: log‑spaced histogram of D (μm²/s).
    • alpha_vs_logD.png: scatter of α vs. log10(D).
  - Optionally overlays colored tracks on the MAX_*.tif image using a rainbow colormap.

2.2 msd_diffusion.py
- Core MSD computation and fitting utilities:
  - _msd2d_jit: fast Numba‐parallel function computing 2D MSD up to max lag.
  - fit_msd: non‐linear least squares (SciPy) to fit MSD to power-law, returns D, α, R².
  - fit_msd_linear: fallback linear fit for purely diffusive tracks.
- Step‐size export:
  - set_track_data and step_sizes_and_angles compute step‐size matrices and angles.
  - save_step_sizes writes a “long” table with tlag & step_size columns.

2.3 rainbow_tracks.py
- Overlay raw tracks on background TIFF images, color‐coded by diffusion coefficient:
  - Reads MAX_<condition>_<rep>.tif, converts to RGB canvas.
  - Normalizes each track’s D_fit to [min_D, max_D], maps to specified colormap.
  - Draws line segments for each track on the image, saves high-resolution PNG.

2.4 step_size_analysis.py
- Per-replicate and per-ensemble step-size analysis:
  - Expects all_data_step_sizes.txt with columns [group, tlag, step_size].
  - For each group and each tlag, plots log‑scale KDE of step_size:
    • step_kde_<group>.png (fade by tlag, inset α₂ parameter).
  - If two groups present, computes KS test per tlag and plots volcano plot:
    • ks_volcano_<group1>_vs_<group2>.png

2.5 ensemble_analysis.py
- Pools replicate msd_results.csv by condition and applies filtering:
  - Groups folders named <condition>_<rep> and concatenates their msd_results.csv.
  - Writes grouped_raw/msd_results.csv and grouped_filtered/msd_results.csv.
  - Generates the same distribution & scatter plots for raw and filtered ensembles.

2.6 compare_conditions.py
- Cross-condition comparison on filtered ensemble data:
  - Overlaid, density-normalized histograms of D_fit on log x-axis with mean lines and KS-test asterisks.
  - Overlaid, density-normalized histograms of α_fit on linear x-axis with mean lines and KS-test asterisks.
  - Boxplot of replicate median D_fit with jittered points and Mann–Whitney U (or KS) test asterisk.

2.7 GEMspa-CLI.py
- Command-line entry point gluing everything together:
  - Discovers Traj_*.csv in --work-dir; processes each in parallel (--n-jobs).
  - Runs trajectory_analysis, exports step sizes, runs step_size_analysis if requested.
  - After replicates, runs ensemble_analysis and compare_conditions.
  - Arguments control filtering, rainbow parameters, and parallelism.
