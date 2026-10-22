"""Run the benchmark for audioseal (kept so the commands in README and docs still work).

Same as `python -m scripts.run_benchmark --method audioseal ...`; all options are described there.

    python -m scripts.run_audioseal --wav-dir data/wav --out results/results_audioseal.csv
"""

import sys

from scripts.run_benchmark import main

if __name__ == "__main__":
    main(["--method", "audioseal", *sys.argv[1:]])
