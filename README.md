# Klemmbaustein-Generator für Fusion

Ein Add-In, das klemmbaustein-kompatible Bauteile parametrisch erzeugt —
mit Live-Vorschau, Druckerkalibrierung und STL-Export.

**[→ Bebilderte Anleitung online lesen](https://wolfb63-del.github.io/Klemmbaustein-Generator/)**
· [Ausführliche Anleitung als Text](ANLEITUNG.md)

---

## Was es kann

**Vierzehn Bauteiltypen**, alle aus demselben 8-mm-Raster abgeleitet:

| Typ | Höhe | Besonderheit |
|---|---|---|
| Stein | 9,60 mm | der Standardstein |
| Halbstein | 4,80 mm | zwei ergeben einen Stein |
| Platte | 3,20 mm | drei ergeben einen Stein |
| Fliese | 3,20 mm | ohne Noppen |
| Jumper-Platte | 3,20 mm | Noppen um ein halbes Raster versetzt |
| Technic-Stein | 9,60 mm | Querbohrungen, wahlweise Rundloch oder Achskreuz |
| Technic-Lochbalken | 9,60 mm | Querbohrungen ohne Noppen |
| Schrägstein | 9,60 mm | Winkel ergibt sich aus der Länge der Schräge |
| Schrägstein umgekehrt | 9,60 mm | Keil an der Unterseite, oben alle Noppen |
| Eckstein | 9,60 mm | L-Form mit einstellbarer Schenkelbreite |
| Rundstein | 9,60 mm | runder Grundriss |
| Rundplatte | 3,20 mm | flache Fassung des Rundsteins |
| Rundfliese | 3,20 mm | rund und ohne Noppen |
| Grundplatte | 1,60 mm | massiv, klemmt nur von oben |

Dazu:

- **Kanten brechen** — Fase oder Radius, getrennt für Einführkante unten,
  Noppenoberkante und Außenecken. Vorgabe überall 0.
- **Druckerkalibrierung** — Soll/Ist-Messwerte je Achse statt Prozentrechnerei,
  plus ein absolutes Aufmaß für den konstanten Düsenfehler.
- **Live-Vorschau**, Serienbetrieb und **STL-Export** mit sprechenden Dateinamen.

## Installation

1. Diesen Ordner nach
   `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\Klemmbaustein\` kopieren
   (macOS: `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/`)

   > **Der Ordner muss `Klemmbaustein` heißen.** Lädst du hier über den grünen
   > **Code**-Knopf, heißt er nach dem Entpacken `Klemmbaustein-Generator-main`
   > — dann vorher umbenennen. Die ZIP-Datei unter **Releases** ist bereits
   > richtig benannt.
2. In Fusion: **Utilities → ADD-INS → Add-Ins → Klemmbaustein → Run**
3. Der Befehl liegt danach unter **SOLID → CREATE → Klemmbaustein-Generator**

Die Datei läuft auch als reines Script (Utilities → ADD-INS → Scripts).

## Der wichtigste Hinweis

Ein Klemmbaustein steht und fällt mit hundertstel Millimetern. Zwei Zahlen,
die man kennen sollte, bevor man kalibriert:

- **Rastermaß ist nicht Außenmaß.** Zwei Noppen sind 16,00 mm Raster, aber nur
  15,80 mm Außenmaß. Die 0,20 mm sind gewollt.
- **Die Klemmung ist tangential.** Noppe und Röhre berühren sich diagonal über
  5,657 mm mit 0,002 mm Rest. Jede Änderung an dieser Diagonalen wirkt sofort.

Beides steht ausführlich in der [Anleitung](ANLEITUNG.md).

## Kalibrierdatenbank

[`kalibrierdatenbank.json`](kalibrierdatenbank.json) sammelt gemessene
Kalibrierwerte aus echten Testdrucken, aufgeschlüsselt nach Material und
Nozzle-Durchmesser — ein Startpunkt, wenn du noch keinen eigenen Testdruck
vermessen hast. **Reines Nachschlage-Dokument:** Das Add-In liest die Datei
nicht selbst, die Werte trägst du von Hand in die Kalibrierfelder im Dialog
ein (siehe oben).

**Eigene Messwerte beisteuern, ohne Git zu benutzen:** [neues Issue mit dem
Formular "Kalibrierdatenbank-Beitrag"](../../issues/new/choose) anlegen -
die Werte werden von Hand in die Datei übernommen.

Wer mit Git vertraut ist, ergänzt stattdessen direkt einen Eintrag nach
diesem Muster per Pull Request —

```json
{
  "material": "PLA",
  "nozzle_mm": 0.4,
  "schrumpf_prozent": 0.24,
  "rund_mm": 0.23,
  "loch_mm": 0.00,
  "drucker": "Snapmaker U1",
  "datum": "2026-08-14"
}
```

Mehrere Einträge zur selben Material/Nozzle-Kombination bleiben bewusst
nebeneinander stehen statt gemittelt zu werden — die Streuung zeigt, wie
verlässlich ein Wert ist. Eine GitHub Action prüft jeden Pull Request gegen
die Wertegrenzen des Add-Ins (`werkzeuge/pruefe_kalibrierdatenbank.py`).

## Aufbau

```
Klemmbaustein.py                    Add-In: Geometrie, Dialog, Export
bausteinbasis.py                    gemeinsamer Unterbau (Einheiten, Skizzen, Kanten, STL)
Klemmbaustein.manifest              Add-In-Beschreibung für Fusion
kalibrierdatenbank.json             gemessene Kalibrierwerte aus der Community
resources/                          Symbole für die Schaltfläche
werkzeuge/
  zeichnen.py                       SVG-Zeichnungen aus den Konstruktionsdaten
  anleitung_bauen.py                erzeugt anleitung.html
  test_logik.py                     prüft die Rechenlogik ohne Fusion
  pruefe_kalibrierdatenbank.py      prüft kalibrierdatenbank.json gegen die Wertegrenzen
```

Die Bilder der Anleitung entstehen aus denselben Funktionen, die auch die
Geometrie in Fusion bauen. Neu erzeugen:

```bash
python werkzeuge/anleitung_bauen.py
```

## Prüfen ohne Fusion

Die Geometrie selbst braucht Fusion, die Rechenlogik dahinter nicht. Rund 150
Prüfungen decken Kalibrierfaktoren, Grenzen, Noppenraster, Dateinamen und
Infotexte ab — die Fusion-API wird dafür durch einen Stub ersetzt:

```bash
python werkzeuge/test_logik.py
```

## Rechtliches

Dieses Projekt ist ein unabhängiges, privates und unentgeltliches Werkzeug.
Es steht in keiner Verbindung zur LEGO Gruppe und wird von ihr weder
gesponsert noch autorisiert oder unterstützt. LEGO® ist eine eingetragene
Marke der LEGO Gruppe; die Nennung dient allein der Beschreibung der
Kompatibilität.

Alle Maße basieren auf frei verfügbaren, gemessenen Nennmaßen des seit
Jahrzehnten patentfreien Klemmbaustein-Rasters.

© 2026 Berthold Wolf. Lizenziert unter der MIT-Lizenz — siehe
[LICENSE](LICENSE). Die Nutzung erfolgt auf eigene Gefahr; eine Gewähr für
Maßhaltigkeit, Eignung oder Druckergebnisse wird nicht übernommen.
