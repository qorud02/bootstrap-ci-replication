"""Render the archived estimates at the official article's text width."""
from pathlib import Path
import argparse
import csv
import sys

ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--results',type=Path,default=ROOT)
parser.add_argument('--dependencies',default='')
args=parser.parse_args()
if args.dependencies:
    sys.path.insert(0,args.dependencies)
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT=ROOT/'figures'
OUT.mkdir(exist_ok=True)
rows=list(csv.DictReader((args.results/'coverage.csv').open(encoding='utf-8')))
main=[r for r in rows if r['experiment']=='main']
methods=['t','tSkew','tBoot','percentile','reverse','expanded','bootT']
palette=dict(zip(methods,['#17375e','#773f89','#818898','#d67b18','#bd4c4e','#268a7e','#226aa5']))
labels=dict(t='Student t',tSkew='Skew-corrected t',tBoot='t with bootstrap SE',
            percentile='Percentile',reverse='Reverse percentile',expanded='Expanded percentile',bootT='Bootstrap t')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11.5,
                     'axes.spines.top':False,'axes.spines.right':False,
                     'savefig.dpi':240,'axes.titlesize':11.5,'legend.fontsize':10.5})
fig,axes=plt.subplots(2,2,figsize=(7.5,5.7),sharex=True)
for i,pop in enumerate(['normal','exponential']):
    for j,side in enumerate(['left','right']):
        ax=axes[i,j]
        for method in methods:
            rr=sorted([r for r in main if r['population']==pop and r['side']==side and r['method']==method],key=lambda r:int(r['n']))
            p=np.array([float(r['miss_probability']) for r in rr])
            err=np.array([float(r['ci95_high'])-float(r['miss_probability']) for r in rr])
            ax.errorbar([int(r['n']) for r in rr],p,yerr=err,label=labels[method],
                        color=palette[method],marker='o',capsize=2,linewidth=1.3,markersize=3.8)
        ax.axhline(.025,color='#222222',linestyle='--',linewidth=.9)
        ax.set_title(f'{pop.title()} · {side} miss')
        ax.set_xticks([10,20,40])
        ax.set_ylim((.022,.051) if pop=='normal' else ((0,.03) if side=='left' else (0,.16)))
        ax.grid(alpha=.17)
        ax.tick_params(labelsize=10.5)
        if j==0:
            ax.set_ylabel('Miss probability',fontsize=11)
        if i==1:
            ax.set_xlabel('Sample size n',fontsize=11)
handles,ll=axes[0,0].get_legend_handles_labels()
fig.legend(handles,ll,loc='lower center',ncol=3,frameon=False,bbox_to_anchor=(.5,-.005),
           handlelength=1.7,columnspacing=1.1,labelspacing=.45)
fig.tight_layout(rect=[0,.145,1,1],h_pad=1.1,w_pad=.9)
for suffix in ['pdf','png']:
    fig.savefig(OUT/f'coverage_replication.{suffix}',bbox_inches='tight',pad_inches=.03)
plt.close(fig)

paired=list(csv.DictReader((args.results/'paired_comparisons.csv').open(encoding='utf-8')))
fig,axes=plt.subplots(1,2,figsize=(7.5,3.0),sharey=True)
for ax,n in zip(axes,[10,40]):
    for j,method in enumerate(methods):
        row=next(r for r in paired if int(r['n'])==n and r['comparison']==f'{method}_B9999_minus_B1999' and r['side']=='right')
        difference=float(row['mean_difference'])
        ax.errorbar(j,difference,yerr=float(row['ci95_high'])-difference,fmt='o',capsize=3,
                    color=palette[method],markersize=4.8)
    ax.axhline(0,color='#222222',ls='--',lw=.9)
    ax.set_title(f'Exponential · n={n}')
    ax.set_xticks(range(len(methods)),methods,rotation=45,ha='right',fontsize=10.5)
    ax.tick_params(axis='y',labelsize=10.5)
    if n==10:
        ax.set_ylabel('Change in right miss probability',fontsize=10.5)
    ax.grid(alpha=.17)
fig.tight_layout(w_pad=1)
for suffix in ['pdf','png']:
    fig.savefig(OUT/f'finite_B_sensitivity.{suffix}',bbox_inches='tight',pad_inches=.03)
plt.close(fig)
print('Publication figures rendered from archived CSV estimates; no calculations changed.')
