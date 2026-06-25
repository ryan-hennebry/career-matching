#!/usr/bin/env python3
import json, sys, urllib.request, re

ASHBY = "ramp mistral encord omnea heidihealth tessl glean cognition decagon sierra dust writer harvey hebbia lovable granola cleo n8n conduct helmguard conveo tem valence seamflow ariesglobal axle-careers spruce maze mazehq capsa attio elevenlabs juro lightdash odin meticulous rollstack junior multiverse cohere synthesia wayve nscale searchable".split()

# FA-family title matcher
FA_PAT = re.compile(r"(founder'?s?\s+associate|founding\s+(operator|generalist|team|associate)|member of (the )?founding team|chief of staff|business operations|biz\s?ops|strateg(y|ic) (and|&) operations|operations associate|operations generalist|special projects|0\s?-?>?\s?1|zero to one|generalist|deployment strategist|forward deployed)", re.I)
EXCL = re.compile(r"\b(senior|lead|head of|director|vp|principal|staff|intern\b|internship|junior)\b", re.I)
UK_PAT = re.compile(r"(london|cambridge|oxford|bristol|edinburgh|manchester|united kingdom|\buk\b|england|remote.*uk|uk.*remote)", re.I)

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

results = []
for s in ASHBY:
    try:
        d = fetch(f"https://api.ashbyhq.com/posting-api/job-board/{s}?includeCompensation=true")
        jobs = d.get("jobs", [])
    except Exception as e:
        print(f"# {s}: ERR {e}", file=sys.stderr)
        continue
    hit = 0
    for j in jobs:
        t = j.get("title","")
        loc = (j.get("location") or "") + " " + str(j.get("address") or "") + " " + " ".join(j.get("secondaryLocations",[]) and [str(x) for x in j.get("secondaryLocations",[])] or [])
        if not FA_PAT.search(t): continue
        if EXCL.search(t): continue
        uk = bool(UK_PAT.search(loc)) or bool(j.get("isRemote") and UK_PAT.search(loc))
        results.append({
            "slug": s, "title": t, "location": loc.strip(), "uk_loc": uk,
            "isListed": j.get("isListed"), "url": j.get("jobUrl") or j.get("applyUrl"),
            "id": j.get("id"), "published": j.get("publishedDate"),
            "comp": j.get("compensation",{}).get("compensationTierSummary") if isinstance(j.get("compensation"),dict) else None,
        })
        hit += 1
    print(f"# {s}: {len(jobs)} jobs, {hit} FA-family hits", file=sys.stderr)

print(json.dumps(results, indent=2))
