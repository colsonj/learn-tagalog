#!/usr/bin/env python3
"""Pre-generate offline audio for every Tagalog string in the curriculum.

Uses the fil-PH-AngeloNeural voice (male Filipino) via edge-tts and writes
web/audio/<sha1-16>.mp3 plus web/audio/manifest.json ({text: hash}), which the
frontend uses for fully-offline playback in any browser. Run once per
curriculum change, then rebuild. Requires internet during generation only.
"""
import asyncio, glob, hashlib, json, os, sys

import edge_tts

VOICE = "fil-PH-AngeloNeural"
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "web", "audio")
CONCURRENCY = 8
RETRIES = 4

PREVIEW = "Magandang hapon! Kumusta ka? Ito ang boses na gagamitin mo sa pag-aaral ng Tagalog."


def collect_texts():
    texts = {PREVIEW.strip()}

    def add(s):
        if s and isinstance(s, str) and s.strip():
            texts.add(s.strip())

    for f in glob.glob(os.path.join(ROOT, "data", "*", "*.json")):
        data = json.load(open(f, encoding="utf-8"))
        name = os.path.basename(f)
        if name == "meta.json":
            continue
        qs = data.get("questions", data.get("exercises", []))
        for q in qs:
            if q.get("type") == "listen":
                add(q.get("tl"))
        if name == "exam.json":
            continue
        for g in data.get("grammar", []):
            for e in g.get("examples", []):
                add(e.get("tl"))
        for v in data.get("vocab", []):
            add(v.get("tl"))
            add((v.get("example") or {}).get("tl"))
        for ln in (data.get("dialogue") or {}).get("lines", []):
            add(ln.get("tl"))
        r = data.get("reading")
        if r:
            add(r.get("tl"))
    return sorted(texts)


def hid(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


async def synth(sem, text, path):
    async with sem:
        for attempt in range(RETRIES):
            try:
                await edge_tts.Communicate(text, VOICE).save(path)
                if os.path.getsize(path) > 400:  # sanity: non-empty audio
                    return True
                raise RuntimeError("suspiciously small file")
            except Exception as e:
                if os.path.exists(path):
                    os.remove(path)
                if attempt == RETRIES - 1:
                    print(f"FAILED after {RETRIES} tries: {text[:60]!r}: {e}")
                    return False
                await asyncio.sleep(2 * (attempt + 1))


async def main():
    os.makedirs(OUT, exist_ok=True)
    texts = collect_texts()
    manifest = {t: hid(t) for t in texts}
    todo = [(t, os.path.join(OUT, h + ".mp3")) for t, h in manifest.items()
            if not os.path.exists(os.path.join(OUT, h + ".mp3"))]
    print(f"{len(texts)} unique utterances, {len(todo)} to synthesize")
    sem = asyncio.Semaphore(CONCURRENCY)
    done = 0
    failed = 0
    tasks = [synth(sem, t, p) for t, p in todo]
    for i in range(0, len(tasks), 100):
        results = await asyncio.gather(*tasks[i:i + 100])
        done += sum(1 for r in results if r)
        failed += sum(1 for r in results if not r)
        print(f"  progress: {min(i+100, len(tasks))}/{len(tasks)} (ok={done} failed={failed})")

    # only list clips that actually exist so the frontend can trust the manifest
    final = {t: h for t, h in manifest.items()
             if os.path.exists(os.path.join(OUT, h + ".mp3"))}
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, separators=(",", ":"))
    size = sum(os.path.getsize(os.path.join(OUT, x)) for x in os.listdir(OUT))
    print(f"manifest: {len(final)} clips, audio dir {size/1e6:.1f} MB, failures: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
