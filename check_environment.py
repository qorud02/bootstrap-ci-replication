import sys
print(sys.version, flush=True)
for m in ['numpy','scipy','matplotlib','pandas']:
    try:
        x=__import__(m)
        print(m,x.__version__,flush=True)
    except Exception as exc:
        print(m,repr(exc),flush=True)
