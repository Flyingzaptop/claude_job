"""Join candidates with LLM scores -> tracker/jobs.json (published next to the tracker page)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
cand = {r["id"]: r for r in map(json.loads, (ROOT / "data" / "candidates.jsonl").open())}  # already-applied jobs are excluded here
scored = {}
for f in sorted((ROOT / "data").glob("scored_*.jsonl")):
    for line in f.open():
        line = line.strip()
        if not line: continue
        try: s = json.loads(line)
        except json.JSONDecodeError: continue
        if s.get("id") in cand: scored[s["id"]] = s
keep = ["id", "title", "company", "location", "posted", "url", "source"]
rows = [{**{k: cand[i].get(k) for k in keep}, **{k: v for k, v in s.items() if k != "id"}}
        for i, s in scored.items() if (s.get("fit", s.get("score")) or 0) >= 3]
for r in rows:  # older scores had one number = skills fit; schedule unknown
    r.setdefault("fit", r.pop("score", None)); r.setdefault("schedule", None)
import re
for r in rows:  # tailored CV built during a search run: tracker/cv/tailored/<safe id>.pdf
    f = ROOT / "tracker" / "cv" / "tailored" / (re.sub(r"[^A-Za-z0-9_\-.~:@+]", "_", r["id"]).replace(":", "_") + ".pdf")
    if f.exists(): r["cv_file"] = "cv/tailored/" + f.name
msgs = ROOT / "data" / "messages.json"  # tailored motivation messages from a search run: {id: {"PL": ..., "EN": ...}}
if msgs.exists():
    m = json.loads(msgs.read_text(encoding="utf-8"))
    for r in rows:
        if r["id"] in m: r["message"] = m[r["id"]]
rows.sort(key=lambda r: -((r.get("fit") or 0) + (r.get("schedule") or 5)))
(ROOT / "tracker" / "jobs.json").write_text(json.dumps(rows, ensure_ascii=False))
print(f"scored {len(scored)}/{len(cand)}, published {len(rows)}, fit 7+: {sum((r['fit'] or 0) >= 7 for r in rows)}")
