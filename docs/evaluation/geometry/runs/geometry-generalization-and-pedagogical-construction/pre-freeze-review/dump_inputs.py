import json, os, sys
sys.argv = [sys.argv[0], sys.argv[1], os.devnull]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'probes2.py'), encoding='utf-8').read().split('def run(fn, p):')[0]
ns = {'__file__': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'probes2.py')}; exec(src, ns)
json.dump(ns['P'], open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'probes2-inputs.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
