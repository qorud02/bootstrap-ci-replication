"""Generate the article, figures and comparison ledger from saved results."""
from pathlib import Path
import argparse
import csv
import json
import os
import sys

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--dependencies', help='Optional local dependency directory')
args = parser.parse_args()
if args.dependencies:
    os.environ['BOOTSTRAP_REPLICATION_DEPS'] = args.dependencies
if (ROOT/'_deps').exists():
    sys.path.insert(0,str(ROOT/'_deps'))
if os.environ.get('BOOTSTRAP_REPLICATION_DEPS'):
    sys.path.insert(0,os.environ['BOOTSTRAP_REPLICATION_DEPS'])
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

rows = list(csv.DictReader((ROOT/'coverage.csv').open(encoding='utf-8')))
for row in rows:
    for key in ['n','outer','bootstrap_resamples']:
        row[key] = int(row[key])
    for key in ['miss_probability','monte_carlo_se','ci95_low','ci95_high']:
        row[key] = float(row[key])
main = [r for r in rows if r['experiment']=='main']
methods = ['t','tSkew','tBoot','percentile','reverse','expanded','bootT']
saved_weights = np.load(ROOT/'conditional_miss_samples.npz')
artifact_checks=[]
for population in ['normal','exponential']:
    for n in [10,20,40]:
        values=saved_weights[f'{population}_{n}']
        assert values.shape == (5000,7,2)
        assert np.all(np.isfinite(values)) and np.all((values>=0)&(values<=1))
        assert np.all(values.sum(axis=2)<=1+1e-12)
        for j,method in enumerate(methods):
            for k,side in enumerate(['left','right']):
                observed=next(r for r in main if r['population']==population and r['n']==n and r['method']==method and r['side']==side)
                assert abs(float(values[:,j,k].mean())-observed['miss_probability'])<1e-14
        artifact_checks.append(dict(population=population,n=n,finite_bounded_disjoint_weights=True,csv_matches_archive=True))
for n in [10,40]:
    for b in [1999,9999]:
        values=saved_weights[f'finite_B_exponential_{n}_B{b}']
        assert values.shape == (1500,7,2)
        assert np.all(np.isfinite(values)) and np.all((values>=0)&(values<=1))
        assert np.all(values.sum(axis=2)<=1+1e-12)
        for j,method in enumerate(methods):
            for k,side in enumerate(['left','right']):
                observed=next(r for r in rows if r['experiment']=='finite_B' and r['n']==n and r['bootstrap_resamples']==b and r['method']==method and r['side']==side)
                assert abs(float(values[:,j,k].mean())-observed['miss_probability'])<1e-14
        artifact_checks.append(dict(population='exponential',n=n,bootstrap_resamples=b,finite_bounded_disjoint_weights=True,csv_matches_archive=True))
(ROOT/'result_integrity.json').write_text(json.dumps(artifact_checks,indent=2),encoding='utf-8')
palette = dict(zip(methods,['#17375e','#773f89','#818898','#d67b18','#bd4c4e','#268a7e','#226aa5']))
labels = dict(t='Student t',tSkew='Skew-corrected t',tBoot='t with bootstrap SE',
              percentile='Percentile',reverse='Reverse percentile',expanded='Expanded percentile',bootT='Bootstrap t')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                     'axes.spines.right':False,'figure.dpi':150,'savefig.dpi':220})

fig, axes = plt.subplots(2,2,figsize=(11,7.2),sharex=True)
for i,pop in enumerate(['normal','exponential']):
    for j,side in enumerate(['left','right']):
        ax = axes[i,j]
        for method in methods:
            rr = sorted([r for r in main if r['population']==pop and r['side']==side and r['method']==method],key=lambda r:r['n'])
            p = np.array([r['miss_probability'] for r in rr])
            err = np.array([r['ci95_high']-r['miss_probability'] for r in rr])
            ax.errorbar([r['n'] for r in rr],p,yerr=err,label=labels[method],color=palette[method],marker='o',capsize=2,linewidth=1.5,markersize=4)
        ax.axhline(.025,color='#222222',linestyle='--',linewidth=1)
        ax.set_title(f'{pop.title()} population · {side} miss')
        ax.set_xticks([10,20,40])
        ax.set_ylabel('One-sided miss probability')
        ax.set_ylim((.022,.051) if pop=='normal' else ((0,.03) if side=='left' else (0,.16)))
        ax.grid(alpha=.17)
        if i==1:
            ax.set_xlabel('Sample size n')
