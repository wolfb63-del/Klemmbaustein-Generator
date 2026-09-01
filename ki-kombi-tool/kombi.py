# -*- coding: utf-8 -*-
"""
kombi - schickt eine Anfrage an Claude und ChatGPT und stellt beide
Antworten nebeneinander
=====================================================================

Eigenstaendiges Kommandozeilen-Tool, unabhaengig vom eigentlichen
Klemmbaustein-Generator. Zwei Anwendungsfaelle:

  1. Beide Antworten einfach nebeneinander anzeigen (Standard).
  2. Zusaetzlich eine der beiden KIs die andere Antwort gegenlesen und
     zusammenfassen lassen (--vergleich).

Benoetigt die Pakete "anthropic" und "openai" sowie die
Umgebungsvariablen ANTHROPIC_API_KEY und OPENAI_API_KEY.
"""

import argparse
import os
import sys


def frage_claude(prompt: str, model: str) -> str:
    """Schickt prompt an die Anthropic-API und gibt die Antwort als Text zurueck."""
    try:
        import anthropic
    except ImportError:
        sys.exit("Paket 'anthropic' fehlt. Installieren mit: pip install anthropic")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("Umgebungsvariable ANTHROPIC_API_KEY ist nicht gesetzt.")

    client = anthropic.Anthropic(api_key=api_key)
    antwort = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in antwort.content if block.type == "text")


def frage_chatgpt(prompt: str, model: str) -> str:
    """Schickt prompt an die OpenAI-API und gibt die Antwort als Text zurueck."""
    try:
        import openai
    except ImportError:
        sys.exit("Paket 'openai' fehlt. Installieren mit: pip install openai")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        sys.exit("Umgebungsvariable OPENAI_API_KEY ist nicht gesetzt.")

    client = openai.OpenAI(api_key=api_key)
    antwort = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return antwort.choices[0].message.content


def vergleiche(prompt: str, antwort_claude: str, antwort_chatgpt: str, claude_model: str) -> str:
    """Laesst Claude die beiden Antworten gegenlesen und zusammenfassen."""
    vergleichs_prompt = (
        f"Urspruengliche Frage:\n{prompt}\n\n"
        f"Antwort von Claude:\n{antwort_claude}\n\n"
        f"Antwort von ChatGPT:\n{antwort_chatgpt}\n\n"
        "Vergleiche beide Antworten kurz: Wo stimmen sie ueberein, wo "
        "widersprechen sie sich, und welche ist fuer die Frage hilfreicher?"
    )
    return frage_claude(vergleichs_prompt, claude_model)


def main():
    parser = argparse.ArgumentParser(
        description="Schickt eine Anfrage an Claude und ChatGPT und zeigt beide Antworten."
    )
    parser.add_argument("prompt", help="Die Frage bzw. Anweisung fuer beide KIs.")
    parser.add_argument(
        "--claude-model", default="claude-haiku-4-5",
        help="Anthropic-Modell (Standard: claude-haiku-4-5, das guenstigste Claude-Modell).",
    )
    parser.add_argument(
        "--chatgpt-model", default="gpt-4o-mini",
        help="OpenAI-Modell (Standard: gpt-4o-mini, das guenstigste ChatGPT-Modell).",
    )
    parser.add_argument(
        "--vergleich", action="store_true",
        help="Laesst Claude beide Antworten zusaetzlich gegenlesen und zusammenfassen.",
    )
    args = parser.parse_args()

    antwort_claude = frage_claude(args.prompt, args.claude_model)
    antwort_chatgpt = frage_chatgpt(args.prompt, args.chatgpt_model)

    print("=" * 70)
    print(f"Claude ({args.claude_model})")
    print("=" * 70)
    print(antwort_claude.strip())
    print()
    print("=" * 70)
    print(f"ChatGPT ({args.chatgpt_model})")
    print("=" * 70)
    print(antwort_chatgpt.strip())

    if args.vergleich:
        fazit = vergleiche(args.prompt, antwort_claude, antwort_chatgpt, args.claude_model)
        print()
        print("=" * 70)
        print("Vergleich (von Claude erstellt)")
        print("=" * 70)
        print(fazit.strip())


if __name__ == "__main__":
    main()
