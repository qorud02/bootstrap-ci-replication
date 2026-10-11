from pathlib import Path
import argparse
import os
import subprocess
import sys

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--dependencies', default=None)
args = parser.parse_args()
environment = os.environ.copy()
if args.dependencies:
    environment['BOOTSTRAP_REPLICATION_DEPS'] = args.dependencies
with (root/'execution.jsonl').open('w',encoding='utf-8') as log:
    process = subprocess.Popen([sys.executable,str(root/'replicate.py')],stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,text=True,encoding='utf-8',cwd=root,env=environment)
    for line in process.stdout:
        log.write(line)
        log.flush()
        print(line,end='',flush=True)
    code = process.wait()
    if code:
        raise SystemExit(code)
