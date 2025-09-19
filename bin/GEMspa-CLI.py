#!/usr/bin/env python3
# bin/GEMspa-CLI.py

import argparse
import os
import glob
import re
from functools import partial
from multiprocessing import Pool, cpu_count

from gemspa.trajectory_analysis import trajectory_analysis
from gemspa.step_size_analysis import run_step_size_analysis_if_requested
from gemspa.ensemble_analysis import run_ensemble
from gemspa.compare_conditions import compare_conditions

def process_movie(args, csv_file):
    base = os.path.basename(csv_file)
    name, _ = os.path.splitext(base)
    replicate = name.replace('Traj_', '')
    cond = re.sub(r'_[0-9]+$', '', replicate)

    result_dir = os.path.join(args.work_dir, replicate)
    os.makedirs(result_dir, exist_ok=True)

    # compute threads per replicate
    if args.threads_per_rep:
        tpr = args.threads_per_rep
    else:
        tpr = max(1, cpu_count() // max(1, args.n_jobs))

    traj = trajectory_analysis(
        data_file=csv_file,
        results_dir=result_dir,
        condition=cond,
        time_step=args.time_step,
        micron_per_px=args.micron_per_px,
        ts_resolution=args.ts_resolution,
        min_track_len_linfit=args.min_track_len,
        tlag_cutoff_linfit=args.tlag_cutoff,
        make_rainbow_tracks=args.rainbow_tracks,
        img_file_prefix=args.img_prefix,
        rainbow_min_D=args.rainbow_min_D,
        rainbow_max_D=args.rainbow_max_D,
        rainbow_colormap=args.rainbow_colormap,
        rainbow_scale=args.rainbow_scale,
        rainbow_dpi=args.rainbow_dpi,
        n_jobs=args.n_jobs,
        threads_per_rep=tpr
    )

    traj.write_params_to_log_file()
    traj.calculate_msd_and_diffusion()

    if args.step_size_analysis:
        traj.export_step_sizes()
        run_step_size_analysis_if_requested(result_dir)

def main():
    parser = argparse.ArgumentParser(
        description="GEMspa Single-Particle Tracking Analysis CLI"
    )
    parser.add_argument("-d","--work-dir", required=True,
                        help="Directory with Traj_*.csv files")
    parser.add_argument("-j","--n-jobs", type=int, default=cpu_count(),
                        help="Parallel processes (across replicates)")
    parser.add_argument("--threads-per-rep", type=int, default=None,
                        help="Threads per replicate (default=cores/n-jobs)")
    parser.add_argument("--time-step", type=float, default=0.010)
    parser.add_argument("--micron-per-px", type=float, default=0.11)
    parser.add_argument("--ts-resolution", type=float, default=0.005)
    parser.add_argument("--min-track-len", type=int, default=11)
    parser.add_argument("--tlag-cutoff", type=int, default=10)
    parser.add_argument("--rainbow-tracks", action="store_true")
    parser.add_argument("--img-prefix", default="MAX_")
    parser.add_argument("--rainbow-min-D", type=float, default=0.0)
    parser.add_argument("--rainbow-max-D", type=float, default=2.0)
    parser.add_argument("--rainbow-colormap", default="viridis")
    parser.add_argument("--rainbow-scale", type=float, default=1.0)
    parser.add_argument("--rainbow-dpi", type=int, default=200)
    parser.add_argument("--filter-D-min", type=float, default=0.001)
    parser.add_argument("--filter-D-max", type=float, default=2.0)
    parser.add_argument("--filter-alpha-min", type=float, default=0.0)
    parser.add_argument("--filter-alpha-max", type=float, default=2.0)
    parser.add_argument("--step-size-analysis", action="store_true",
                        help="Also run the step-size KDE & KS analysis")
    args = parser.parse_args()

    all_csv = glob.glob(os.path.join(args.work_dir, "Traj_*.csv"))
    csvs = [f for f in all_csv if os.path.getsize(f) > 0]
    if not csvs:
        parser.exit(message=f"No Traj_*.csv files in {args.work_dir}\n")

    if args.n_jobs > 1:
        with Pool(args.n_jobs) as pool:
            pool.map(partial(process_movie, args), csvs)
    else:
        for f in csvs:
            process_movie(args, f)

    run_ensemble(
        args.work_dir,
        filter_D_min=args.filter_D_min,
        filter_D_max=args.filter_D_max,
        filter_alpha_min=args.filter_alpha_min,
        filter_alpha_max=args.filter_alpha_max
    )
    compare_conditions(
        args.work_dir,
        filter_D_min=args.filter_D_min,
        filter_D_max=args.filter_D_max,
        filter_alpha_min=args.filter_alpha_min,
        filter_alpha_max=args.filter_alpha_max
    )

if __name__ == "__main__":
    main()
