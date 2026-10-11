# Independent review of the bootstrap replication

Current status: final numerical and manuscript review PASS. All 140 coverage rows and 88 paired-comparison rows were independently recomputed from archived raw weights. Later addenda below supersede earlier pending items.

Reviewed 2026-10-11. Files: replicate.py, run_all.py, SOURCE_TRACE.md. This review changed none of the research implementation or experiment outputs. Numerical checks ran in memory with bytecode writes disabled.

## Decision

No blocking mathematical error was found in the seven interval algorithms, the Table 5 calculations, or the normal/exponential conditioning estimator. This is a selective computational replication, with a smaller resampling budget, rather than a reproduction of the complete paper. The main experiment was still running at review time; this review does not certify the eventual numerical results, plots, manuscript, or complete environment replay.

## Source match

The [2014 extended manuscript](https://arxiv.org/html/1411.5279v1), sections 1.1 and 5.3–5.6.2, defines the seven interval families and conditioning estimator. Table 5 supplies the 20 rounded targets. Its source simulation used 10,000 outer samples and 10,000 resamples, with 5,000 outer samples at n ≥ 6000. The [2015 journal article record](https://pubmed.ncbi.nlm.nih.gov/27019512/) identifies Figure 10 as the normal/exponential one-sided-miss comparison. The journal's [archived primary article](https://pmc.ncbi.nlm.nih.gov/articles/PMC4784504/) search index confirms the same simulation appendix. Publisher access returned HTTP 403 and the PMC page showed a browser check, so the extended manuscript was the directly readable source for implementation details.

## Implementation audit

- replicate.py 39–64: the Table 5 anchor uses the appropriate sample-variance shrinkage, z/t ratio, one-sided t tail and adjusted normal quantile. All 20 source values are hard-coded next to calculated values, with tolerance equal to half the published final decimal unit. These are agreement checks on published numerical facts, not a new mathematical result.
- replicate.py 67–113: ordinary t uses sample SD with divisor n−1. tBoot uses the SD of bootstrap means with divisor B−1 and a t critical value. Percentile/reverse/expanded endpoints use the correct quantiles and reversal. Bootstrap-t correctly exchanges the upper/lower studentized quantiles. The skewness estimate uses central third moment divided by n and sample SD cubed. Its correction is clamped at the quadratic extremum; the choice is explicit and monotone.
- replicate.py 117–137: normal tails condition on centered residuals. Exponential tails condition on the normalized sample and integrate the independent Gamma(n, scale=1/n) mean. Nonpositive endpoint-ratio branches are correct. left means L > mu and right means U < mu; this matches the source's direction in which the interval misses the parameter.
- replicate.py 140–171: independently generated outer samples and resampling indices preserve the conditional argument. The finite-B comparison shares original samples and the smaller resample prefix, allowing paired uncertainty estimates.
- replicate.py 173 onward: standard errors use independent outer replicates. The reported intervals quantify Monte Carlo uncertainty in the specified finite-B algorithm, not uncertainty about a universal ranking of methods. A paired mean tail-probability difference is not a difference in squared calibration errors.
- run_all.py: returns the subprocess failure code and captures merged output. It currently executes the numerical experiment only; the final README must give the figure/manuscript-generation step separately, if applicable.

## Read-only numerical checks

Runtime: bundled Python, NumPy 2.3.5 and SciPy 1.15.3, using the executing experiment's supplied dependency directory. Independent test seed 54321.

| Check | Result |
| --- | ---: |
| Translation equivariance, all seven intervals, 32 samples, n=10, B=1000 | maximum error 2.665e−15 |
| Positive scale equivariance, same cases | maximum error 0 |
| Normal conditional probability vs 250,000 direct conditional draws | maximum difference 0.000764722 |
| Exponential conditional probability vs 250,000 direct conditional draws | maximum difference 0.000696902 |
| Normal t control, 100,000 independent samples at n=20 | mean one-sided miss 0.0250957833 |
| Normal t control Monte Carlo SE | 0.0000617478 |
| Studentized resamples in the equivariance check | 32,000 finite, 0 degenerate |

The exact normal t control is 1.55 Monte Carlo standard errors from 0.025. Explicit exponential cases with nonpositive lower/upper endpoints also passed. These checks independently exercise signs, normalization, scale/translation properties and the conditional probability calculation. They are not a second full run of the selected study.

## Corrections and remaining release checks

1. The paired-comparison comment originally referred to squared two-tail calibration error. The authoring agent corrected it to paired tail-probability differences after this review. Any prose using that output must retain the corrected interpretation.
2. SOURCE_TRACE originally used secondary readthedocs instructions as its venue authority. The authoring agent corrected it to the current official WRITE page and submission repository.
3. Link the selected experiment to journal Figure 10 explicitly, alongside the extended manuscript's Table 5 and Figures 20–22. The current n=10,20,40 experiment cannot verify the source's large-n thresholds or asymptotic-order claims.
4. Before release, inspect completed outputs and finite-B differences. B=1999 estimates tail quantiles less precisely than the source's B=10000; the paired sensitivity experiment should determine whether substantive small-sample conclusions persist. Report material differences directly.
5. The main numerical script and logs establish computations, not acceptance. Public repository, archival DOI, journal submission and peer review remain separate states. Add the new code and article licenses and replay from the documented environment before submission.

## Venue requirements checked

The [official ReScience C WRITE page](https://rescience.github.io/write/) requires rigorous methods, original code and substantial evidence of agreement or a documented failure. It excludes one's own or close collaborators' work. The [submission repository](https://github.com/ReScience/submissions) currently requests public PDF, YAML metadata and code URLs, then directs to a GitHub submission issue. Use that path rather than the secondary documentation's short-form link. The [FAQ](https://rescience.github.io/faq/) requires openly licensed code and warns that an already published replication may be rejected.

No explicit generative-AI disclosure requirement was found in those inspected pages or the [secondary author guidelines](https://resciencec.readthedocs.io/en/latest/submitting.html). This is a bounded policy check, not a claim that every editorial policy was exhausted. Keep discretionary mentions out of the title, abstract and results. If a submission field or editor requests a disclosure, answer accurately and briefly. Do not assert that the human author personally implemented or manually checked work that was performed by tools. The source-independence statement concerns independence from Hesterberg's implementation.

## Recommended description

Suggested title: **[Re] Selected small-sample confidence-interval experiments from Hesterberg (2015)**.

Suggested scope sentence: “We independently implement the confidence-interval comparison underlying Figure 10 of Hesterberg (2015), focusing on normal and exponential populations at n=10,20,40. We also check all 20 numerical entries of Table 5 in the 2014 extended manuscript and examine sensitivity to the number of bootstrap resamples.”

This accurately describes the current deliverable. Whether the selected experiment supplies substantial enough evidence for ReScience C remains an editorial decision. A source-versus-replication comparison table should distinguish exact rounded Table 5 agreement from qualitative agreement with the selected Figure 10 conclusions.


## Completed-experiment review addendum

The completed experiment and generated manuscript were reviewed after the initial report. The run finished in 731.5966 seconds. All six main conditions and both finite-B conditions completed. Completed artifacts inspected: coverage.csv, paired_comparisons.csv, conditional_miss_samples.npz, run_metadata.json, verification.json, result_integrity.json, original_results_comparison.csv, analyze.py, verify.py, paper.md, README.md and both PNG figures.

### Independent output recomputation

Using Python's statistics.fmean/stdev on the saved weights, rather than the summary generator's NumPy reductions, I recomputed all 84 main CSV means, MCSEs and pointwise 95% intervals. I also independently recomputed all 60 main paired method-comparison means, SEs and intervals.

| Output checked | Maximum absolute discrepancy |
| --- | ---: |
| Main estimated probabilities | 1.388e−17 |
| Main Monte Carlo SEs | 1.084e−19 |
| Main 95% Monte Carlo endpoints | 1.388e−17 |
| Main paired means | 1.388e−17 |
| Main paired SEs | 5.421e−20 |
| Main paired 95% endpoints | 1.388e−17 |

The 140 coverage rows consist of 84 main and 56 sensitivity rows. The 88 paired rows consist of 60 main and 28 finite-B comparisons. Every finite-B mean difference agrees with its two marginal coverage estimates; every paired interval equals mean ±1.96 SE; every paired SE satisfies the bounds imposed by its two marginal SEs. The largest-magnitude finite-B contrast is correctly identified: expanded, exponential n=10, right tail, −0.0008128425, interval [−0.001091629, −0.0005340563].

The archived NPZ currently contains only the six main weight arrays. Therefore the finite-B paired SEs cannot yet be independently recomputed from saved raw weights. The implementation of their calculation is correct on inspection. The authoring agent was asked to archive the two B-specific weight arrays for each sensitivity condition, which would close this replay gap without rerunning the main experiment. This status will be amended if the additional archive is supplied.

### Manuscript and interpretation

The manuscript now provides all seven interval definitions, including a separate explicit skewness formula and flattening rule. It correctly associates journal Figure 10 with the selected n=10,20,40 cases and extended Table 5 with the 20 deterministic anchors. The abstract and scope state the restricted experiment. The large-n thresholds, asymptotic convergence orders and other population families are excluded from the empirical conclusions.

The original-results ledger distinguishes the exact normal Student t benchmark from a nominal 0.025 bootstrap-t target. In particular, normal bootstrap-t estimates at n=20 and n=40 lie above the nominal target by more than their pointwise Monte Carlo uncertainty; this is recorded, rather than incorrectly claiming exact bootstrap-t calibration. All three normal Student t benchmark cases have 0.025 inside their pointwise intervals.

The exponential bootstrap-t ranking is expressly a point-estimate ranking under a newly specified sum of absolute one-sided errors. It is not presented as a simultaneous statistical superiority test. This appropriately limits the claim. Both figure images are readable, with axes, legends and uncertainty bars visible and no clipping found.

Three small wording corrections were sent to the authoring agent: label Gamma parameters explicitly as shape n and scale 1/n; replace “largest absolute change is −...” with “largest-magnitude change” or a positive magnitude; and distinguish table5_comparison.csv from original_results_comparison.csv, since the latter currently contains benchmark and qualitative-comparison rows rather than the Table 5 cells themselves. The README already describes the NPZ as main weights, while the manuscript's archive description should be equally precise until sensitivity weights are added.

### Final assessment

The numerical results and uncertainty calculations inspected here are internally consistent, and the manuscript's core mathematical definitions and partial-replication scope are sound. The remaining reproducibility improvement is archiving and checking sensitivity raw weights. There has been no second complete fresh-environment replay in this independent review and no external mathematical or journal review. No code, manuscript or research output was edited by this reviewer; only this report was updated.


## Closure after sensitivity archive and manuscript corrections

The authoring agent reran only the two recorded sensitivity conditions with their original seeds. Four additional weight arrays are now preserved in conditional_miss_samples.npz (10 arrays total). The rebuild log and metadata report 156.5042 seconds; recorded sensitivity means and SEs were unchanged. The fresh-run implementation now also saves these arrays.

I independently recomputed all 56 sensitivity means, MCSEs and 95% endpoints, plus all 28 finite-B paired means, SEs and 95% endpoints from these added raw weights. Maximum discrepancies were 2.776e−17 for marginal means/endpoints, 2.168e−19 for marginal MCSEs, 1.084e−19 for paired means/endpoints and 2.711e−20 for paired MCSEs. All passed the 1e−14 tolerance. Together with the earlier main checks, every coverage row (140) and every paired-comparison row (88) has now been independently checked against archived raw weights. The archive gap described above is closed.

The 21-row exponential results table was independently parsed from paper.md and compared with coverage.csv: left miss, right miss, coverage and both MCSE fields all match at their displayed precision. The manuscript corrections are present: explicit gamma shape/scale parameters; largest-magnitude signed contrast; separate Table 5 and benchmark-comparison files; all main and finite-B weights described accurately. Added abstract results agree with the checked table.

Final internal assessment: PASS for mathematical implementation, saved numerical summaries, reported Monte Carlo uncertainty, final manuscript's result transcription and bounded partial-replication claims. No unresolved numerical or scope blocker was found in this review. Acceptance, originality relative to every prior replication and a complete clean-environment replay remain outside the verified claims.
