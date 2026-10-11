# Bootstrap confidence-interval replication

This project independently implements the interval-calibration experiment
in Tim Hesterberg's 2014 extended manuscript and related 2015 article. It
compares seven methods using exactly specified normal and exponential
populations and newly written Python algorithms.

The numerical targets are all 20 printed cells of extended-manuscript
Table 5, plus selected small-sample conditions of journal Figure 10
(extended-manuscript Figures 20–21). The main
simulation uses n=10,20,40 with 5,000 original samples and 1,999 resamples
per sample. A paired sensitivity analysis increases B to 9,999 at two
prespecified exponential conditions.

## Run

Use Python 3.12 in a fresh virtual environment:

```text
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python verify.py
.venv\Scripts\python run_all.py
.venv\Scripts\python analyze.py
```

On Unix, substitute `.venv/bin/python`. The full numerical experiment takes
minutes in a single Python process; the actual measured duration and versions are in
`run_metadata.json`. `run_all.py --dependencies PATH` optionally loads an
isolated package directory; `verify.py` and `analyze.py` accept the same
option. The scripts also recognize `BOOTSTRAP_REPLICATION_DEPS`. No paid or
proprietary scientific software is needed.

## Read and inspect

- `Bootstrap_replication.pdf` / `.docx`: reading and editable document copies.
- `INDEPENDENT_REVIEW.md`: separate numerical and scope review.
- `paper.md` / `paper.bib`: article and references, generated from the results.
- `SOURCE_TRACE.md`: original source version, method choices and scope.
- `table5_comparison.csv`: original and independently calculated exact targets.
- `coverage.csv`: one-sided estimates, Monte Carlo SEs and 95% intervals.
- `paired_comparisons.csv`: paired method and finite-B differences.
- `original_results_comparison.csv`: comparison with explicit source targets.
- `coverage_replication.png` / `.pdf`: normal and exponential calibration.
- `finite_B_sensitivity.png` / `.pdf`: paired finite-resample experiment.
- `conditional_miss_samples.npz`: main and finite-B conditional weights for reanalysis.
- `save_sensitivity_weights.py`: reconstitutes the initially omitted finite-B archive from recorded seeds and verifies its agreement with the recorded results.
- `sensitivity_archive_execution.jsonl`, `sensitivity_archive_metadata.json`: archive reconstruction evidence.
- `result_integrity.json`: bounded weights and CSV/archive agreement checks.
- `execution.jsonl`, `run_metadata.json`, `verification.json`: execution evidence.

The full large-n curves of the original study are outside this experiment.
All generated figures are new calculations. The original article, figures
and scripts are linked rather than redistributed.

Code is MIT licensed; the newly written article and figures are CC BY 4.0.
The original numerical facts and mathematical formulas retain their proper
source attribution. This package contains no private or participant data.
