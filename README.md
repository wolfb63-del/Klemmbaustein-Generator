# Klemmbaustein-Generator für Fusion

Ein Add-In, das klemmbaustein-kompatible Bauteile parametrisch erzeugt —
mit Live-Vorschau, Druckerkalibrierung und STL-Export.

**[→ Bebilderte Anleitung](anleitung.html)** (im Browser öffnen)
· [Ausführliche Anleitung als Text](ANLEITUNG.md)

---

## Was es kann

**Elf Bauteiltypen**, alle aus demselben 8-mm-Raster abgeleitet:

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
| Eckstein | 9,60 mm | L-Form mit einstellbarer Schenkelbreite |
| Rundstein | 9,60 mm | runder Grundriss |
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

## Aufbau

```
Klemmbaustein.py        Add-In: Geometrie, Dialog, Export
bausteinbasis.py        gemeinsamer Unterbau (Einheiten, Skizzen, Kanten, STL)
Klemmbaustein.manifest  Add-In-Beschreibung für Fusion
resources/              Symbole für die Schaltfläche
werkzeuge/
  zeichnen.py           SVG-Zeichnungen aus den Konstruktionsdaten
  anleitung_bauen.py    erzeugt anleitung.html
  test_logik.py         prüft die Rechenlogik ohne Fusion
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
