#!/usr/bin/env python3
"""Check the game data.  python3 validate.py   (run from the repo root)

questions.json: unique ids, 3 distinct wrong answers, answer not among them, valid topic/difficulty.
stats.json:     higher-or-lower items: unique ids, known category, positive number, a source note.
clues.json:     Guess-the-artist items: unique ids, exactly 5 clues, the answer not given away in a
                clue before the last, names/aliases unambiguous (also against the decoys).
"""
import json, sys, collections, os, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "server"))
import modes  # noqa: E402

TOPICS = ("art", "alb", "lyr", "era", "awd", "glb")
bad = []

# ---------------------------------------------------------------- questions
Q = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "docs/questions.json", encoding="utf-8"))
ids = collections.Counter(q["id"] for q in Q)
bad += [f"duplicate id {i}" for i, n in ids.items() if n > 1]
texts = collections.Counter(q["q"] for q in Q)
bad += [f"duplicate question: {t[:70]}" for t, n in texts.items() if n > 1]
for q in Q:
    if not re.match(r"^(art|alb|lyr|era|awd|glb)\d{3}$", q["id"]): bad.append(f"{q['id']}: bad id")
    if q["a"] in q["w"]: bad.append(f"{q['id']}: answer is among the wrong options")
    if any(len(o) > 44 for o in [q["a"], *q["w"]]): bad.append(f"{q['id']}: option too long for the buttons")
    opts = [q["a"], *q["w"]]
    if len(q["w"]) != 3: bad.append(f"{q['id']}: needs 3 wrong answers")
    if len({o.casefold() for o in opts}) != 4: bad.append(f"{q['id']}: repeated option")
    if q["l"] not in TOPICS: bad.append(f"{q['id']}: bad topic")
    if not q["id"].startswith(q["l"]): bad.append(f"{q['id']}: id doesn't start with its topic")
    if q["d"] not in (1, 2, 3): bad.append(f"{q['id']}: bad difficulty")
    if not q.get("x"): bad.append(f"{q['id']}: no explanation")
    if q.get("img"): bad.append(f"{q['id']}: this quiz has no image questions")

# ---------------------------------------------------------------- stats (higher or lower)
S = json.load(open("docs/stats.json", encoding="utf-8"))
cats = S["cats"]
sids = collections.Counter(i["id"] for i in S["items"])
bad += [f"stats: duplicate id {i}" for i, n in sids.items() if n > 1]
same = collections.Counter((i["c"], i["n"], i["d"]) for i in S["items"])
bad += [f"stats: duplicate item {k}" for k, n in same.items() if n > 1]
for i in S["items"]:
    if i["c"] not in cats: bad.append(f"stats {i['id']}: unknown category {i['c']}")
    yr = cats.get(i["c"], {}).get("year")
    if isinstance(i["v"], bool) or not isinstance(i["v"], (int, float)) or (i["v"] <= 0 and not yr) or (yr and not 1970 <= i["v"] <= 2026):
        bad.append(f"stats {i['id']}: bad value")
    for k in ("n", "d", "note"):
        if not str(i.get(k) or "").strip(): bad.append(f"stats {i['id']}: missing {k}")
per_cat = collections.Counter(i["c"] for i in S["items"])
for c in cats:
    its = [i for i in S["items"] if i["c"] == c]
    def can_pair(a, b, cat=cats[c]):
        if cat.get("year"):
            return abs(a["v"] - b["v"]) >= (30 if a.get("ap") or b.get("ap") else 10)
        return abs(a["v"] - b["v"]) / max(a["v"], b["v"]) >= cat.get("gap", 0.1)
    pairs = sum(1 for x in range(len(its)) for y in range(x + 1, len(its)) if can_pair(its[x], its[y]))
    for k in ("name", "unit", "word", "ask", "hi", "lo"):
        if not cats[c].get(k): bad.append(f"stats: category {c} missing {k}")
    if per_cat[c] < 8 or pairs < 20: bad.append(f"stats: category {c} too small ({per_cat[c]} items, {pairs} pairs)")

# ---------------------------------------------------------------- guess the artist (clues.json)
CD = json.load(open("docs/clues.json", encoding="utf-8"))
C = CD["items"]
cids = collections.Counter(p["id"] for p in C)
bad += [f"clues: duplicate id {i}" for i, n in cids.items() if n > 1]
owner = collections.defaultdict(set)
for p in C:
    for k in [modes.key(p["n"])] + [modes.key(a) for a in p.get("al", [])]:
        owner[k].add(p["n"])
    if len(p["clues"]) != 5: bad.append(f"clues {p['id']}: needs exactly 5 clues")
    if len(set(p["clues"])) != len(p["clues"]): bad.append(f"clues {p['id']}: repeated clue")
    names = [p["n"]] + p.get("al", [])
    for clue in p["clues"][:-1]:
        cw = " " + " ".join(modes.words(clue)) + " "
        for nm in names:
            nw = " ".join(modes.words(nm))
            if nw and " " + nw + " " in cw: bad.append(f"clues {p['id']}: '{nm}' given away in '{clue}'")
bad += [f"clues: '{k}' is a name or alias of {sorted(v)}" for k, v in owner.items() if len(v) > 1]
for d in CD.get("decoys", []):
    if modes.key(d) in owner: bad.append(f"clues: decoy '{d}' is also an answer")
forms = modes.build_forms(C)
taken = modes.taken_keys(C, CD.get("decoys", []))
for p in C:
    if not modes.is_match(p["n"], forms[p["id"]], taken): bad.append(f"clues {p['id']}: own name doesn't match")

print("\n".join(bad) or "OK")
print(len(Q), "questions:", dict(collections.Counter(q["l"] for q in Q)), "difficulty", dict(sorted(collections.Counter(q["d"] for q in Q).items())))
print(len(S["items"]), "higher-or-lower items:", dict(per_cat))
print(len(C), "guess-the-artist items,", len(CD.get("decoys", [])), "decoys")
sys.exit(1 if bad else 0)
