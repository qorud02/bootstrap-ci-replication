"""Prepare ReScience metadata and official-style TeX without changing research files."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import sys

ROOT=Path(__file__).resolve().parent
LATEX=ROOT/'latex'
sys.path.insert(0,str(ROOT/'_tools/python-deps'))
import yaml

parser=argparse.ArgumentParser()
parser.add_argument('--manuscript',type=Path,default=ROOT/'paper.md')
parser.add_argument('--email',default='qorud001@gmail.com')
parser.add_argument('--orcid',default='')
parser.add_argument('--code-url',default='https://github.com/qorud02/bootstrap-ci-replication')
parser.add_argument('--data-url',default='https://github.com/qorud02/bootstrap-ci-replication')
parser.add_argument('--code-doi',default='',help='Set only after the archival record is published')
parser.add_argument('--data-doi',default='',help='Set only after the archival record is published')
parser.add_argument('--figures',type=Path,default=ROOT/'figures')
parser.add_argument('--competing-interests',default=None,help='Only a statement explicitly confirmed by the author')
parser.add_argument('--funding',default=None,help='Only a statement explicitly confirmed by the author')
parser.add_argument('--eligibility-confirmed',action='store_true',help='Author has confirmed no disqualifying close collaboration')
args=parser.parse_args()
original=args.manuscript.read_text(encoding='utf-8')
front,body=re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$',original,re.S).groups()
front=yaml.safe_load(front)
title=front['title']
if not title.startswith('[Re]'):
    title='[Re] '+title
abstract=re.search(r'^# Abstract\s*\n(.*?)(?=\n# )',body,re.S|re.M).group(1)
abstract=' '.join(abstract.split())

meta={
 'title':title,
 'authors':[{'name':'Kyunghan Bae','orcid':args.orcid,'email':args.email,'affiliations':'1,*'}],
 'affiliations':[{'code':1,'name':'Independent researcher','address':'South Korea'}],
 'keywords':'bootstrap, confidence intervals, small samples, Monte Carlo, Python',
 'code':[{'url':args.code_url},{'doi':args.code_doi},{'swh':''}],
 'data':[{'url':args.data_url},{'doi':args.data_doi}],
 'replication':[
  {'cite':'Hesterberg, T. C. (2015). What Teachers Should Know About the Bootstrap: Resampling in the Undergraduate Statistics Curriculum. The American Statistician, 69(4), 371–386.'},
  {'bib':'hesterberg2015'},
  {'url':'https://arxiv.org/pdf/1411.5279v1'},
  {'doi':'10.1080/00031305.2015.1089789'}],
 'abstract':abstract,'bibliography':'bibliography.bib','type':'Replication','domain':'Statistics','language':'Python',
 'review':[{'url':''}],
 'contributors':[{'name':'','orcid':'','role':'editor'},{'name':'','orcid':'','role':'reviewer'},{'name':'','orcid':'','role':'reviewer'}],
 'dates':[{'received':''},{'accepted':''},{'published':''}],
 'article':[{'number':''},{'doi':''},{'url':''}],
 'journal':[{'name':'ReScience C'},{'issn':'2430-3658'},{'volume':''},{'issue':''}],
}
metadata_text=yaml.safe_dump(meta,allow_unicode=True,sort_keys=False,width=100000)
metadata_text=re.sub(r'^abstract:.*$',lambda _: 'abstract: '+json.dumps(abstract,ensure_ascii=False),metadata_text,flags=re.M)
(ROOT/'metadata.yaml').write_text(metadata_text,encoding='utf-8')
(LATEX/'metadata.yaml').write_text(metadata_text,encoding='utf-8')

# Use the official parser and converter, bypassing only its Unix-specific
# locale-setting CLI wrapper. Their algorithm is unchanged.
sys.path.insert(0,str(LATEX))
from article import Article
spec=importlib.util.spec_from_file_location('official_converter',LATEX/'yaml-to-latex.py')
converter=importlib.util.module_from_spec(spec)
spec.loader.exec_module(converter)
article=Article(metadata_text)
metadata_tex=converter.generate_latex_metadata('metadata.yaml',article)
(LATEX/'metadata.tex').write_text(metadata_tex,encoding='utf-8')

def escape(s):
    chars={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}
    return ''.join(chars.get(c,c) for c in s)

def inline(s):
    parts=re.split(r'(\$[^$\n]*\$|`[^`]*`|\[[^\]]+\]\([^)]*\)|\*[^*\n]+\*)',s)
    out=[]
    for p in parts:
        if p.startswith('$') and p.endswith('$'):
            out.append(p)
        elif p.startswith('`') and p.endswith('`'):
            code=escape(p[1:-1]).replace(r'\_',r'\_\allowbreak{}').replace('.',r'.\allowbreak{}')
            out.append(r'\texttt{'+code+'}')
        elif re.fullmatch(r'\[[^\]]+\]\([^)]*\)',p):
            m=re.fullmatch(r'\[([^\]]+)\]\(([^)]*)\)',p)
            out.append(r'\href{'+m[2]+'}{'+escape(m[1])+'}')
        elif p.startswith('*') and p.endswith('*'):
            out.append(r'\emph{'+escape(p[1:-1])+'}')
        else:
            out.append(escape(p))
    return ''.join(out)

lines=body.splitlines()
content=[]
paragraph=[]
def flush():
    if paragraph:
        text=inline(' '.join(x.strip() for x in paragraph))
        text=text.replace('(Hesterberg, 2014, 2015)',r'\cite{hesterberg2014,hesterberg2015}')
        content.append(text+'\n')
        paragraph.clear()

i=0
while i<len(lines):
    line=lines[i].strip()
    if line=='# References':
        flush()
        break
    if line.startswith('# '):
        flush()
        heading=line[2:]
        cmd=r'\section*' if heading=='Abstract' else r'\section'
        content.append(cmd+'{'+escape(heading)+'}\n')
    elif line.startswith('!['):
        flush()
        m=re.fullmatch(r'!\[(.*)\]\(([^)]*)\)',line)
        figure=Path(m[2]).with_suffix('.pdf').name
        figure_source=args.figures/figure if (args.figures/figure).exists() else args.manuscript.parent/figure
        shutil.copy2(figure_source,LATEX/figure)
        content.append(r'\begin{figure}[tbp]'+'\n'+r'\centering'+'\n'+r'\includegraphics[width=\linewidth]{'+figure+'}\n'+r'\caption{'+inline(m[1])+'}\n'+r'\end{figure}'+'\n')
    elif line.startswith('$$') and line.endswith('$$'):
        flush()
        content.append('\\[\n'+line[2:-2]+'\n\\]\n')
    elif line.startswith('|'):
        flush()
        table=[]
        while i<len(lines) and lines[i].strip().startswith('|'):
            table.append([x.strip() for x in lines[i].strip().strip('|').split('|')])
            i+=1
        headers,values=table[0],table[2:]
        ncols=len(headers)
        if ncols==2:
            spec=r'@{}p{.23\linewidth}p{.72\linewidth}@{}'
            size=r'\small'
        elif ncols==7:
            headers=['n','Method','Left miss','Right miss','Coverage','MCSE(L)','MCSE(R)']
            spec='@{}rlrrrrr@{}'
            size=r'\scriptsize'
        else:
            spec='@{}'+'r'*ncols+'@{}'
            size=r'\small'
        content.append('{'+size+r'\setlength{\tabcolsep}{3pt}'+'\n'+r'\begin{longtable}{'+spec+'}\n'+r'\toprule'+'\n')
        header=' & '.join(inline(x) for x in headers)+r' \\'+'\n'+r'\midrule'+'\n'
        content.append(header+r'\endfirsthead'+'\n'+r'\toprule'+'\n'+header+r'\endhead'+'\n')
        content.extend(' & '.join(inline(x) for x in row)+r' \\'+'\n' for row in values)
        content.append(r'\bottomrule'+'\n'+r'\end{longtable}'+'\n}\n')
        continue
    elif not line:
        flush()
    else:
        paragraph.append(line)
    i+=1
flush()
if args.funding:
    content.extend([r'\section*{Funding}'+'\n',inline(args.funding)+'\n'])
content.append(r'\nocite{hesterberg2015,hesterberg2014}'+'\n')
(LATEX/'content.tex').write_text('\n'.join(content),encoding='utf-8')
shutil.copy2(args.manuscript.parent/'paper.bib',LATEX/'bibliography.bib')

# BibTeX is available inside Tectonic. This backend substitution preserves
# the official numeric bibliography style and avoids an unpinned Biber binary.
classfile=LATEX/'rescience.cls'
class_text=classfile.read_text(encoding='utf-8').replace('backend=biber,','backend=bibtex,')
classfile.write_text(class_text,encoding='utf-8')
tex=(LATEX/'article.tex').read_text(encoding='utf-8')
if r'\usepackage{booktabs,longtable,array,graphicx}' not in tex:
    tex=tex.replace(r'\documentclass{rescience}',r'\documentclass{rescience}'+'\n'+r'\usepackage{booktabs,longtable,array,graphicx}')
if r'\setlength{\emergencystretch}{2em}' not in tex:
    tex=tex.replace(r'\usepackage{booktabs,longtable,array,graphicx}',r'\usepackage{booktabs,longtable,array,graphicx}'+'\n'+r'\setlength{\emergencystretch}{2em}')
(LATEX/'article.tex').write_text(tex,encoding='utf-8')
headerfile=LATEX/'header.tex'
header=headerfile.read_text(encoding='utf-8')
sentence='The authors have declared that no competing interests exist.'
# A fixed template sentence is not an author declaration. Restore it only
# on an explicit confirmed statement, preserving the supplied wording.
header=re.sub(r'(?m)^\s*'+re.escape(sentence)+r'\s*$', '',header)
marker='% AUTHOR_CONFIRMED_COMPETING_INTERESTS'
header=re.sub(re.escape(marker)+r'.*?% END_AUTHOR_CONFIRMED_COMPETING_INTERESTS','',header,flags=re.S)
if args.competing_interests:
    header=header.replace(r'\ifdefempty{\codeURL}',marker+'\n'+inline(args.competing_interests)+r'\par'+'\n% END_AUTHOR_CONFIRMED_COMPETING_INTERESTS\n'+r'\ifdefempty{\codeURL}',1)
headerfile.write_text(header,encoding='utf-8')

front['title']=title
submission_body=body
declarations=[]
if args.funding:
    declarations.append('# Funding\n\n'+args.funding+'\n\n')
if args.competing_interests:
    declarations.append('# Competing interests\n\n'+args.competing_interests+'\n\n')
if declarations:
    submission_body=submission_body.replace('# References\n',''.join(declarations)+'# References\n',1)
front['code_doi']=args.code_doi
front['data_doi']=args.data_doi
copy='---\n'+yaml.safe_dump(front,allow_unicode=True,sort_keys=False)+'---\n\n'+submission_body
(ROOT/'submission_manuscript.md').write_text(copy,encoding='utf-8')
issue=f'''**Original article:** Hesterberg (2015), The American Statistician 69(4), 371–386. DOI: 10.1080/00031305.2015.1089789.

This is a partial replication of journal Figure 10 for normal and exponential means at n=10,20,40, supplemented by all 20 printed numerical cells of Table 5 in the 2014 extended manuscript. Seven interval algorithms are implemented independently. The submission includes Monte Carlo uncertainty, a paired finite-resample sensitivity experiment, and archived conditional weights.

**PDF URL:** https://raw.githubusercontent.com/qorud02/bootstrap-ci-replication/main/article.pdf
**Metadata URL:** https://raw.githubusercontent.com/qorud02/bootstrap-ci-replication/main/metadata.yaml
**Code URL:** {args.code_url}

**Scientific domain:** Statistics
**Programming language:** Python
**Suggested editor:**
'''
(ROOT/'submission_issue.md').write_text(issue,encoding='utf-8')
validation={
 'official_template_commit':'0978d0e5d9a86246789fd3468aec6fc71e39c944',
 'official_parser_loaded':True,'contact_author':article.contact.name,'contact_email':article.contact.email,
 'orcid':article.contact.orcid,'metadata_title':article.title,
 'code_url_requires_publication_verification':True,
 'close_collaborator_eligibility_requires_author_confirmation':not args.eligibility_confirmed,
 'close_collaborator_eligibility_author_confirmed':args.eligibility_confirmed,
 'code_doi':args.code_doi,'data_doi':args.data_doi,
 'competing_interests_confirmed_text':args.competing_interests,
 'funding_confirmed_text':args.funding,
 'original_manuscript_sha256':hashlib.sha256(args.manuscript.read_bytes()).hexdigest(),
 'template_changes':['BibLaTeX backend biber to bibtex','Add booktabs/longtable/array/graphicx','Use only author-confirmed competing-interests wording'],
}
(ROOT/'preparation_validation.json').write_text(json.dumps(validation,indent=2),encoding='utf-8')
print(json.dumps(validation,indent=2))
