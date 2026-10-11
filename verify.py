"""Focused mathematical checks independent of the large simulation run."""
from pathlib import Path
import argparse
import json
import os
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument('--dependencies', help='Optional local dependency directory')
args = parser.parse_args()
if args.dependencies:
    os.environ['BOOTSTRAP_REPLICATION_DEPS'] = args.dependencies
import replicate as r
from scipy.integrate import quad

ROOT = Path(__file__).resolve().parent
np, stats = r.np, r.stats
checks=[]

def record(name, passed, detail):
    checks.append(dict(name=name,passed=bool(passed),detail=detail))
    if not passed:
        raise AssertionError(name)

anchors=r.anchor_table()
record('20 original Table5 numerical cells',all(x['agrees_at_printed_precision'] for x in anchors),20)

rng=np.random.default_rng(928131)
x=rng.normal(size=(8,10))
indices=rng.integers(10,size=(8,399,10),dtype=np.int16)
ci,_=r.endpoints(x,indices)
translated,_=r.endpoints(x+7.25,indices)
scaled,_=r.endpoints(x*3.5,indices)
record('all 7 interval translation equivariance',np.allclose(translated,ci+7.25,rtol=0,atol=1e-12),float(np.max(abs(translated-ci-7.25))))
record('all 7 interval positive scale equivariance',np.allclose(scaled,3.5*ci,rtol=0,atol=1e-12),float(np.max(abs(scaled-3.5*ci))))

for n in [10,20,40]:
    tc=stats.t.ppf(.975,n-1)
    value,err=quad(lambda q:stats.norm.cdf(-tc*np.sqrt(q/(n-1)))*stats.chi2.pdf(q,n-1),0,np.inf,epsabs=1e-12)
    record(f'normal conditioned Student t exact size n={n}',abs(value-.025)<1e-10,dict(calculated=value,quadrature_error=err))

# Verify the gamma conditioning algebra by integrating an independent sample
# mean against a frozen interval on a normalized exponential residual vector.
n=10
lower_v,upper_v=.6,1.4
left=stats.gamma.sf(1/lower_v,a=n,scale=1/n)
right=stats.gamma.cdf(1/upper_v,a=n,scale=1/n)
mean=rng.gamma(shape=n,scale=1/n,size=300000)
binary_left=np.mean(mean*lower_v>1)
binary_right=np.mean(mean*upper_v<1)
max_z=max(abs(binary_left-left)/np.sqrt(left*(1-left)/len(mean)),abs(binary_right-right)/np.sqrt(right*(1-right)/len(mean)))
record('exponential normalization/conditional tails',max_z<5,dict(left_analytic=left,left_binary=binary_left,right_analytic=right,right_binary=binary_right,max_z=max_z))

try:
    r.endpoints(x,np.zeros((8,399,10),dtype=np.int16))
    rejected=False
except RuntimeError:
    rejected=True
record('undefined studentized resamples trigger explicit failure',rejected,True)

out=dict(passed=len(checks),checks=checks)
(ROOT/'verification.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
