# Pull the original Prius model (PRIUS_DATA) out of the game file into /tmp/lp/prius.json for the build scripts.
import json, sys, os
src = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
t = open(src).read(); i = t.index('const PRIUS_DATA = ') + len('const PRIUS_DATA = '); j = t.index(';\n', i)
os.makedirs('/tmp/lp', exist_ok=True); json.dump(json.loads(t[i:j]), open('/tmp/lp/prius.json', 'w'))
print('wrote /tmp/lp/prius.json')