fig.suptitle('Independent replication of confidence-interval calibration',fontsize=15,y=.99)
handles,ll = axes[0,0].get_legend_handles_labels()
fig.legend(handles,ll,loc='lower center',ncol=4,frameon=False,bbox_to_anchor=(.5,-.02))
fig.tight_layout(rect=[0,.08,1,.95])
fig.savefig(ROOT/'coverage_replication.png',bbox_inches='tight')
fig.savefig(ROOT/'coverage_replication.pdf',bbox_inches='tight')
plt.close(fig)

paired=list(csv.DictReader((ROOT/'paired_comparisons.csv').open(encoding='utf-8')))
fig,axes=plt.subplots(1,2,figsize=(10,4),sharey=True)
for ax,n in zip(axes,[10,40]):
    for j,method in enumerate(methods):
        row=next(r for r in paired if int(r['n'])==n and r['comparison']==f'{method}_B9999_minus_B1999' and r['side']=='right')
        difference=float(row['mean_difference'])
        ax.errorbar(j,difference,yerr=float(row['ci95_high'])-difference,fmt='o',capsize=4,
                    color=palette[method],markersize=5)
    ax.axhline(0,color='#222222',ls='--',lw=1)
    ax.set_title(f'Exponential · n={n}')
    ax.set_xticks(range(len(methods)),methods,rotation=40,ha='right')
    if n==10:
        ax.set_ylabel('Change in right miss probability')
    ax.grid(alpha=.17)
fig.suptitle('Finite-resample sensitivity · B=1,999 to 9,999 · 1,500 paired samples',fontsize=12)
fig.tight_layout()
fig.savefig(ROOT/'finite_B_sensitivity.png',bbox_inches='tight')
fig.savefig(ROOT/'finite_B_sensitivity.pdf',bbox_inches='tight')
plt.close(fig)

def get(pop,n,method,side):
    return next(r for r in main if r['population']==pop and r['n']==n and r['method']==method and r['side']==side)

def error(pop,n,method):
    return sum(abs(get(pop,n,method,s)['miss_probability']-.025) for s in ['left','right'])

comparison=[]
for n in [10,20,40]:
    for method in ['t','bootT']:
        for side in ['left','right']:
            r=get('normal',n,method,side)
            comparison.append(dict(source='Exact normal Student t probability' if method=='t' else 'Nominal one-sided calibration target',population='normal',n=n,method=method,
                side=side,target_type='exact_probability' if method=='t' else 'nominal_probability',source_target=.025,our_estimate=r['miss_probability'],
                mc_ci_low=r['ci95_low'],mc_ci_high=r['ci95_high'],status='target_in_95_mc_interval' if r['ci95_low']<=.025<=r['ci95_high'] else 'target_outside_95_mc_interval'))
    ranking=sorted(methods,key=lambda m:error('exponential',n,m))
    comparison.append(dict(source='Journal Fig10 and extended Fig21 qualitative conclusion',population='exponential',n=n,
        method='bootT',side='both',target_type='qualitative_rank',source_target='bootstrap t best overall coverage accuracy',
        our_estimate=ranking.index('bootT')+1,mc_ci_low='',mc_ci_high='',
        status='point_estimate_agrees' if ranking[0]=='bootT' else 'point_estimate_differs'))
with (ROOT/'original_results_comparison.csv').open('w',newline='',encoding='utf-8') as f:
    writer=csv.DictWriter(f,fieldnames=list(comparison[0]));writer.writeheader();writer.writerows(comparison)

metadata=json.loads((ROOT/'run_metadata.json').read_text(encoding='utf-8'))
sensitivity=[r for r in paired if '_B' in r['comparison']]
largest=max(sensitivity,key=lambda r:abs(float(r['mean_difference'])))
degenerate=sum(int(d['degenerate_bootstrap_resamples']) for c in metadata['cases'] for d in c['diagnostics'].values())
flattened=sum(int(d['skew_quadratic_flattened_samples']) for c in metadata['cases'] for d in c['diagnostics'].values())
table_lines=['| n | Method | Left miss | Right miss | Coverage | MC SE, left | MC SE, right |',
             '|---:|---|---:|---:|---:|---:|---:|']
for n in [10,20,40]:
    for m in methods:
        left,right=get('exponential',n,m,'left'),get('exponential',n,m,'right')
        table_lines.append(f"| {n} | {labels[m]} | {left['miss_probability']:.4f} | {right['miss_probability']:.4f} | {1-left['miss_probability']-right['miss_probability']:.4f} | {left['monte_carlo_se']:.5f} | {right['monte_carlo_se']:.5f} |")
