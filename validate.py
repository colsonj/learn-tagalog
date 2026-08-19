#!/usr/bin/env python3
"""Validate TagTrain curriculum data against the schema in data/SCHEMA.md."""
import json, sys, glob, os

ROOT = os.path.join(os.path.dirname(__file__), "data")
EX_TYPES = {"mcq", "fill", "translate", "listen"}
errors = []

def err(f, msg):
    errors.append(f"{f}: {msg}")

def check_exercise(f, where, q):
    t = q.get("type")
    if t not in EX_TYPES:
        return err(f, f"{where}: bad type {t!r}")
    if not q.get("explain"):
        err(f, f"{where}: missing explain")
    if t in ("mcq", "listen"):
        ch = q.get("choices")
        if not isinstance(ch, list) or len(ch) < 2:
            return err(f, f"{where}: bad choices")
        a = q.get("answer")
        if not isinstance(a, int) or not (0 <= a < len(ch)):
            err(f, f"{where}: answer index {a!r} out of range 0..{len(ch)-1}")
        if t == "listen" and not q.get("tl"):
            err(f, f"{where}: listen missing tl")
        if not q.get("prompt"):
            err(f, f"{where}: missing prompt")
    else:
        if not q.get("answer"):
            err(f, f"{where}: missing answer")
        if not q.get("accept"):
            err(f, f"{where}: missing/empty accept")
        if not q.get("prompt"):
            err(f, f"{where}: missing prompt")
        if t == "translate" and q.get("direction") not in ("en2tl", "tl2en"):
            err(f, f"{where}: bad direction")

totals = {}
for lv in ("a1", "a2", "b1", "b2"):
    d = os.path.join(ROOT, lv)
    meta_f = os.path.join(d, "meta.json")
    exam_f = os.path.join(d, "exam.json")
    units_f = sorted(glob.glob(os.path.join(d, "unit*.json")))
    for f in (meta_f, exam_f):
        if not os.path.exists(f):
            err(f, "missing")
    vocab_count = 0
    for f in [meta_f, exam_f] + units_f:
        if not os.path.exists(f):
            continue
        try:
            data = json.load(open(f, encoding="utf-8"))
        except Exception as e:
            err(f, f"JSON parse error: {e}")
            continue
        name = os.path.basename(f)
        if name == "meta.json":
            for k in ("level", "title", "description", "canDo", "units"):
                if k not in data:
                    err(f, f"meta missing {k}")
            if len(units_f) != data.get("units"):
                err(f, f"meta says {data.get('units')} units, found {len(units_f)}")
        elif name == "exam.json":
            if not isinstance(data.get("passPct"), (int, float)):
                err(f, "missing passPct")
            qs = data.get("questions", [])
            if len(qs) < 30:
                err(f, f"exam has only {len(qs)} questions")
            for i, q in enumerate(qs):
                check_exercise(f, f"q{i}", q)
        else:
            for k in ("id", "title", "grammar", "vocab", "dialogue", "exercises"):
                if not data.get(k):
                    err(f, f"unit missing {k}")
            if lv in ("b1", "b2") and not data.get("reading"):
                err(f, "unit missing reading (required for B1/B2)")
            for vi, v in enumerate(data.get("vocab", [])):
                for k in ("tl", "en", "pos"):
                    if not v.get(k):
                        err(f, f"vocab[{vi}] missing {k}")
                if not v.get("example", {}).get("tl"):
                    err(f, f"vocab[{vi}] missing example")
            vocab_count += len(data.get("vocab", []))
            for ln in data.get("dialogue", {}).get("lines", []):
                if not (ln.get("speaker") and ln.get("tl") and ln.get("en")):
                    err(f, "dialogue line missing field")
            exs = data.get("exercises", [])
            if len(exs) < 8:
                err(f, f"only {len(exs)} exercises")
            for i, q in enumerate(exs):
                check_exercise(f, f"ex{i}", q)
    totals[lv] = {"units": len(units_f), "vocab": vocab_count}

for lv, t in totals.items():
    print(f"{lv.upper()}: {t['units']} units, {t['vocab']} vocab items")
if errors:
    print(f"\n{len(errors)} ERRORS:")
    for e in errors[:80]:
        print(" -", e)
    sys.exit(1)
print("\nAll curriculum files valid.")
