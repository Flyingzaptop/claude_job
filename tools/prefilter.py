"""Merge data/raw/*.jsonl, dedupe and drop obvious misfits -> data/candidates.jsonl (cheap keyword pass before LLM scoring)."""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SENIOR = re.compile(r"\b(senior|sr\.?|lead|principal|staff|director|head of|manager|kierownik|dyrektor|architect|ekspert)\b", re.I)
GERMAN = re.compile(json.loads((ROOT / "config.json").read_text(encoding="utf-8")).get("excluded_language_regex") or r"$^", re.I)  # required languages the candidate lacks
KW = json.loads((ROOT / "tools" / "search" / "keywords.json").read_text(encoding="utf-8"))
RELEVANT = re.compile("|".join(re.escape(k) for k in KW["a"] + KW["b"] + ["junior", "intern", "trainee", "staż", "praktyk", "student"]), re.I)

def norm(s): return re.sub(r"[^a-z0-9ąćęłńóśźż ]", " ", (s or "").lower())
# Generic title words say nothing about which role it is; only the rest are compared.
STOP = set("""płatny platny staż staz stażysta intern internship w we z i na do dla dziale dział the of and in for at to a
junior młodszy mlodszy senior mid specjalista specialist k m f x n d kmx engineer inżynier inzynier""".split())
def words(s): return {w for w in norm(s).split() if w not in STOP}
EXCL = [(norm(e["company"]).strip(), words(e["role"])) for e in json.load(open(ROOT / "data" / "exclusions.json"))]
def applied(r):
    """Same company and a clearly overlapping role title -> already applied."""
    c, t = norm(r["company"]), words(r["title"])
    for ec, er in EXCL:
        if ec and er and (ec in c or (len(c.strip()) >= 4 and c.strip() in ec)) and len(t & er) >= max(1, (len(er) + 1) // 2): return True
    return False

seen, keys, out, skipped = set(), set(), [], 0
for f in sorted((ROOT / "data" / "raw").glob("*.jsonl")):
    for line in f.open():
        r = json.loads(line)
        k = (r["title"] or "").lower().strip(), (r["company"] or "").lower().strip()
        if r["id"] in seen or k in keys: continue
        seen.add(r["id"]); keys.add(k)
        title, text = r["title"] or "", r.get("text") or ""
        if SENIOR.search(title) or not RELEVANT.search(title): continue
        if GERMAN.search(text) or (r["source"] == "arbeitnow" and re.search(r"\b(m/w/d|w/m/d)\b", title) and not re.search(r"[a-z]{3,} engineer", title, re.I)): continue
        if applied(r): skipped += 1; continue
        if r.get("triage") == "drop": continue  # Haiku triage said clearly irrelevant
        out.append(r)
with open(ROOT / "data" / "candidates.jsonl", "w") as fh:
    for r in out: fh.write(json.dumps(r, ensure_ascii=False) + "\n")
from collections import Counter
print(len(out), Counter(r["source"] for r in out), "already applied:", skipped)
