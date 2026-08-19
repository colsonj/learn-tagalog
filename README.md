# TagTrain 🇵🇭

A fully self-contained Windows app that teaches Tagalog from complete beginner
to CEFR B2, with a milestone exam gating each level.

> **Status: as-is / not maintained.** This project is published in a finished
> state and there will likely not be any further updates, fixes, or responses
> to issues and pull requests. Feel free to fork it.

**Download:** grab `TagTrain.exe` from the
[latest release](../../releases/latest) — no install needed, just run it.

## Running it

Copy `dist/TagTrain.exe` anywhere on a Windows machine and double-click it.
It opens your default browser at `http://127.0.0.1:8873` — the whole app
(curriculum, audio, exams, flashcards) is embedded in the exe; no internet
connection, install, or runtime is needed.

Your progress is saved to `tagtrain-progress.json` next to the exe, so you can
keep it on a USB stick. Use the **Quit app** button in the footer to close it
(the process also exits on its own a few minutes after the last browser tab
closes).

**Audio**: every Tagalog sentence in the course (3,522 utterances) is embedded
in the exe as a recording of the Filipino male neural voice **Angelo**, so
pronunciation is native quality, fully offline, and identical in every
browser. Pressing the same ► twice in a row automatically replays it slowed
down (pitch preserved), Google-Translate style. The **🔊 Voice & speed**
button in the header sets the base playback speed and lets you preview and
switch to a browser text-to-speech voice instead if you prefer. To regenerate
the audio after editing the curriculum, run `python3 gen_audio.py`
(needs internet + `pip install edge-tts`), then rebuild.

**Updating the exe**: launching a newer TagTrain.exe automatically shuts down
any older version still running in the background and takes over, so you
always see the build you double-clicked.

## Structure of the course

- **A1 Foundations** — 10 units: greetings and po/opo, numbers and time,
  family, food, adjectives and linkers, location, first verbs (mag-/-um- and
  the three aspects), shopping, dates, question words.
- **A2 Everyday Tagalog** — 10 units: the sa-pronouns, object-focus -in verbs,
  aspect mastery, ability/obligation words, enclitic particles, directions and
  -an verbs, health, comparisons, past experiences, i- verbs and future plans.
- **B1 Independent user** — 12 units: the four-voice focus system as a system,
  maka-/na-, causative magpa-, emotion verbs, particle mastery, opinions,
  conditionals, relative clauses, reported speech, professional life,
  narration, current topics. Every unit adds a reading passage.
- **B2 Upper intermediate** — 12 units: voice nuance (i- vs -an), formal and
  written Tagalog, nominalization, advanced conditionals, concession,
  idioms, news, debate, literature, professional/academic language, capstone.

Each unit = grammar lessons, 22–40 vocabulary items (with audio and example
sentences), a dialogue, a reading passage (B1/B2), and a scored practice set
(70% to complete the unit). Finish all units of a level to unlock its timed
**milestone exam** (36–44 questions, ~70–75% pass mark, modelled on the CEFR
can-do statements for that level). Passing the exam unlocks the next level.

Daily **flashcard review** uses SM-2 spaced repetition over the vocabulary of
every unit you've opened.

## Building from source

Requires Go 1.21+ and Python 3 (for validation only):

```bash
./build.sh          # validates data/, builds dist/TagTrain.exe + a Linux test binary
```

Curriculum content lives in `data/<level>/` as JSON; the format is documented
in `data/SCHEMA.md`. The exe embeds `data/` and `web/` at compile time.
