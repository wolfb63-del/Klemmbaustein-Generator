# KI-Kombi-Tool

Kommandozeilen-Tool, das eine Frage gleichzeitig an Claude (Anthropic) und
ChatGPT (OpenAI) schickt und beide Antworten nebeneinander anzeigt.
Optional lässt es Claude beide Antworten gegenlesen und zusammenfassen.

Eigenständig und unabhängig vom Klemmbaustein-Generator — reines
Hilfswerkzeug in diesem Repo.

## Installation

```bash
pip install -r ki-kombi-tool/requirements.txt
```

## Einrichtung

Zwei API-Keys werden als Umgebungsvariablen erwartet:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
```

## Verwendung

```bash
python ki-kombi-tool/kombi.py "Erkläre kurz, was ein Klemmbaustein ist."
```

Mit Vergleich (Claude liest beide Antworten gegen):

```bash
python ki-kombi-tool/kombi.py "Erkläre kurz, was ein Klemmbaustein ist." --vergleich
```

Andere Modelle wählen:

```bash
python ki-kombi-tool/kombi.py "Frage" --claude-model claude-opus-4-1 --chatgpt-model gpt-4o-mini
```

## Optionen

| Option | Bedeutung |
|---|---|
| `--claude-model` | Anthropic-Modell (Standard: `claude-sonnet-4-5`) |
| `--chatgpt-model` | OpenAI-Modell (Standard: `gpt-4o`) |
| `--vergleich` | Lässt Claude beide Antworten zusätzlich gegenlesen und zusammenfassen |
