"""Run the benchmark for audiowmark (kept so the commands in README and docs still work).

Same as `python -m scripts.run_benchmark --method audiowmark ...`; all options are described there.

    python -m scripts.run_audiowmark --wav-dir data/wav --out results/results_audiowmark.csv
"""

import sys

from scripts.run_benchmark import main

if __name__ == "__main__":
    main(["--method", "audiowmark", *sys.argv[1:]])
