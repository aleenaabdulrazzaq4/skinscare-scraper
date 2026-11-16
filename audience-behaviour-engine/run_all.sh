#!/usr/bin/env bash
# Rebuild everything (about 1 minute). Then start the web app with:  python app/app.py
set -e
cd "$(dirname "$0")/src"
python3 simulate_data.py --posts 3000 --out ../data      # simulated posts, comments and hidden truth
python3 build_results.py                                  # fit model, run 5 analyses, validate, save results
python3 export_static.py                                  # dashboard.html (no server needed)
python3 charts.py                                         # report figures