rank_lines=[]
for n in [10,20,40]:
    rank=sorted(methods,key=lambda m:error('exponential',n,m))
    rank_lines.append(f"At n={n}, {labels[rank[0]]} has the smallest point-estimated sum of absolute one-sided calibration errors ({error('exponential',n,rank[0]):.4f}).")
anchor=list(csv.DictReader((ROOT/'table5_comparison.csv').open(encoding='utf-8')))
passed=sum(r['agrees_at_printed_precision']=='True' for r in anchor)
paper=r'''---
title: 'An independent replication of bootstrap confidence-interval calibration for small samples'
authors:
  - name: Kyunghan Bae
    affiliation: 1
affiliations:
  - name: Independent researcher, South Korea
    index: 1
date: 11 October 2026
bibliography: paper.bib
---

# Abstract

We independently implement seven confidence-interval procedures from
Hesterberg's study of resampling inference. All 20 printed numerical cells of
Table 5 in the extended manuscript agree with direct calculations at the
published precision. A fixed-seed experiment evaluates normal and exponential
sample means at n=10,20,40, using 5,000 original samples and 1,999 bootstrap
resamples per condition. Conditioning on centered or normalized residuals
reduces outer simulation noise. The experiment compares one-sided miss
probabilities and their Monte Carlo uncertainty, and a paired experiment
checks sensitivity to 9,999 resamples. The replication concerns a prespecified
small-sample subset of the original study.

# Original study and target

Hesterberg (2015), Figure 10, compares one-sided miss probabilities for normal
and exponential populations. We independently implement its selected
small-sample conditions. The publicly accessible 2014 extended manuscript
provides detailed methods and exact numerical targets (Hesterberg, 2014,
2015). Table 5 and Figures 20–22 refer to that extended manuscript;
Figure 10 refers to the journal article. The exact anchor supplements the
simulation target. The interval algorithms are newly written from the equations.

# Methods

The sample mean is the parameter estimate. The seven intervals are Student
t, skewness-corrected t, t with bootstrap standard error, percentile, reverse
percentile, expanded percentile, and bootstrap t. Their endpoints are
implemented in `replicate.py`, directly from the manuscript definitions. All
variances used for Student standard errors have divisor n-1. Bootstrap
standard error uses the sample standard deviation of the B resampled means.
Empirical quantiles use linear interpolation (Hyndman–Fan type 7).

Write the sample mean as $\bar x$, its standard error as $h=s/\sqrt n$,
and $c=t_{n-1,0.975}$. For bootstrap means $\bar x_b^*$, let $Q_p$ denote
the empirical $p$ quantile, $h_B$ their sample standard deviation, and
$T_b^*=(\bar x_b^*-\bar x)/(s_b^*/\sqrt n)$. The intervals are:

| Procedure | Lower and upper endpoints |
|---|---|
| Student t | $\bar x\pm ch$ |
| t with bootstrap SE | $\bar x\pm ch_B$ |
| Percentile | $[Q_{0.025}(\bar x^*), Q_{0.975}(\bar x^*)]$ |
| Reverse percentile | $[2\bar x-Q_{0.975}(\bar x^*), 2\bar x-Q_{0.025}(\bar x^*)]$ |
| Expanded percentile | $[Q_{a_n}(\bar x^*), Q_{1-a_n}(\bar x^*)]$ |
| Bootstrap t | $[\bar x-Q_{0.975}(T^*)h,\bar x-Q_{0.025}(T^*)h]$ |

Here $a_n=\Phi(-c\sqrt{n/(n-1)})$. For the skewness-corrected t
interval define $g(q)=q+\kappa(1+2q^2)$ and
$\kappa=m_3/(6s^3\sqrt n)$, where $m_3=n^{-1}\sum_i(x_i-\bar x)^3$.
Its endpoints are $\bar x+h g(-c)$ and $\bar x+h g(c)$ after the
flattening rule below. If $\kappa>0$, arguments below $-1/(4\kappa)$
are set to that value; if $\kappa<0$, arguments above it are set to it.
The zero-skewness limit equals Student t.

The skewness correction uses $m_3/s^3$. Its quadratic is flattened at the
extremum when a nominal endpoint lies beyond it, specifying the source's
instruction explicitly. Constant resamples have undefined studentized
statistics; the implementation counts and excludes only those statistics
from bootstrap-t quantiles. It fails if fewer than 99% remain finite.

Two source populations are studied, N(0,1) and Exponential(mean=1). The six
main conditions each use 5,000 independently generated original samples and
B=1,999 resamples. The finite-B comparison uses 1,500 fresh exponential
samples at n=10 and n=40, with B=1,999 and B=9,999 sharing original samples and
the initial resample prefix. PCG64DXSM seeds are fixed before calculation.

Let a left miss mean $L>\mu$ and a right miss mean $U<\mu$.
For normal data, $\bar X$ is independent of $V=X-\bar X$, and the
intervals are translation equivariant. Conditional on $V$ and the resample
indices, $L=\bar X+L_V$ and $U=\bar X+U_V$. Since
$\bar X\sim N(0,1/n)$, the conditional probabilities are

$$p_L(V)=\Phi(\sqrt n L_V),\qquad p_R(V)=\Phi(-\sqrt n U_V).$$

For exponential data, $V=X/\bar X$ is independent of
$\bar X\sim\operatorname{Gamma}(\text{shape}=n,\text{scale}=1/n)$ and the intervals are positively
scale equivariant. Thus $L=\bar X L_V$ and $U=\bar X U_V$. If $G_n$
is the CDF of that gamma law, the conditional probabilities are

$$p_L(V)=1-G_n(1/L_V),\qquad p_R(V)=G_n(1/U_V),$$

when the corresponding residual endpoint is positive. For $L_V\le0$ the
left probability is zero; for $U_V\le0$ the right probability is one.
We average these conditional weights over independent residual vectors and
independently drawn resample indices. The law of total expectation gives
the same unconditional miss probability as binary simulation, while
conditioning removes the sample-mean component of Monte Carlo variance.

Reported Monte Carlo standard errors are the sample standard deviation of
the conditional weights divided by sqrt(R); pointwise 95% intervals use a
Student critical value with R-1 degrees of freedom. Paired B differences use
the standard error of within-sample differences and the normal critical
value 1.96. These intervals quantify
outer simulation uncertainty at the specified B. The separate paired
experiment assesses finite-B sensitivity. Prespecified sample sizes cover
three small-sample conditions.

For descriptive comparisons we use
$E=|p_L-0.025|+|p_R-0.025|$. This operationalizes the source's qualitative
statement about overall coverage accuracy; the source does not specify this
particular loss function. Individual tail estimates and their uncertainty
remain the primary simulation results.

# Results

'''
paper+=f'All {passed}/20 numerical targets in Table 5 agree at their printed precision. '
paper+='The full values and discrepancies are available in `table5_comparison.csv`.\n\n'
paper+=r'''For the deterministic anchor, let $d_n=\sqrt{(n-1)/n}$ and
$z=\Phi^{-1}(0.975)$. The four calculated quantities are $d_n$,
$z/c$, $1-F_{t_{n-1}}(zd_n)$, and $\Phi(-c/d_n)$, respectively.
The following table reports our calculations with more digits than the
source's three or four decimal places.

'''
paper+='| n | Narrowness | z/t | One-sided size | Adjusted alpha/2 |\n|---:|---:|---:|---:|---:|\n'
for n in [5,10,20,40,80]:
    vals=[float(r['calculated']) for r in anchor if int(r['n'])==n]
    paper+=f"| {n} | "+' | '.join(f'{v:.6f}' for v in vals)+' |\n'
