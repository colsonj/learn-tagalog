# TagTrain curriculum content schema

Each CEFR level lives in `data/<level>/` (`a1`, `a2`, `b1`, `b2`) and contains:

- `meta.json` — level metadata
- `unit01.json` … `unitNN.json` — one file per unit (zero-padded two digits)
- `exam.json` — the milestone exam for the level

All files are strict JSON (no comments, no trailing commas), UTF-8.
Tagalog text uses standard modern orthography, no diacritics required.
Keep Taglish out of A1/A2 model sentences; B1/B2 may *discuss* register and
colloquial forms explicitly.

## meta.json

```json
{
  "level": "A1",
  "title": "Foundations",
  "description": "One-paragraph description of what the learner can do after this level.",
  "canDo": ["CEFR-style can-do statement", "..."],
  "units": 10
}
```

## unitNN.json

```json
{
  "id": "a1-u01",
  "title": "Greetings and introductions",
  "objectives": ["...", "..."],
  "grammar": [
    {
      "title": "The polite particle po / opo",
      "explanation": "Plain-text explanation, a few short paragraphs. May use \\n\\n between paragraphs. Written for an English-speaking self-learner. No markdown syntax.",
      "examples": [ {"tl": "Salamat po.", "en": "Thank you (polite)."} ]
    }
  ],
  "vocab": [
    {
      "tl": "magandang umaga",
      "en": "good morning",
      "pos": "phrase",
      "note": "optional usage note",
      "example": {"tl": "Magandang umaga po sa inyong lahat.", "en": "Good morning to you all."}
    }
  ],
  "dialogue": {
    "title": "At the sari-sari store",
    "context": "One line of scene-setting in English.",
    "lines": [ {"speaker": "Ana", "tl": "Magandang umaga po!", "en": "Good morning!"} ]
  },
  "exercises": [ Exercise, Exercise, ... ]
}
```

- `grammar`: 2–4 points per unit. Explanations must actually teach (contrast with
  English, show the pattern, warn about common mistakes).
- `vocab`: 22–35 items per unit for A1/A2, 25–40 for B1/B2. Every item needs an
  example sentence. `pos` is one of: noun, verb, adjective, adverb, pronoun,
  particle, phrase, conjunction, interjection, number.
  For verbs, `tl` is the citation form actually taught in that unit (e.g.
  "kumain (um)") and the `note` should give the aspect forms once aspect has
  been introduced (e.g. "kumain, kumakain, kakain").
- `dialogue`: 8–16 lines, natural, uses this unit's grammar and vocab.
- `exercises`: 10–14 per unit, mixed types, ordered easy → hard.

### Reading passages (B1/B2 only)

B1 and B2 units add a `reading` field between `dialogue` and `exercises`:

```json
"reading": {
  "title": "...",
  "tl": "A passage of 80–150 words (B1) / 150–250 words (B2) in Tagalog. \\n\\n between paragraphs.",
  "en": "Full English translation.",
  "gloss": [ {"tl": "hard word/phrase in the passage", "en": "meaning"} ]
}
```

## Exercise objects

Four types. Every exercise has an `explain` field: one or two sentences shown
after answering, explaining why the answer is right (not just restating it).

```json
{"type": "mcq", "prompt": "Question text (may contain Tagalog).",
 "choices": ["a", "b", "c", "d"], "answer": 1, "explain": "..."}

{"type": "fill", "prompt": "Kumain ___ ng mansanas.",
 "answer": "ako", "accept": ["ako"], "hint": "optional hint", "explain": "..."}

{"type": "translate", "direction": "en2tl",
 "prompt": "I want to eat.", "answer": "Gusto kong kumain.",
 "accept": ["Gusto kong kumain", "Gusto ko kumain"], "explain": "..."}

{"type": "listen", "tl": "Sentence to be spoken aloud by TTS.",
 "prompt": "What does the sentence mean?",
 "choices": ["a", "b", "c", "d"], "answer": 0, "explain": "..."}
```

- `answer` for mcq/listen is a 0-based index into `choices`.
- `translate` also supports `"direction": "tl2en"`.
- `accept` lists all acceptable answers; matching is case/punctuation-insensitive.
  Include common legitimate variants (word order, optional po, din/rin,
  contracted forms) so learners aren't marked wrong unfairly.

## exam.json

```json
{
  "passPct": 75,
  "timeLimitMin": 40,
  "description": "One paragraph telling the learner what this exam certifies, phrased against the CEFR level.",
  "questions": [ Exercise, ... ]
}
```

- 36–44 questions drawing on the whole level, all four exercise types
  represented, at least 6 `listen` questions, weighted toward the level's core
  grammar. Order roughly easy → hard. B1/B2 exams should include 2–3 short
  reading passages delivered as `mcq` items whose `prompt` contains the passage
  followed by the question.
