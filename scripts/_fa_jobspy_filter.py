#!/usr/bin/env python3
import json, glob, re

FA_PAT = re.compile(r"(founder'?s?\s+associate|founding\s+(operator|generalist|team|associate|member)|member of (the )?founding team|chief of staff|business operations|biz\s?ops|strateg(y|ic) (and|&) operations|operations associate|operations generalist|special projects|0\s?-?>?\s?1|zero to one|founding generalist)", re.I)
EXCL = re.compile(r"\b(senior|lead|head of|director|vp\b|principal|staff|intern\b|internship|junior|manager,? partner|recruiter)\b", re.I)
UK_PAT = re.compile(r"(london|cambridge|oxford|bristol|edinburgh|manchester|united kingdom|england|\buk\b)", re.I)

# Known dedup company tokens (on jun23/jun25 boards or applied)
SEEN = set("ramp encord conduct tem seamflow axle maze lightdash junior meticulous omnea aries techtree spruce synthesized 01health 32co conveo helmguard valence dust mistral ivee".split())

seen_keys=set()
rows=[]
for f in glob.glob("output/jobs/fa-operator-scan-jun25/*.json"):
    d=json.load(open(f))
    for j in d.get("jobs", d if isinstance(d,list) else []):
        t=j.get("title","") or ""
        comp=j.get("company","") or ""
        loc=j.get("location","") or ""
        if not FA_PAT.search(t): continue
        if EXCL.search(t): continue
        if not UK_PAT.search(loc): continue
        key=(comp.lower().strip(), t.lower().strip())
        if key in seen_keys: continue
        seen_keys.add(key)
        ct=comp.lower()
        dedup = any(s in ct for s in SEEN)
        rows.append({"title":t,"company":comp,"location":loc,"url":j.get("job_url"),"site":j.get("site"),"date":j.get("date_posted"),"dedup_flag":dedup})

rows.sort(key=lambda x:(x["dedup_flag"], x["company"]))
print(f"# {len(rows)} unique FA-family UK rows")
for r in rows:
    flag="DEDUP?" if r["dedup_flag"] else "NEW"
    print(f"[{flag}] {r['company']} | {r['title']} | {r['location']} | {r['site']} | {r['date']}")
    print(f"   {r['url']}")
