#!/usr/bin/env bash
# Smoke-Test fuer das ki-kombi-tool-CLI: baut das Paket in einem
# frischen venv, installiert es und prueft alle Pfade, die ohne echte
# API-Keys (kostenlos, deterministisch) exercierbar sind.
#
# Aufruf (von <unit>/ = ki-kombi-tool/):
#   bash .claude/skills/run-ki-kombi-tool/smoke.sh
#
# Fuer einen echten End-to-End-Lauf mit echten API-Antworten siehe
# "Voller Lauf" in SKILL.md - das braucht echte ANTHROPIC_API_KEY /
# OPENAI_API_KEY und verursacht Kosten, daher NICHT Teil dieses Smoke-Tests.

set -euo pipefail

UNIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
VENV_DIR="$(mktemp -d)/kombi-smoke-venv"

cleanup() { rm -rf "$VENV_DIR"; }
trap cleanup EXIT

echo "== 1) Paket in frischem venv installieren =="
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --quiet "$UNIT_DIR"
KOMBI="$VENV_DIR/bin/kombi"

echo "== 2) 'kombi --help' liefert Usage und exit 0 =="
"$KOMBI" --help >/tmp/kombi-smoke-help.txt
grep -q "usage: kombi" /tmp/kombi-smoke-help.txt
echo "OK"

echo "== 3) Ohne ANTHROPIC_API_KEY: klare Fehlermeldung, exit 1 =="
set +e
OUT=$(env -u ANTHROPIC_API_KEY -u OPENAI_API_KEY "$KOMBI" "Testfrage" 2>&1)
CODE=$?
set -e
if [ "$CODE" -ne 1 ] || ! echo "$OUT" | grep -q "ANTHROPIC_API_KEY ist nicht gesetzt"; then
  echo "FEHLGESCHLAGEN: erwartete Fehlermeldung zu ANTHROPIC_API_KEY nicht gefunden"
  echo "$OUT"
  exit 1
fi
echo "OK"

echo "== 4) Mit ungueltigem ANTHROPIC_API_KEY: Anthropic-API meldet 401 =="
set +e
OUT=$(env -u OPENAI_API_KEY ANTHROPIC_API_KEY=dummy-key "$KOMBI" "Testfrage" 2>&1)
CODE=$?
set -e
if [ "$CODE" -eq 0 ] || ! echo "$OUT" | grep -q "authentication_error"; then
  echo "FEHLGESCHLAGEN: erwartete 401/authentication_error von der Anthropic-API nicht gefunden"
  echo "$OUT"
  exit 1
fi
echo "OK (Netzwerkpfad zur Anthropic-API bestaetigt erreichbar)"

echo
echo "Alle Smoke-Checks erfolgreich."
