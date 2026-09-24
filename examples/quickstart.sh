#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
OUT=$(mktemp -d "${TMPDIR:-/tmp}/claim-audit-example.XXXXXX")
python3 - "$OUT/evidence-pack.json" <<'PY'
import json,sys
from pathlib import Path
path=Path(sys.argv[1])
pack={'schema':1,
 'plan':{'question':'What period does the synthetic specification define?','scope':'Synthetic specification only','as_of_time':'not time-sensitive','completion_rule':'One retrieved official source directly answers the claim.'},
 'sources':[{'id':'S001','url':'https://standards.example/spec','title':'Synthetic specification','publisher':'Example Standards','source_type':'official','independent_group':'synthetic-spec','retrieved':True,'accessed_at':'2026-09-23T00:00:00Z'}],
 'claims':[{'id':'C001','text':'The synthetic specification defines a 30 day period.','kind':'fact','status':'verified','citations':['S001'],'evidence':[{'source_id':'S001','relation':'supports','locator':'Section 2','excerpt':'The period is 30 days.'}]}],
 'contradictions':[],
 'report':{'title':'Synthetic research report','sections':[{'claim_id':'C001','text':'The specification defines a 30 day period.'}]}}
path.write_text(json.dumps(pack,indent=2)+'\n')
PY
python3 "$ROOT/scripts/finalize-research.py" "$OUT/evidence-pack.json" "$OUT" >/dev/null
python3 - "$OUT/final-audit.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]));assert d['passed'] and d['claims']==1 and d['sources']==1
PY
grep -q '\[C001\]\[S001\]' "$OUT/report.md"
echo "Artifacts: $OUT"
echo "Quickstart passed: claim-audit"
