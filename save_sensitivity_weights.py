"""Rebuild only the finite-B archive for an existing completed experiment.

The original run omitted those auxiliary weights. This helper repeats the
two cases with their recorded seeds, checks every recorded estimate and
paired standard error, then adds the weights without rerunning the main cases.
A fresh run of replicate.py saves the same arrays automatically.
"""
from pathlib import Path
import argparse
import contextlib
import csv
import json
import os
import sys
import time

parser=argparse.ArgumentParser()
parser.add_argument('--dependencies')
args=parser.parse_args()
if args.dependencies:
    os.environ['BOOTSTRAP_REPLICATION_DEPS']=args.dependencies
import replicate as r

ROOT=Path(__file__).resolve().parent
np=r.np
metadata=json.loads((ROOT/'run_metadata.json').read_text(encoding='utf-8'))
coverage=list(csv.DictReader((ROOT/'coverage.csv').open(encoding='utf-8')))
paired=list(csv.DictReader((ROOT/'paired_comparisons.csv').open(encoding='utf-8')))
with np.load(ROOT/'conditional_miss_samples.npz') as saved:
    arrays={name:saved[name].copy() for name in saved.files}

class Tee:
    def __init__(self,*streams):
        self.streams=streams
    def write(self,value):
        for stream in self.streams:
            stream.write(value)
            stream.flush()
    def flush(self):
        for stream in self.streams:
            stream.flush()

started=time.perf_counter()
cases=[]
checked=0
with (ROOT/'sensitivity_archive_execution.jsonl').open('w',encoding='utf-8') as log:
    with contextlib.redirect_stdout(Tee(sys.stdout,log)):
        for case in metadata['cases']:
            if case['label']!='finite_B':
                continue
            n,bs=case['n'],case['bootstrap_counts']
            outputs,new_meta=r.run_case(case['population'],n,case['outer'],bs,case['seed'],'archive_rebuild')
            for b,out in outputs.items():
                assert out['diagnostics']==case['diagnostics'][str(b)]
                arrays[f'finite_B_exponential_{n}_B{b}']=out['weighted']
                for j,method in enumerate(r.METHODS):
                    for k,side in enumerate(['left','right']):
                        target=next(v for v in coverage if v['experiment']=='finite_B' and int(v['n'])==n
                                    and int(v['bootstrap_resamples'])==b and v['method']==method and v['side']==side)
                        w=out['weighted'][:,j,k]
                        assert abs(float(w.mean())-float(target['miss_probability']))<1e-14
                        assert abs(float(w.std(ddof=1)/np.sqrt(len(w)))-float(target['monte_carlo_se']))<1e-14
                        checked+=1
            for j,method in enumerate(r.METHODS):
                for k,side in enumerate(['left','right']):
                    target=next(v for v in paired if int(v['n'])==n and v['side']==side
                                and v['comparison']==f'{method}_B{max(bs)}_minus_B{min(bs)}')
                    diff=outputs[max(bs)]['weighted'][:,j,k]-outputs[min(bs)]['weighted'][:,j,k]
                    assert abs(float(diff.mean())-float(target['mean_difference']))<1e-14
                    assert abs(float(diff.std(ddof=1)/np.sqrt(len(diff)))-float(target['paired_mcse']))<1e-14
                    checked+=1
            cases.append(new_meta)
        pending=ROOT/'conditional_miss_samples.pending.npz'
        np.savez_compressed(pending,**arrays)
        pending.replace(ROOT/'conditional_miss_samples.npz')
        result=dict(event='archive_complete',checked_rows=checked,archive_arrays=len(arrays),cases=cases,
                    elapsed_seconds=time.perf_counter()-started)
        (ROOT/'sensitivity_archive_metadata.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps(result),flush=True)
