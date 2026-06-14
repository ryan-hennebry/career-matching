import json, glob, re, os

os.chdir("/private/tmp/career-matching")

# Title exclusions (substring, case-insensitive). "Chief" allowed (Chief of Staff).
EXCL_TITLE = ["senior","lead","head ","head of","director","vp ","vice president",
              " svp","evp"," principal","staff ","intern","junior"," jr ","graduate"]
# careful: "lead" excludes "Leader"; "head" handled with space variants

def title_excluded(t):
    if not isinstance(t, str): return None
    tl = " " + t.lower() + " "
    for e in EXCL_TITLE:
        if e in tl:
            return e
    return None

# Operator-fit keywords (must match at least one)
OP_KW = ["founder","founding","chief of staff","operations","operator","generalist",
         "forward deployed","forward-deployed","deployment","delivery","implementation",
         "business operations","bizops","biz ops","strategy & op","strategy and op",
         "ai product","product associate","solutions","applied ai","ai strategist",
         "special projects","ceo office","founder's office","founders office"]

def op_fit(t):
    if not isinstance(t, str): return False
    tl = t.lower()
    return any(k in tl for k in OP_KW)

# Normalized excluded companies
with open("output/_freshsweep_exclusion.json") as f:
    excl = json.load(f)
EXCL_CO = set(excl["company_names_normalized"])

def norm_co(c):
    if not isinstance(c, str): return ""
    c = c.lower()
    c = re.sub(r"\b(ai|inc|ltd|llc|limited|technologies|labs|corp|gmbh|the)\b","",c)
    c = re.sub(r"[^a-z0-9 ]","",c)
    c = re.sub(r"\s+"," ",c).strip()
    return c

# Load all rows
all_rows = []
seen_urls = set()
for fp in glob.glob("output/jobs/*-aggregator.json"):
    with open(fp) as f:
        data = json.load(f)
    for j in data.get("jobs", []):
        url = j.get("job_url") or j.get("job_url_direct") or ""
        key = (norm_co(j.get("company","") or ""), (j.get("title","") or "").lower().strip())
        all_rows.append(j)

print(f"TOTAL RAW ROWS (all files): {len(all_rows)}")

# Dedup by (company,title)
uniq = {}
for j in all_rows:
    key = (norm_co(j.get("company","") or ""), (j.get("title","") or "").lower().strip())
    if key not in uniq:
        uniq[key] = j
print(f"UNIQUE (company,title): {len(uniq)}")

# Pipeline
title_kept = []
for key, j in uniq.items():
    t = j.get("title","") or ""
    if not t: continue
    ex = title_excluded(t)
    if ex: continue
    title_kept.append(j)
print(f"AFTER TITLE EXCLUSIONS: {len(title_kept)}")

opfit = [j for j in title_kept if op_fit(j.get("title",""))]
print(f"OPERATOR-FIT TITLES: {len(opfit)}")

# Remove excluded companies
candidates = []
for j in opfit:
    nc = norm_co(j.get("company","") or "")
    # match if any excluded token-set is substring
    excluded = False
    for ec in EXCL_CO:
        if ec and (ec == nc or (len(ec) > 3 and ec in nc) or (len(nc) > 3 and nc in ec)):
            excluded = True
            break
    if excluded: continue
    candidates.append(j)
print(f"AFTER COMPANY DEDUP-EXCLUDE: {len(candidates)}")

# Filter to UK-ish locations
def uk_loc(loc):
    if not isinstance(loc, str): return True
    if not loc: return True  # keep unknown for review
    ll = loc.lower()
    uk_tokens = ["united kingdom","uk","england","london","manchester","cambridge",
                 "oxford","bristol","edinburgh","scotland","wales","leeds","birmingham",
                 "remote","reading","brighton"]
    non_uk = ["united states","usa"," us "," ny","new york","san francisco","california",
              "germany","berlin","france","paris","spain","india","canada","australia",
              "netherlands","amsterdam","singapore","ireland","dublin"]
    if any(n in ll for n in non_uk) and not any(u in ll for u in ["united kingdom","london","england"]):
        return False
    return True

uk_cands = [j for j in candidates if uk_loc(j.get("location",""))]
print(f"UK-ELIGIBLE CANDIDATES: {len(uk_cands)}")
print("="*80)
for j in sorted(uk_cands, key=lambda x: norm_co(x.get("company","") or "")):
    site = j.get("site","?")
    co = j.get("company","?")
    t = j.get("title","?")
    loc = j.get("location","?")
    url = j.get("job_url") or j.get("job_url_direct") or ""
    desc = j.get("description")
    has_desc = "DESC" if (desc and str(desc).strip() and str(desc).lower()!="nan") else "nan"
    print(f"[{site}|{has_desc}] {co} :: {t} :: {loc}\n    {url}")

# Save candidates for next step
with open("/tmp/career-matching/uk_candidates.json","w") as f:
    json.dump(uk_cands, f, indent=2, default=str)
