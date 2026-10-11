# Source and protocol trace

The simulation target is the selected small-sample conditions in Figure 10
of Tim Hesterberg's journal article, *The American Statistician* 69(4),
371–386 (2015),
DOI [10.1080/00031305.2015.1089789](https://doi.org/10.1080/00031305.2015.1089789).
The detailed methods and exact numerical anchor come from its 2014 extended
manuscript, arXiv:1411.5279v1, Table 5 and Figures 20–22. The journal's Figure
10 consolidates the normal and exponential one-sided miss-probability plots.
Table 5 and Figures 20–22 in this package refer to the 83-page extended
manuscript; Figure 10 refers to the 16-page journal article.

Primary sources inspected on 2026-10-11:

- [Extended manuscript, HTML](https://arxiv.org/html/1411.5279v1)
- [Extended manuscript, PDF](https://arxiv.org/pdf/1411.5279v1)
- [Author's source page](https://www.timhesterberg.net/bootstrap-and-resampling)
- [Journal article in PubMed](https://pubmed.ncbi.nlm.nih.gov/27019512/), Figure 10 caption
- [Journal article in PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC4784504/), Appendix simulation details

The journal Figure 10 caption and appendix were available in the primary
PubMed/PMC search index. Direct full-page access returned a browser check;
the complete interval definitions were therefore read in the linked
extended manuscript. Both versions specify R=10,000 and B=10,000 for these
simulation plots and describe conditioning variance reduction.

The source's Table 5 supplies five sample sizes (5, 10, 20, 40, 80) and four
rounded numerical quantities. `table5_comparison.csv` contains all 20 source
numbers beside our independently calculated values.

Source §1.1 defines the intervals and the sample-variance divisor. Sections
5.3–5.5 give the expanded, reverse-percentile and studentized intervals.
Sections 5.6–5.6.2 supply the experiment, conditioning method and skewness
estimate. The confidence level is 95%; each one-sided target is 0.025.

The source describes bootstrap t as best overall for exponential data and
skewness-adjusted t as next best. Our descriptive ranking uses the sum of
absolute deviations of the two miss probabilities from 0.025. That loss
function is our explicit operationalization of the qualitative statement,
not a quoted or tabulated metric from the source.

## This implementation's choices

We use three prespecified sample sizes, n=10,20,40, and both source populations:
N(0,1) and Exponential(mean=1). Location and scale equivariance makes these
normalizations sufficient. All seven source interval families are included.

The primary experiment uses 5,000 independent original samples per condition
and 1,999 resamples per sample, with fixed PCG64DXSM seeds. The source used
10,000 original samples and 10,000 resamples (5,000 original samples for its
largest n). We replicate its conditioning estimator to reduce outer Monte
Carlo noise. We do not claim reproduction of the full original curves or of
the large-n thresholds in Figure 22.

The finite-B experiment uses 1,500 exponential samples at n=10 and n=40,
each with both B=1,999 and B=9,999. Original samples and the first 1,999
resamples are shared, so the B difference has a paired Monte Carlo interval.
This measures a computational sensitivity separately from outer simulation
uncertainty. Seeds, timings and degenerate-resample counts are logged.

NumPy's linear quantile interpolation (Hyndman–Fan type 7) is explicit.
The skewness estimate is m3/s^3, with m3 divided by n and s^2 by n-1. Following
§5.6.2, the quadratic correction is flattened at its extremum when necessary;
the code defines that boundary precisely. Constant bootstrap resamples have
undefined studentized statistics. We exclude them from that empirical
studentized distribution, count them, and fail the run if fewer than 99% of
resamples remain finite. Other intervals retain every resample.

The original author's scripts are not used. The public code only calls NumPy
for arrays and RNG and SciPy for elementary distribution functions.

## Licensing

The arXiv manuscript displays the arXiv perpetual non-exclusive license;
that is not an open redistribution license for this project. We link to the
manuscript and do not bundle its PDF, figures or original scripts. The 20
numerical target facts are transcribed for explicit comparison. All simulated
samples and figures in this package are newly generated. The new code can
be distributed under MIT and the new article under CC BY 4.0.

## Independence and venue check

Kyunghan Bae is not listed among the original paper's authors. We have no
evidence of a close collaboration with the original author; the submitter
must confirm that relationship statement personally at submission time.

Searches of the ReScience publication site and GitHub review repositories
for Hesterberg, the exact paper title and arXiv ID found no matching published
replication. This is a bounded duplicate check, not proof that none exists.
Broader educational bootstrap implementations exist and are not treated as
our own contribution.

ReScience C's official [submission instructions](https://rescience.github.io/write/)
require original source code and substantial agreement analysis. The official
[submission repository](https://github.com/ReScience/submissions) requests
public PDF, YAML metadata and code URLs before opening a submission issue.
The [secondary documentation](https://resciencec.readthedocs.io/en/latest/submitting.html)
also excludes trivial execution reports. Its [FAQ](https://rescience.github.io/faq/)
excludes replicating one's own or close collaborators' work, and warns that
already published replications may be rejected. The inspected author
guidelines and FAQ contain no explicit generative-AI provision. We do not
infer blanket permission from that absence. Public posting, submission and
peer review have not occurred as part of this local experiment.