paper+='\n'
paper+='The exponential experiment gives the following newly computed results. A nominal 95% interval has target left and right miss probabilities of 0.025 each.\n\n'
paper+='\n'.join(table_lines)+'\n\n'
paper+=' '.join(rank_lines)+'\n\n'
bt10=get('exponential',10,'bootT','right')
t10=get('exponential',10,'t','right')
bt_coverage10=1-sum(get('exponential',10,'bootT',s)['miss_probability'] for s in ['left','right'])
t_coverage10=1-sum(get('exponential',10,'t',s)['miss_probability'] for s in ['left','right'])
paper+=f"For exponential data at n=10, the bootstrap-t right miss probability is {bt10['miss_probability']:.4f} (95% Monte Carlo interval [{bt10['ci95_low']:.4f}, {bt10['ci95_high']:.4f}]), compared with {t10['miss_probability']:.4f} for Student t. Their total coverages are {bt_coverage10:.4f} and {t_coverage10:.4f}, respectively. Bootstrap t ranks first here while retaining appreciable right-tail error relative to the 0.025 target.\n\n"
paper+='For normal data, all three Student-t estimates have Monte Carlo intervals containing their exact one-sided probability of 0.025. Bootstrap-t miss estimates at n=20 and n=40 are slightly above the nominal target; their pointwise intervals and the percentile undercoverage are shown below and in the comparison ledger.\n\n'
paper+='![One-sided miss probabilities with pointwise 95% Monte Carlo intervals. All points are newly computed; the dashed line is 0.025. The exponential panels use different vertical ranges.](coverage_replication.png)\n\n'
paper+=f"The largest-magnitude finite-B point change is {float(largest['mean_difference']):+.5f} ({largest['comparison']}, n={largest['n']}, {largest['side']} tail; paired 95% Monte Carlo interval [{float(largest['ci95_low']):+.5f}, {float(largest['ci95_high']):+.5f}]). "
paper+='All paired differences are reported in `paired_comparisons.csv`.\n\n'
paper+='![Paired changes in right-tail miss probability from 1,999 to 9,999 resamples, with 95% Monte Carlo intervals. Original samples and initial resamples are shared; the dashed line is zero.](finite_B_sensitivity.png)\n\n'
paper+=f'The run recorded {degenerate} degenerate studentized resamples and {flattened} skewness-flattening events across the main and sensitivity calculations. The latter count includes the same sensitivity original samples once per B. The primary experiment took {metadata["elapsed_seconds"]:.1f} seconds.\n\n'
paper+='''# Interpretation and scope

The deterministic anchor is reproduced at source precision. The simulation
comparison provides independent small-sample evidence about the original
interval-calibration conclusions. The original curves are supplied as
figures without tabulated ordinates. `table5_comparison.csv` contains the
exact numerical anchor. `original_results_comparison.csv` distinguishes
theoretical Student-t probabilities, nominal calibration targets and
qualitative ranking checks. Point-estimate rankings are
descriptive, and the Monte Carlo intervals are pointwise.

We explicitly reduce R and B relative to the source and quantify both outer
uncertainty and finite-B sensitivity. The target is the selected small-sample
regime. The large-n cutoffs in extended Figure 22, second-order convergence
rates and dependent, discrete or heavy-tailed populations require separate
experiments. The conditioning argument uses the stated normal and exponential
distributional assumptions.

# Reproducibility

Python 3.12 and the pinned requirements suffice. `python run_all.py` generates
all numerical results; `python analyze.py` creates this article and figures.
The numeric source trace, seeds, versions, per-condition timings and failure
counts are supplied. All main and finite-B conditional weights are archived in
`conditional_miss_samples.npz`, allowing independent reanalysis. The source
paper and figures are linked in `SOURCE_TRACE.md`. All observations are
generated from the stated probability distributions.

# References

Hesterberg, T. C. (2015). What Teachers Should Know About the Bootstrap:
Resampling in the Undergraduate Statistics Curriculum. *The American
Statistician*, 69(4), 371–386.
[doi:10.1080/00031305.2015.1089789](https://doi.org/10.1080/00031305.2015.1089789).

Hesterberg, T. (2014). What Teachers Should Know about the Bootstrap:
Resampling in the Undergraduate Statistics Curriculum. Extended manuscript,
arXiv:1411.5279v1. [Version 1](https://arxiv.org/abs/1411.5279v1).
'''
paper=paper.replace('The replication concerns a prespecified\nsmall-sample subset of the original study.',
    f'For exponential data at n=10, bootstrap-t coverage is {bt_coverage10:.4f}, compared with {t_coverage10:.4f} for Student t. '
    f'The largest-magnitude finite-B tail-probability change is {float(largest["mean_difference"]):+.5f}. '
    'The replication concerns a prespecified small-sample subset of the original study.')
(ROOT/'paper.md').write_text(paper,encoding='utf-8')
summary=dict(anchor_cells_passed=passed,rankings={str(n):sorted(methods,key=lambda m:error('exponential',n,m)) for n in [10,20,40]},
             largest_finite_B_change=largest,degenerate_bootstrap_resamples=degenerate,
             elapsed_seconds=metadata['elapsed_seconds'],figure_files=['coverage_replication.png','finite_B_sensitivity.png'],
             exponential_n10_coverage=dict(Student_t=t_coverage10,bootstrap_t=bt_coverage10),
             source_subset='2015 journal Figure10 normal/exponential n10/20/40 + 2014 extended Table5',
             independent_original_samples=33000,
             software=dict(numpy=np.__version__,scipy=metadata['scipy'],matplotlib=matplotlib.__version__))
(ROOT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
