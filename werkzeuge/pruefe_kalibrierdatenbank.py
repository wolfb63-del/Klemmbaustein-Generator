# -*- coding: utf-8 -*-
"""Prueft kalibrierdatenbank.json gegen die Wertegrenzen des Add-Ins.

Community-Eintraege koennen Tippfehler oder unplausible Messungen enthalten
(eine Kommastelle verrutscht, Prozent statt mm eingetragen). Diese Pruefung
lehnt sich bewusst nicht an eigene, doppelt gepflegte Grenzwerte an, sondern
importiert FAKTOR_MIN/FAKTOR_MAX/MAX_RUND direkt aus Klemmbaustein.py - liefe
sie an einer eigenen Kopie der Grenzen vorbei, faende eine spaetere Aenderung
dort keinen Widerhall hier.

Exit-Code 1 bei jedem Befund, 0 wenn alle Eintraege plausibel sind. Gedacht
fuer eine GitHub Action bei jedem Pull Request auf diese Datei.
"""

import json
import os
import re
import sys

HIER = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

from fusion_stub import stub_adsk   # noqa: E402

stub_adsk()
sys.path.insert(0, HIER)
import Klemmbaustein as K   # noqa: E402

DATEI = os.path.join(HIER, 'kalibrierdatenbank.json')
DATUM_MUSTER = re.compile(r'^\d{4}-\d{2}-\d{2}$')
PFLICHTFELDER = ('material', 'nozzle_mm', 'schrumpf_prozent', 'rund_mm',
                  'loch_mm', 'drucker', 'datum')


def _faktor_aus_prozent(prozent):
    """Dieselbe Umrechnung wie _profil_uebernehmen in Klemmbaustein.py."""
    if abs(prozent) <= 1e-9:
        return 1.0
    return 1.0 / (1.0 - prozent / 100.0)


def pruefe_eintrag(nr, eintrag):
    fehler = []

    for feld in PFLICHTFELDER:
        if feld not in eintrag:
            fehler.append('Feld "{}" fehlt'.format(feld))
    if fehler:
        return fehler   # Rest ergibt ohne die Felder keinen Sinn.

    if not str(eintrag['material']).strip():
        fehler.append('material ist leer')
    if not str(eintrag['drucker']).strip():
        fehler.append('drucker ist leer')
    if not DATUM_MUSTER.match(str(eintrag['datum'])):
        fehler.append('datum "{}" ist kein YYYY-MM-DD'.format(eintrag['datum']))

    nozzle = eintrag['nozzle_mm']
    if not (0.0 < nozzle <= 2.0):
        fehler.append('nozzle_mm {} liegt ausserhalb 0-2 mm'.format(nozzle))

    faktor = _faktor_aus_prozent(eintrag['schrumpf_prozent'])
    if not (K.FAKTOR_MIN <= faktor <= K.FAKTOR_MAX):
        fehler.append(
            'schrumpf_prozent {} ergibt Faktor {:.5f}, ausserhalb '
            '[{}, {}] - wuerde im Add-In stillschweigend gekappt'.format(
                eintrag['schrumpf_prozent'], faktor, K.FAKTOR_MIN, K.FAKTOR_MAX))

    for feld in ('rund_mm', 'loch_mm'):
        wert = eintrag[feld]
        if not (0.0 <= wert <= K.MAX_RUND):
            fehler.append('{} {} liegt ausserhalb [0.0, {}]'.format(
                feld, wert, K.MAX_RUND))

    return fehler


def main():
    with open(DATEI, encoding='utf-8') as f:
        daten = json.load(f)

    eintraege = daten.get('eintraege', [])
    if not eintraege:
        print('kalibrierdatenbank.json enthaelt keine Eintraege.')
        return 1

    gesamt_fehler = 0
    for nr, eintrag in enumerate(eintraege, start=1):
        fehler = pruefe_eintrag(nr, eintrag)
        bezeichner = '{} / {} mm ({})'.format(
            eintrag.get('material', '?'), eintrag.get('nozzle_mm', '?'),
            eintrag.get('drucker', '?'))
        if fehler:
            gesamt_fehler += len(fehler)
            print('FEHLER  Eintrag {} [{}]:'.format(nr, bezeichner))
            for f in fehler:
                print('        - {}'.format(f))
        else:
            print('OK      Eintrag {} [{}]'.format(nr, bezeichner))

    print('\n{} Eintraege, {} Befund(e).'.format(len(eintraege), gesamt_fehler))
    return 1 if gesamt_fehler else 0


if __name__ == '__main__':
    sys.exit(main())
