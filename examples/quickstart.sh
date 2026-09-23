#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
OUT=$(mktemp -d "${TMPDIR:-/tmp}/research-verifier-example.XXXXXX")
python3 "$ROOT/scripts/init-research.py" "$OUT" >/dev/null
python3 - "$OUT" <<'PY'
import json,sys
from pathlib import Path
r=Path(sys.argv[1])
def write(name,value):(r/name).write_text(json.dumps(value,indent=2)+'\n')
write('source-register.json',{'schema':1,'sources':[{'id':'S001','url':'https://standards.example/spec','title':'Synthetic specification','publisher':'Example Standards','source_type':'official','independent_group':'synthetic-spec','retrieved':True,'accessed_at':'2026-09-23T00:00:00Z'}]})
write('claim-ledger.json',{'schema':1,'claims':[{'id':'C001','text':'The synthetic specification defines a 30 day period.','kind':'fact','status':'verified','citations':['S001'],'evidence':[{'source_id':'S001','relation':'supports','locator':'Section 2','excerpt':'The period is 30 days.'}]}]})
write('contradictions.json',{'schema':1,'contradictions':[]})
(r/'report.md').write_text('# Synthetic research report\n\nThe specification defines a 30 day period. [C001][S001]\n')
PY
python3 "$ROOT/scripts/validate-ledger.py" "$OUT" >/dev/null
python3 "$ROOT/scripts/audit-report.py" "$OUT" >/dev/null
python3 - "$OUT/final-audit.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]));assert d['passed'] and d['claims']==1 and d['sources']==1
PY
echo "Artifacts: $OUT"
echo "Quickstart passed: research-verifier"
