# KI-Kombi-Tool

Kommandozeilen-Tool, das eine Frage gleichzeitig an Claude (Anthropic) und
ChatGPT (OpenAI) schickt und beide Antworten nebeneinander anzeigt.
Optional lässt es Claude beide Antworten gegenlesen und zusammenfassen.

Eigenständig und unabhängig vom Klemmbaustein-Generator — reines
Hilfswerkzeug in diesem Repo.

## Installation

Global als Kommando `kombi` installieren (in einer virtuellen Umgebung
oder mit `pip install --user`):

```bash
pip install ki-kombi-tool/
```

Damit steht `kombi` danach von jedem Verzeichnis aus zur Verfügung — kein
`python ki-kombi-tool/kombi.py` mehr nötig. Für Entwicklung mit Live-Reload
statt `pip install ki-kombi-tool/` besser `pip install -e ki-kombi-tool/`
verwenden.

## Einrichtung

Zwei API-Keys werden als Umgebungsvariablen erwartet:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
```

## Verwendung

```bash
kombi "Erkläre kurz, was ein Klemmbaustein ist."
```

Mit Vergleich (Claude liest beide Antworten gegen):

```bash
kombi "Erkläre kurz, was ein Klemmbaustein ist." --vergleich
```

Andere Modelle wählen:

```bash
kombi "Frage" --claude-model claude-opus-4-1 --chatgpt-model gpt-4o-mini
```

Ohne Installation geht es weiterhin auch direkt per Skriptaufruf:

```bash
python ki-kombi-tool/kombi.py "Frage"
```

## Optionen

| Option | Bedeutung |
|---|---|
| `--claude-model` | Anthropic-Modell (Standard: `claude-sonnet-4-5`) |
| `--chatgpt-model` | OpenAI-Modell (Standard: `gpt-4o`) |
| `--vergleich` | Lässt Claude beide Antworten zusätzlich gegenlesen und zusammenfassen |
