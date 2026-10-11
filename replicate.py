"""Independent implementation of Hesterberg's confidence-interval experiment.

Core interval algorithms are written here; no original author's code is used.
SciPy supplies distribution CDFs/quantiles, NumPy supplies array arithmetic/RNG.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parent
if (ROOT / '_deps').exists():
    sys.path.insert(0, str(ROOT / '_deps'))
if os.environ.get('BOOTSTRAP_REPLICATION_DEPS'):
    sys.path.insert(0, os.environ['BOOTSTRAP_REPLICATION_DEPS'])
import numpy as np
import scipy
from scipy import stats

METHODS = ['t', 'tSkew', 'tBoot', 'percentile', 'reverse', 'expanded', 'bootT']


def csv_write(name, rows):
    if not rows:
        return
    with (ROOT / name).open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def anchor_table():
    original = [
        (5, .894, .706, .077, .0010),
        (10, .949, .866, .048, .0086),
        (20, .975, .936, .036, .0159),
        (40, .987, .969, .030, .0203),
        (80, .994, .985, .028, .0226),
    ]
    rows = []
    z = stats.norm.ppf(.975)
    for n, *published in original:
        narrow = np.sqrt((n-1)/n)
        critical = stats.t.ppf(.975, n-1)
        calculated = [narrow, z/critical,
                      stats.t.sf(z*narrow, n-1),
                      stats.norm.cdf(-critical/narrow)]
        for label, ref, value, places in zip(
            ['narrowness', 'z_over_t', 'one_sided_size', 'adjusted_alpha_over_2'],
            published, calculated, [3, 3, 3, 4]
        ):
            agrees = abs(float(value)-ref) <= .5*10**(-places)+1e-12
            rows.append(dict(n=n, quantity=label, source_value=ref,
                             calculated=float(value), source_decimal_places=places,
                             difference=float(value)-ref, agrees_at_printed_precision=agrees))
    csv_write('table5_comparison.csv', rows)
    assert all(r['agrees_at_printed_precision'] for r in rows), rows
    return rows


def endpoints(x, resample_indices):
    """Return [replicate, method, low/high] and numerical diagnostics."""
    r, n = x.shape
    b = resample_indices.shape[1]
    mean = np.mean(x, axis=1)
    sd = np.std(x, axis=1, ddof=1)
    se = sd/np.sqrt(n)
    tc = stats.t.ppf(.975, n-1)
    skew = np.mean((x-mean[:, None])**3, axis=1)/sd**3
    kappa = skew/(6*np.sqrt(n))
    qlo, qhi = np.full(r, -tc), np.full(r, tc)
    # The source requests flattening beyond the quadratic's extremum.
    # These clamps specify that otherwise ambiguous instruction explicitly.
    positive, negative = kappa > 0, kappa < 0
    qlo[positive] = np.maximum(qlo[positive], -1/(4*kappa[positive]))
    qhi[negative] = np.minimum(qhi[negative], -1/(4*kappa[negative]))
    clipped = (qlo != -tc) | (qhi != tc)
    low_skew = mean + se*(qlo+kappa*(1+2*qlo*qlo))
    high_skew = mean + se*(qhi+kappa*(1+2*qhi*qhi))

    bs = np.take_along_axis(x[:, None, :], resample_indices, axis=2)
    boot_mean = np.mean(bs, axis=2)
    boot_se = np.std(bs, axis=2, ddof=1)/np.sqrt(n)
    degenerate = (np.max(bs, axis=2) == np.min(bs, axis=2)) | (boot_se <= 0) | ~np.isfinite(boot_se)
    if np.any(np.sum(~degenerate, axis=1) < max(100, .99*b)):
        raise RuntimeError('Too few finite studentized resamples; see numerical policy.')
    studentized = np.full_like(boot_mean, np.nan)
    np.divide(boot_mean-mean[:, None], boot_se, out=studentized, where=~degenerate)
    p025, p975 = np.quantile(boot_mean, [.025, .975], axis=1, method='linear')
    adjusted = stats.norm.cdf(-tc*np.sqrt(n/(n-1)))
    e_low, e_high = np.quantile(boot_mean, [adjusted, 1-adjusted], axis=1, method='linear')
    tq025, tq975 = np.nanquantile(studentized, [.025, .975], axis=1, method='linear')
    se_bootstrap = np.std(boot_mean, axis=1, ddof=1)
    result = np.stack([
        np.stack([mean-tc*se, mean+tc*se], axis=1),
        np.stack([low_skew, high_skew], axis=1),
        np.stack([mean-tc*se_bootstrap, mean+tc*se_bootstrap], axis=1),
        np.stack([p025, p975], axis=1),
        np.stack([2*mean-p975, 2*mean-p025], axis=1),
        np.stack([e_low, e_high], axis=1),
        np.stack([mean-tq975*se, mean-tq025*se], axis=1),
    ], axis=1)
    if not np.all(np.isfinite(result)) or np.any(result[:, :, 0] > result[:, :, 1]):
        raise RuntimeError('Non-finite or reversed confidence interval.')
    diag = dict(degenerate_bootstrap_resamples=int(degenerate.sum()),
                skew_quadratic_flattened_samples=int(clipped.sum()),
                total_bootstrap_resamples=int(r*b))
    return result, diag


def conditional_miss(x, intervals, population):
    n = x.shape[1]
    center = x.mean(axis=1)[:, None]
    low, high = intervals[:, :, 0], intervals[:, :, 1]
    if population == 'normal':
        # Xbar independent of centered residual vector; Xbar~N(0,1/n).
        right = stats.norm.cdf(-np.sqrt(n)*(high-center))
        left = stats.norm.cdf(np.sqrt(n)*(low-center))
        mu = 0
    else:
        # Xbar independent of X/Xbar; Xbar~Gamma(n, scale=1/n).
        low_v, high_v = low/center, high/center
        right = np.ones_like(high_v)
        left = np.zeros_like(low_v)
        pos_high, pos_low = high_v > 0, low_v > 0
        right[pos_high] = stats.gamma.cdf(1/high_v[pos_high], a=n, scale=1/n)
        left[pos_low] = stats.gamma.sf(1/low_v[pos_low], a=n, scale=1/n)
        mu = 1
    weighted = np.stack([left, right], axis=2)
    binary = np.stack([low > mu, high < mu], axis=2).astype(float)
    return weighted, binary


def run_case(population, n, outer, bootstrap_counts, seed, label):
    started = time.perf_counter()
    # Separate streams preserve samples and the resample prefixes in B sensitivity.
    sample_rng = np.random.Generator(np.random.PCG64DXSM(seed))
    boot_rng = np.random.Generator(np.random.PCG64DXSM(seed+1000003))
    x = (sample_rng.normal(size=(outer, n)) if population == 'normal'
         else sample_rng.exponential(size=(outer, n)))
    outputs = {b: dict(weighted=[], binary=[], diagnostics={
        'degenerate_bootstrap_resamples': 0, 'skew_quadratic_flattened_samples': 0,
        'total_bootstrap_resamples': 0}) for b in bootstrap_counts}
    max_b = max(bootstrap_counts)
    chunk = max(1, min(32, int(2_000_000/(max_b*n))))
    for start in range(0, outer, chunk):
        xx = x[start:start+chunk]
        indices = boot_rng.integers(n, size=(len(xx), max_b, n), dtype=np.int16)
        for b in bootstrap_counts:
            ci, diag = endpoints(xx, indices[:, :b])
            weighted, binary = conditional_miss(xx, ci, population)
            outputs[b]['weighted'].append(weighted)
            outputs[b]['binary'].append(binary)
            for key in diag:
                outputs[b]['diagnostics'][key] += diag[key]
        if start == 0 or start+chunk >= outer or (start//chunk) % 50 == 0:
            print(json.dumps(dict(event='progress', case=label, population=population,
                                  n=n, completed=min(start+chunk, outer), outer=outer,
                                  elapsed_seconds=round(time.perf_counter()-started, 3))), flush=True)
    for b, output in outputs.items():
        output['weighted'] = np.concatenate(output['weighted'])
        output['binary'] = np.concatenate(output['binary'])
    return outputs, dict(population=population, n=n, outer=outer, bootstrap_counts=bootstrap_counts,
                         seed=seed, label=label, elapsed_seconds=time.perf_counter()-started)


def summaries(population, n, outputs, outer, label):
    rows = []
    quantile = stats.t.ppf(.975, outer-1)
    for b, out in outputs.items():
        for j, method in enumerate(METHODS):
            for k, side in enumerate(['left', 'right']):
                w, raw = out['weighted'][:, j, k], out['binary'][:, j, k]
                p = np.mean(w)
                mcse = np.std(w, ddof=1)/np.sqrt(outer)
                raw_mcse = np.std(raw, ddof=1)/np.sqrt(outer)
                rows.append(dict(experiment=label, population=population, n=n, outer=outer,
                    bootstrap_resamples=b, method=method, side=side, miss_probability=p,
                    monte_carlo_se=mcse, ci95_low=max(0,p-quantile*mcse),
                    ci95_high=min(1,p+quantile*mcse), target=.025,
                    raw_miss_probability=np.mean(raw), raw_monte_carlo_se=raw_mcse,
                    conditioning_variance_reduction=(raw_mcse/mcse)**2 if mcse > 0 else float('inf')))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--outer', type=int, default=5000)
    parser.add_argument('--bootstrap', type=int, default=1999)
    parser.add_argument('--sensitivity-outer', type=int, default=1500)
    parser.add_argument('--sensitivity-bootstrap', type=int, default=9999)
    parser.add_argument('--seed', type=int, default=20261011)
    args = parser.parse_args()
    start = time.perf_counter()
    anchors = anchor_table()
    rows, metadata, paired = [], [], []
    all_arrays = {}
    for p_idx, population in enumerate(['normal', 'exponential']):
        for n in [10, 20, 40]:
            seed = args.seed+10000*p_idx+100*n
            outs, meta = run_case(population,n,args.outer,[args.bootstrap],seed,'main')
            rows.extend(summaries(population,n,outs,args.outer,'main'))
            meta['diagnostics'] = {b: v['diagnostics'] for b,v in outs.items()}
            metadata.append(meta)
            all_arrays[f'{population}_{n}'] = outs[args.bootstrap]['weighted']
            for method in ['t', 'tSkew', 'percentile', 'expanded', 'reverse']:
                j, bt = METHODS.index(method), METHODS.index('bootT')
                # Compare each tail's miss probability using the paired original samples.
                for side in [0,1]:
                    diff = outs[args.bootstrap]['weighted'][:,j,side]-outs[args.bootstrap]['weighted'][:,bt,side]
                    se = np.std(diff,ddof=1)/np.sqrt(args.outer)
                    d = diff.mean()
                    paired.append(dict(population=population,n=n,comparison=f'{method}_minus_bootT',
                        side=['left','right'][side],mean_difference=d,paired_mcse=se,
                        ci95_low=d-1.96*se,ci95_high=d+1.96*se))
    for n in [10, 40]:
        outs, meta = run_case('exponential',n,args.sensitivity_outer,
                    [args.bootstrap,args.sensitivity_bootstrap],args.seed+200000+100*n,'finite_B')
        rows.extend(summaries('exponential',n,outs,args.sensitivity_outer,'finite_B'))
        meta['diagnostics'] = {b: v['diagnostics'] for b,v in outs.items()}
        metadata.append(meta)
        for b,output in outs.items():
            all_arrays[f'finite_B_exponential_{n}_B{b}'] = output['weighted']
        for j,method in enumerate(METHODS):
            for k,side in enumerate(['left','right']):
                d = outs[args.sensitivity_bootstrap]['weighted'][:,j,k]-outs[args.bootstrap]['weighted'][:,j,k]
                se = np.std(d,ddof=1)/np.sqrt(args.sensitivity_outer)
                paired.append(dict(population='exponential',n=n,
                    comparison=f'{method}_B{args.sensitivity_bootstrap}_minus_B{args.bootstrap}',
                    side=side,mean_difference=d.mean(),paired_mcse=se,
                    ci95_low=d.mean()-1.96*se,ci95_high=d.mean()+1.96*se))
    csv_write('coverage.csv',rows)
    csv_write('paired_comparisons.csv',paired)
    np.savez_compressed(ROOT/'conditional_miss_samples.npz',**all_arrays)
    run = dict(arguments=vars(args),python=sys.version,platform=platform.platform(),
               numpy=np.__version__,scipy=scipy.__version__,rng='PCG64DXSM',
               quantile_method='NumPy linear (Hyndman-Fan type 7)',
               anchor_cells_passed=sum(r['agrees_at_printed_precision'] for r in anchors),
               cases=metadata,elapsed_seconds=time.perf_counter()-start)
    (ROOT/'run_metadata.json').write_text(json.dumps(run,indent=2),encoding='utf-8')
    print(json.dumps(dict(event='complete',elapsed_seconds=run['elapsed_seconds'],
                          anchor_cells_passed=run['anchor_cells_passed'],coverage_rows=len(rows))),flush=True)


if __name__ == '__main__':
    main()
