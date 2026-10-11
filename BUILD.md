# Build the submission PDF

The local preparation directory contains the official ReScience template
and a portable Tectonic 0.17.0 executable. The research's original directory
is read as input and is not edited.

```text
python publication_figures.py --results PATH/TO/RESEARCH --dependencies PATH/TO/SCIENTIFIC/PACKAGES
python prepare_submission.py --manuscript PATH/TO/paper.md
cd latex
../_tools/tectonic/tectonic.exe -X compile --keep-intermediates --keep-logs article.tex
```

On Windows, use backslashes in the executable path if required by the shell.
`prepare_submission.py` accepts `--email`, `--orcid`, `--code-url` and
`--data-url`. `--code-doi` and `--data-doi` can be set after the archival record
is published. Publication figures are read from `figures/`, or an alternate
directory supplied with `--figures`; absent files fall back to the research
directory. `--competing-interests` and `--funding` accept only statements
explicitly confirmed by the author. Unknown personal facts are omitted.

The root `metadata.yaml` and its build copy are synchronized. The official
parser/converter are used to generate the TeX metadata. Rebuild after any
metadata or declaration change and inspect the resulting PDF before upload.

For a fresh environment, install PyYAML and obtain the official Tectonic
release. On Unix use the matching Tectonic executable. A traditional
XeLaTeX installation can also compile the supplied template with BibTeX.
Template source and font licenses are in `latex/`.

The figures are redrawn from the archived CSV estimates with larger labels
for the official article's text width. They contain the same estimates,
pointwise intervals and paired differences as the research figures.
