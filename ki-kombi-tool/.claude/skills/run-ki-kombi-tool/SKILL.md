---
name: run-ki-kombi-tool
description: Build, install, run, and smoke-test the ki-kombi-tool CLI (the "kombi" command that queries Claude and ChatGPT together). Use when asked to run, launch, install, build, test, or smoke-test the ki-kombi-tool / kombi CLI.
---

Paths below are relative to `<unit>/` = `ki-kombi-tool/` (this skill's
grandparent directory), not to this skill directory.

`ki-kombi-tool` is a small standalone Python CLI (`kombi`, entry point in
`pyproject.toml` -> `kombi:main`) that sends one prompt to both the
Anthropic and OpenAI APIs and prints both answers. It has no GUI/server —
it's driven directly via the installed `kombi` command or by importing
`kombi.py`.

## Run (agent path) — smoke test

The committed driver installs the package into a throwaway venv and
exercises every path that doesn't require real, paid API keys:

```bash
cd ki-kombi-tool
bash .claude/skills/run-ki-kombi-tool/smoke.sh
```

Verified in this container — ran clean:

```
== 1) Paket in frischem venv installieren ==
== 2) 'kombi --help' liefert Usage und exit 0 ==
OK
== 3) Ohne ANTHROPIC_API_KEY: klare Fehlermeldung, exit 1 ==
OK
== 4) Mit ungueltigem ANTHROPIC_API_KEY: Anthropic-API meldet 401 ==
OK (Netzwerkpfad zur Anthropic-API bestaetigt erreichbar)

Alle Smoke-Checks erfolgreich.
```

Step 4 proves the container can actually reach `api.anthropic.com`
through the sandbox's outbound proxy (a real 401 comes back for a fake
key) — so the only thing missing for a full run is real credentials,
not network access.

## Prerequisites

Nothing beyond Python 3.9+ and `pip`. No `apt-get` packages were needed —
confirmed by installing from scratch in this container.

## Build / install

```bash
cd ki-kombi-tool
python3 -m venv /tmp/kombi-venv
/tmp/kombi-venv/bin/pip install .        # or: pip install -e . for dev
```

This installs `anthropic` and `openai` (declared in `pyproject.toml`)
and registers the `kombi` console script on the venv's `bin/`.

## Direct invocation (no install)

```bash
python3 ki-kombi-tool/kombi.py "Testfrage"
```

Same code path as the installed command — useful when you only want to
exercise `frage_claude` / `frage_chatgpt` / `vergleiche` without
installing, e.g. from a Python REPL:

```python
import sys; sys.path.insert(0, "ki-kombi-tool")
from kombi import frage_claude, frage_chatgpt, vergleiche
```

## Full run (real API calls — costs money, not run in this container)

Requires real keys:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
kombi "Erkläre kurz, was ein Klemmbaustein ist." --vergleich
```

Not exercised here — no real keys are available in this container, and
each call bills the account. The smoke test above stops short of this
deliberately (see Gotchas).

## Gotchas

- **Missing-key check only covers `ANTHROPIC_API_KEY`.** `frage_claude`
  runs before `frage_chatgpt` (see `main()` in `kombi.py`), so a run
  with `ANTHROPIC_API_KEY` set but `OPENAI_API_KEY` missing will make a
  real (billed) Claude call before failing on the missing OpenAI key.
  Keep this in mind when smoke-testing with a real Anthropic key —
  either set both keys or expect a real Claude API call to fire.
- **`frage_claude` raises an unhandled `anthropic.AuthenticationError`
  traceback** on a bad/dummy key instead of a clean `sys.exit` message
  (unlike the missing-env-var case, which *is* clean). The smoke test
  treats this traceback as expected output (step 4) — don't mistake it
  for the driver breaking.
- **`pip install .` (non-editable) copies `kombi.py` into the venv's
  `site-packages`.** Edits to the working tree after installing
  non-editably won't be picked up — use `pip install -e .` while
  iterating on `kombi.py`.
- Installing leaves `build/` and `*.egg-info/` behind if you run
  `pip install .` from inside `ki-kombi-tool/` directly (rather than
  from a venv against the path as shown above) — both are gitignored
  already, but `git status` after a manual `pip install .` here is
  worth a glance.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Paket 'anthropic' fehlt. Installieren mit: pip install anthropic` | Running `kombi.py` directly with `python3` in an environment where the package was never installed | `pip install .` (or `-e .`) from `ki-kombi-tool/`, or `pip install anthropic openai` directly |
| `Umgebungsvariable ANTHROPIC_API_KEY ist nicht gesetzt.` (exit 1) | No `ANTHROPIC_API_KEY` in the environment | `export ANTHROPIC_API_KEY=...` (checked before `OPENAI_API_KEY`, so this fires first even if the OpenAI key is also missing) |
| `anthropic.AuthenticationError: ... invalid x-api-key` (raw traceback, exit 1) | Key is set but not a real/valid Anthropic key | Use a real key from the Anthropic console |
