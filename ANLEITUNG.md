# Klemmbaustein-Generator für Fusion — Anleitung

Ein kostenloses Add-In für Autodesk Fusion, das klemmbaustein-kompatible Bauteile
parametrisch erzeugt: **Stein, Platte, Fliese und Technic-Stein** in beliebiger
Größe, mit Live-Vorschau, Druckprofilen und direktem STL-Export.

Kein Modellieren, kein Skizzieren: Typ wählen, Länge × Breite eintippen,
"Erzeugen" — fertig ist der druckbare Körper.

---

## 1. Was das Add-In kann

| Funktion | Details |
|---|---|
| Bauteiltypen | Stein (9,6 mm hoch), Platte (3,2 mm), Fliese (3,2 mm, ohne Noppen), Technic-Stein (Stein mit Querbohrungen) |
| Größe | 1 × 1 bis 32 × 32 Noppen, frei kombinierbar |
| Unterseite | Ab 2×2 echte Röhren, bei 1×N schmale Stege — wie beim Original |
| Live-Vorschau | Das Teil baut sich beim Tippen im Viewport auf |
| Druckprofile | PETG, PLA, PLA fein, Resin, "Locker" — jeweils mit passenden Spielmaßen |
| Feinjustage | Klemmspiel-Regler von −0,25 bis +0,25 mm |
| Druckerkompensation | Schrumpf und Rundungsfehler des eigenen Druckers vorhalten |
| Serienbetrieb | Dialog bleibt offen, Steine werden automatisch nebeneinander abgelegt |
| STL-Export | Binäres STL direkt beim Erzeugen, mit sprechendem Dateinamen |
| Merkfunktion | Alle Einstellungen überleben den Fusion-Neustart |

**Maße** (Nennmaße des Klemmbaustein-Rasters): Raster 8,0 mm · Noppe ⌀ 4,8 × 1,8 mm ·
Röhre außen ⌀ 6,51 mm · Wand 1,2 mm · Technic-Bohrung ⌀ 4,8 mm auf 5,8 mm Achshöhe.

---

## 2. Voraussetzungen

* **Autodesk Fusion** (früher Fusion 360), Windows oder macOS.
  Die kostenlose Hobby-/Personal-Lizenz reicht vollständig aus.
* Python muss **nicht** installiert werden — Fusion bringt seine eigene Python-Laufzeit mit.
* Ein 3D-Drucker (oder ein Slicer) für den letzten Schritt. Für reines Konstruieren
  in Fusion braucht es nichts weiter.

---

## 3. Installation

Im Paket liegen drei Dateien, die zusammengehören — `bausteinbasis.py` muss
zwingend mit, sonst startet das Add-In nicht:

```
Klemmbaustein\
├── Klemmbaustein.py          ← das Add-In
├── Klemmbaustein.manifest    ← sagt Fusion, dass es ein Add-In ist
├── bausteinbasis.py          ← gemeinsamer Unterbau, muss mitkopiert werden
├── ANLEITUNG.md
└── resources\                ← Symbole für den Button (optional)
```

> **Wichtig:** Der **Ordner muss `Klemmbaustein` heißen** — genau wie die
> `.py`- und die `.manifest`-Datei. Fusion findet das Add-In sonst nicht.

### Weg A — Ordner an die richtige Stelle kopieren (empfohlen)

1. ZIP entpacken. Du erhältst den Ordner `Klemmbaustein`.

   > **Wenn du über den grünen „Code"-Knopf bei GitHub geladen hast**, heißt
   > der Ordner stattdessen `Klemmbaustein-Generator-main`. **Benenne ihn in
   > `Klemmbaustein` um**, sonst startet das Add-In nicht. Wer das umgehen
   > will, lädt die ZIP-Datei unter *Releases* — die ist schon richtig
   > benannt.

2. Diesen Ordner **komplett** kopieren nach:

   **Windows**
   ```
   %APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\
   ```
   (In den Explorer-Adressbalken einfach `%APPDATA%` eintippen und weiterklicken.)

   **macOS**
   ```
   ~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/
   ```
   (Im Finder: `Gehe zu` → `Gehe zum Ordner…` → Pfad einfügen. Der Ordner
   `Library` ist standardmäßig ausgeblendet.)

   Existiert der Ordner `AddIns` noch nicht, einfach anlegen.
3. Fusion **starten bzw. neu starten**.

### Weg B — über den Fusion-Dialog hinzufügen

1. Fusion öffnen → Reiter **UTILITIES** → **ADD-INS** → **Scripts and Add-Ins…**
   (Tastenkürzel: `Shift` + `S`)
2. Reiter **Add-Ins** wählen → auf das **grüne `+`** neben "My Add-Ins" klicken.
3. Den entpackten Ordner `Klemmbaustein` auswählen.

### Add-In starten

1. `Shift` + `S` → Reiter **Add-Ins** → Eintrag **Klemmbaustein** markieren.
2. Häkchen bei **"Run on Startup"** setzen (dann ist es nach jedem Fusion-Start sofort da).
3. Auf **Run** klicken.

Der Dialog öffnet sich sofort. Ab jetzt liegt der Befehl dauerhaft unter:

> **SOLID → CREATE → Klemmbaustein-Generator**

Er ist zusätzlich als Symbol direkt in der Create-Leiste angeheftet.

---

## 4. Der erste Baustein in 30 Sekunden

1. In Fusion ein **neues Design** anlegen (`Datei → Neues Design`).
2. **SOLID → CREATE → Klemmbaustein-Generator**.
3. Bauteiltyp `Stein`, Länge `4`, Breite `2`.
4. Druckprofil passend zum Material wählen.
5. Auf **Erzeugen** klicken.

Der Stein liegt als eigene Komponente im Browser (`Stein 4x2`), sauber benannt und
mit vollständiger Feature-Historie — du kannst also jederzeit weiterkonstruieren.

---

## 5. Der Dialog im Detail

### Bauteiltyp

| Typ | Höhe | Oberseite | Besonderheit |
|---|---|---|---|
| **Stein** | 9,6 mm | Noppen | der Standardstein |
| **Platte** | 3,2 mm | Noppen | flach, ein Drittel Steinhöhe |
| **Fliese** | 3,2 mm | glatt | ohne Noppen, für saubere Oberflächen |
| **Technic-Stein** | 9,6 mm | Noppen | zusätzlich ⌀ 4,8 mm Querbohrungen auf 5,8 mm Höhe, eine pro Noppenspalte |
| **Schrägstein** | 9,6 mm | teils Noppen | fällt zur Vorderkante auf Plattenhöhe ab |
| **Grundplatte** | 1,6 mm | Noppen | massiv, klemmt nur von oben |
| **Jumper-Platte** | 3,2 mm | Noppen | Noppen um ein **halbes Raster (4 mm)** versetzt |
| **Halbstein** | 4,8 mm | Noppen | halbe Steinhöhe — zwei ergeben einen Stein |
| **Technic-Lochbalken** | 9,6 mm | glatt | Querbohrungen ohne Noppen |
| **Eckstein** | 9,6 mm | Noppen | L-Form mit einstellbarer Schenkelbreite |
| **Rundstein** | 9,6 mm | Noppen | runder Grundriss, Breite folgt der Länge |

### Halbstein

Halbe Steinhöhe (4,8 mm). Zwei Halbsteine ergeben genau einen Stein, drei
Platten ebenfalls — damit lassen sich Höhensprünge bauen, die mit Steinen
und Platten allein nicht aufgehen.

### Technic-Lochbalken

Ein Technic-Stein ohne Noppen: glatte Oberseite, Querbohrungen, Klemmung nur
an der Unterseite. Praktisch überall dort, wo etwas anschließen soll, ohne
dass oben Noppen im Weg sind.

### Eckstein

Eine L-Form aus zwei Schenkeln: einer läuft über die volle Länge, der andere
über die volle Breite. Die **Schenkelbreite** legt fest, wie dick die beiden
Arme sind — höchstens eine Noppe weniger als die schmalere Seite, sonst wäre
es wieder ein Quader.

```
2×2, Schenkel 1:        4×4, Schenkel 2:
  ●                      ● ●
  ● ●                    ● ●
                         ● ● ● ●
                         ● ● ● ●
```

Röhren an der Unterseite entstehen nur dort, wo alle vier angrenzenden
Rasterfelder vorhanden sind — eine Röhre am Rand der Aussparung hinge sonst
halb in der Luft.

### Rundstein

Runder Grundriss. Die **Breite folgt zwangsläufig der Länge** (das Feld wird
ausgeblendet), denn zwei verschiedene Kantenlängen gäben eine Ellipse.

Noppen und Röhren, die zu weit über den runden Rand ragen würden, entfallen
automatisch. Ein knapper Überstand bleibt dagegen stehen und verschmilzt mit
der Zylinderwand — genau so sitzt auch das echte Teil:

| Größe | Noppen | Anmerkung |
|---|---|---|
| 2×2 rund | 4 | die Noppen liegen bündig am Rand |
| 4×4 rund | 12 | die vier Ecknoppen entfallen |

### Bohrung — nur bei Technic-Stein und Lochbalken

| Art | Wirkung |
|---|---|
| **Rundloch (Pin)** | ⌀ 4,8 mm — nimmt Pins auf, Achsen drehen frei |
| **Achskreuz** | 4,8 mm Spannweite, 1,8 mm Steg — hält die Achse formschlüssig |

Das Achskreuz bekommt **keine Kantenbrechung**: eine Fase an seinen zwölf
Ecken wäre kaum sauber druckbar.

### Jumper-Platte

Die Noppen sitzen nicht in den Feldmitten, sondern auf den **Rasterkreuzen
dazwischen**. Damit lässt sich alles Aufgesteckte um 4 mm versetzen — das
halbe Raster, an das man sonst nicht herankommt.

```
Platte 2×2:            Jumper 2×2:
  ●   ●                     ●
  ●   ●                  (mittig)
```

Die Zahl der Noppen ergibt sich aus der Größe: pro Achse eine weniger als
Rasterfelder — aber mindestens eine, denn bei einer Breite von einer Noppe
gibt es kein Kreuz, und die Noppe bleibt dort quer mittig.

| Größe | Noppen | entspricht |
|---|---|---|
| 1×2 | 1, genau in der Mitte | der Klassiker |
| 2×2 | 1, zentral | |
| 4×2 | 3, längs versetzt | |
| 3×3 | 4 | |
| 1×1 | 1 | = normale Platte, kein Versatz möglich |

> **Was passt darauf?** Ein 1×2-Teil greift die Jumper-Noppe mit seinem Steg —
> das hält. Eine **1×1-Platte klemmt dagegen nicht**: ihr Hohlraum ist 5,40 mm
> weit, die Noppe nur 4,80 mm dick. Dafür bräuchte es 1,50 mm Wandstärke statt
> der 1,20 mm aus dem Profil. Die Infozeile weist darauf hin, sobald du den Typ
> wählst.

### Schräge (Noppen) — nur beim Schrägstein

Über wie viele Noppen die Schräge abfällt. Der **Winkel ergibt sich daraus**
und wird in der Infozeile angezeigt:

| Schräge | Winkel |
|---|---|
| 1 Noppe | 38,7° |
| 2 Noppen | 21,8° |
| 3 Noppen | 14,9° |
| 4 Noppen | 11,3° |

Warum keine glatten 45° oder 33° wie im Handel? Weil die Schräge über **ganze
Noppen** laufen muss — sonst sitzen die verbleibenden Noppen der Oberseite
nicht mehr im Raster. Der Winkel ist deshalb das Ergebnis der Geometrie, nicht
die Vorgabe.

Unter der Schräge ist der Hohlraum flacher (2,2 mm statt 8,6 mm), damit über
ihm noch 1,0 mm Decke bleibt. Für die Noppe des darunterliegenden Steins
reicht das mit 0,4 mm Luft — der Stein klemmt also auch vorn.

Die Röhren in diesem Bereich sind genauso hoch wie dieser flache Hohlraum.
Auf voller Höhe würden sie oben durch die Schrägfläche stoßen und sie
aufrauen; geklemmt wird ohnehin nur an den obersten knapp zwei Millimetern
der Noppe, die kürzere Röhre hält also genauso.

### Länge / Breite (Noppen)

Anzahl der Noppen in X- bzw. Y-Richtung, 1 bis 32. Das Außenmaß ergibt sich
automatisch: `Noppen × 8 mm − 0,2 mm Spiel`. Ein 4×2-Stein misst also
31,8 × 15,8 mm.

Bei 1×N-Teilen (z. B. 1×6) entfallen die Röhren — dort sitzen stattdessen schmale
Stege an der Unterseite, genau wie beim Original.

### Druckprofil

Legt Spielmaße, Wandstärke und STL-Netzqualität in einem Rutsch fest:

| Profil | Gedacht für |
|---|---|
| **PETG (Snapmaker U1)** | PETG. Läuft an kleinen Features nach → mehr Spiel in den Löchern |
| **PETG (Snapmaker U1, kalibriert)** | dasselbe, aber mit Druckerkompensation aus einem echten Testdruck |
| **PLA (0,2 mm Schicht)** | der Alltagsfall |
| **PLA fein (0,1 mm Schicht)** | feine Schichten, engere Toleranzen |
| **Resin / SLA** | sehr maßhaltig, minimale Spielmaße |
| **Locker (leichtgängig)** | wenn Teile für Kinderhände leichter zu trennen sein sollen |

> Ein Profilwechsel setzt das Feld **Klemmspiel** automatisch auf den Vorgabewert
> des neuen Profils zurück.

### Klemmspiel

Das wichtigste Feld — hier stellst du ein, **wie fest die Steine halten**.

Der Wert ist ein Aufmaß auf Noppen und Stege:

* `0,00 mm` = Nennmaß. Noppe und Röhre berühren sich rechnerisch gerade eben
  (0,002 mm Rest) — exakt wie beim Original.
* **positiv** = Noppe dicker = **strammer**
* **negativ** = Noppe dünner = **leichtgängiger**

Sinnvoller Bereich: **−0,10 bis +0,10 mm**. Schon 0,05 mm sind deutlich spürbar.

Die Klemmkraft entsteht ausschließlich am Kontakt **Noppe ↔ Röhrenaußenseite**
(bzw. Noppe ↔ Steg bei 1×N-Teilen). Die Seitenwände haben konstruktiv 0,3 mm
Luft und klemmen bewusst nicht mit. Jede Verkleinerung der Noppe wirkt deshalb
1:1 als Spiel.

Bei PLA vorsichtig sein: die dünnen Röhren vertragen kaum Übermaß, sie reißen
eher als dass sie federn. Dort nicht über +0,05 mm gehen.

### Live-Vorschau

Zeigt das Ergebnis schon während der Eingabe. Bei sehr großen Steinen
(z. B. 32×32 = 1024 Noppen) zum Beschleunigen abschalten.

### Infozeile "Abmessungen"

Rechnet live mit und zeigt Außenmaß, Noppenzahl, Wandstärke und vor allem:

> **Klemmung:** x,xxx mm Luft am Kontakt (locker / Nennmass / stramm)

Das ist die ehrliche Bewertung deiner Einstellung, bevor du druckst.

**Achte auf die Raster-Zeile.** Sie verhindert den häufigsten Messfehler:

```
Außenmaß: 15,80 × 15,80 × 9,60 mm
Raster:   16,00 × 16,00 mm – das Außenmaß liegt konstruktiv 0,20 mm darunter
```

Ein 2×2-Stein ist **15,80 mm breit, nicht 16,00 mm**. Die 0,20 mm sind gewollt,
damit zwei Steine nebeneinander noch ins Raster passen. Wer gegen die 16,00
misst und die Differenz "wegkalibriert", zerstört genau dieses Spiel.

### Gruppe "Kanten brechen"

Bricht die scharfen Kanten, damit die Steine leichter zusammenfinden.
**Alle Werte stehen ab Werk auf 0** — die Geometrie ändert sich nur, wenn du
es willst.

* **Art** — *Fase (45 Grad)* oder *Radius*.
  Auf waagerechten Kanten ist die **Fase** die bessere Wahl: ein Radius wird
  dort beim Drucken zur Stufentreppe. Der Radius sieht dafür schöner aus.
* **Einführkante unten** — bricht Röhren, Stege und Technic-Bohrungen an der
  Unterseite. **Das ist die eigentliche Einführhilfe fürs Zusammenstecken.**
  Kostet nichts an Klemmkraft, weil der Hohlraum mit 8,6 mm viel tiefer ist
  als die 1,8 mm hohe Noppe. Empfehlung: **0,20–0,30 mm**.
* **Einführkante Noppe** — bricht die Oberkante der Noppe, damit sie in die
  Röhre findet. **Hier sparsam sein:** die Noppe ist nur 1,8 mm hoch, und
  genau über diese Höhe klemmt der Stein. Empfehlung: **0,20 mm**.

  | Fase | verlorene Klemmfläche |
  |------|----------------------|
  | 0,10 mm | 6 % |
  | 0,20 mm | 11 % |
  | 0,30 mm | 17 % ← ab hier warnt die Infozeile |
  | 0,40 mm | 22 % |

* **Eckradius außen** — verrundet die vier senkrechten Außenkanten. Rein
  optisch. **Vorsicht:** nebeneinandergesetzte Steine zeigen dann sichtbare
  Spalten an den Ecken; echte Steine sind hier scharfkantig.

> **Große Steine:** Ab etwa 8×8 lässt die Live-Vorschau die Kantenbrechung weg
> und zeigt das Teil scharfkantig — sonst müsste Fusion bei jedem Tastendruck
> tausende Kanten neu verrunden. Die Infozeile sagt Bescheid, wenn das greift.
> **"Erzeugen" bricht die Kanten trotzdem.**

Wenn eine Kantenbrechung nicht möglich war (Maß zu groß für die Geometrie),
steht das im Textkommando-Fenster — der Baustein wird trotzdem fertig gebaut,
nur eben mit scharfer Kante an dieser Stelle.

### Gruppe "Druckerkalibrierung"

Hier sagst du dem Add-In, was dein Drucker aus den Sollmaßen wirklich macht.
Du musst dafür **nichts in Prozent umrechnen** — du trägst einfach zwei Zahlen
ein, und das Add-In rechnet selbst:

```
X Sollmaß   31,80 mm     ← was herauskommen sollte (steht in der Infozeile)
X gemessen  31,73 mm     ← was dein Messschieber wirklich anzeigt
→ Ergebnis: 0,221 % Vorhalt
```

**Lässt du beide Felder einer Achse auf 0, bleibt diese Achse unverändert.**

* **X und Y koppeln** — nimmt deinen X-Wert auch für Y. Lass das an, solange du
  nicht wirklich beide Richtungen gemessen hast. Grund: Noppe und Röhre
  berühren sich **über Eck**, und dort ist nur 0,002 mm Platz. Behandelst du
  die beiden Richtungen unterschiedlich, müsste die Noppe oval werden, um noch
  zu passen — das kann sie nicht. Ab 0,15 % Unterschied warnt die Infozeile.
* **Rundungs-Aufmaß** — hier kommt der Filzstift-Fehler aus Abschnitt 6 hinein:
  ein fester Betrag, der auf Noppen, Stege und Röhrenaußenseiten draufkommt.

> **Warum es zwei Felder gibt** — weil es zwei Sorten Fehler gibt, die sich
> ganz unterschiedlich verhalten:
>
> | Sorte | Verhalten | Das richtige Feld |
> |-----------|-----------|----------|
> | **Schrumpf** (Pullover in der Wäsche) | wächst mit dem Maß: 31,73 statt 31,80 = 0,22 % | Soll / Gemessen |
> | **Düsenversatz** (dicker Filzstift) | immer derselbe Betrag: Noppe 4,56 statt 4,80 = −0,24 mm | Rundungs-Aufmaß |
>
> Beim Testdruck vom 03.08.2026 fehlten an der Noppe **0,24 mm** — und zwar als
> fester Betrag, nicht als Prozentwert. Genau dafür gibt es das zweite Feld.

**Miss möglichst an einem großen Teil** (8×2 oder größer). Bei einem kleinen
Stein fällt der feste Filzstift-Fehler stark ins Gewicht, und wenn du daraus
einen Prozentwert machst, liegt der bei großen Steinen weit daneben.

> **Die Höhe (Z) ist ein Sonderfall.** Sie lässt sich kaum über einen Faktor
> korrigieren, weil der Drucker in Schichten arbeitet — wie ein Stapel Papier.
> Du kannst nur ganze Blätter stapeln, keine halben. Wähle deshalb eine
> Schichthöhe, mit der **3,2 mm glatt aufgeht**: 0,10 / 0,16 / 0,20 / 0,32 mm.
> Bei 0,15 mm bräuchte eine Platte 21,33 Schichten — die gibt es nicht, also
> macht der Drucker 3,15 oder 3,30 mm daraus, und kein Faktor holt das zurück.

**Wechselst du das Druckprofil**, werden die Kalibrierfelder mit den Werten des
Profils neu gefüllt (auch mit Nullen). Danach gewinnen deine eigenen Zahlen —
so wird nie doppelt kompensiert.

### Gruppe "Serie"

* **Dialog offen lassen** — nach "Erzeugen" öffnet sich der Dialog sofort wieder
  mit denselben Werten. Ideal, um eine ganze Kiste voll zu bauen.
  Beenden mit **Abbrechen** oder **Esc**.
* **Nebeneinander ablegen** — legt jeden neuen Baustein mit 5 mm Abstand neben
  den vorherigen, statt alles in den Ursprung zu stapeln. Direkt slicer-fertig.

### Gruppe "STL-Export"

* **STL beim Erzeugen schreiben** — schreibt jeden erzeugten Körper sofort als
  binäres STL in den gewählten Ordner. Netzqualität kommt aus dem Druckprofil.
* **Zielordner** / **Ordner wählen …**

Vorhandene Dateien werden **nie überschrieben**, sondern durchnummeriert
(`..._2.stl`, `..._3.stl`).

Der Dateiname verrät alles Wichtige:

```
Stein_4x2_k00.stl          → Stein, 4×2 Noppen, Klemmspiel 0,00 mm
Stein_4x2_k05.stl          → Klemmspiel +0,05 mm
Stein_4x2_km08.stl         → Klemmspiel −0,08 mm  (m = minus)
Stein_4x2_k00_komp.stl     → mit aktiver Druckerkalibrierung
Stein_4x2_k00_f30.stl      → Fase 0,30 mm
Stein_4x2_k00_r25.stl      → Radius 0,25 mm
```

Damit bleiben Kalibrierdrucke auch nach Wochen noch auseinanderzuhalten.

---

## 6. Der wichtigste Schritt: einmal kalibrieren

### Worum es hier überhaupt geht

Stell dir vor, du malst einen Kreis mit einem dicken Filzstift nach. Dein Kreis
wird nie genau so groß wie die Vorlage — der Stift ist eben dick. Ein 3D-Drucker
macht dasselbe: Er drückt weichen Kunststoff durch eine Düse, und der landet nie
haargenau auf der gedachten Linie.

Bei den meisten Sachen fällt das nicht auf. Bei einem Klemmbaustein schon. Ob er
hält oder nicht, entscheidet sich in **hundertstel Millimetern** — das ist
dünner als ein Haar. Ist die Noppe ein winziges bisschen zu dünn, fällt der Turm
auseinander.

Die gute Nachricht: Dein Drucker macht diesen Fehler **immer gleich**. Du musst
ihn also nur einmal ausmessen und die Zahlen eintragen. Danach passt es für alle
Steine, die du je druckst. Das dauert einen Nachmittag und lohnt sich.

### Schritt 1 — Einen Teststein drucken

Erzeuge einen **4×2-Stein** und lass das Feld **Klemmspiel** dabei auf `0,00`
stehen. Als STL exportieren und ausdrucken — mit demselben Material, derselben
Düse und derselben Schichthöhe, die du auch später benutzen willst. Änderst du
davon später etwas, stimmt die Messung nicht mehr.

### Schritt 2 — Nachmessen

Jetzt brauchst du einen **Messschieber** (auch Schieblehre genannt). Ein
Lineal reicht nicht — wir suchen nach Unterschieden, die kleiner sind als der
Strich auf dem Lineal.

Miss den gedruckten Stein an diesen Stellen und schreib auf, was du abliest.
Rechts steht, was eigentlich herauskommen müsste:

| Was du misst | Sollwert beim 4×2 |
|---|---|
| Länge | 31,80 mm |
| Breite | 15,80 mm |
| Gesamthöhe | 11,40 mm |
| Höhe ohne Noppen | 9,60 mm |
| Noppendurchmesser | 4,80 mm |
| Wandstärke | 1,20 mm |
| Röhre außen | 6,51 mm |
| Röhre innen | 4,95 mm |

### Schritt 3 — Vergleichen: es gibt zwei Sorten Fehler

Das ist der wichtigste Gedanke im ganzen Kapitel. Wenn dein Stein nicht stimmt,
kann das **zwei völlig verschiedene Gründe** haben — und jeder braucht seine
eigene Gegenmaßnahme.

**Fehler 1: Alles wird ein bisschen kleiner.**
Wie ein Pullover, der in der Wäsche eingeht. Der Ärmel schrumpft mehr als der
Kragen, weil er länger ist — der Fehler **wächst mit der Größe**. Bei uns:
Der Stein sollte 31,80 mm lang sein, ist aber nur 31,73 mm. Das sind 0,22 %
zu wenig, und dieselben 0,22 % fehlen dann auch bei einem Riesenstein.

**Fehler 2: Runde Sachen werden zu dünn — immer um denselben Betrag.**
Das ist der dicke Filzstift von vorhin. Er ist immer gleich dick, egal ob du
einen kleinen oder einen großen Kreis malst. Bei uns: Die Noppe sollte 4,80 mm
dick sein, ist aber nur 4,56 mm. Es fehlen 0,24 mm — und **genau diese
0,24 mm** fehlen auch an jeder anderen Rundung, egal wie groß sie ist.

> **Warum das wichtig ist:** Wenn du versuchst, den Filzstift-Fehler mit einem
> Prozentwert wegzurechnen, geht es schief. Bei der kleinen Noppe wären 0,24 mm
> ganze 5 Prozent — rechnest du überall 5 Prozent drauf, wird der ganze Stein
> viel zu groß. Deshalb hat der Dialog für jede Fehlersorte ein eigenes Feld.

Am Klemmkontakt zwischen Noppe und Röhre addieren sich beide Fehler. Deshalb
ist ein unkalibrierter Stein fast immer zu locker.

### Schritt 4 — Die Zahlen eintragen

**Der schnelle Weg:** Erhöhe im Dialog einfach das **Klemmspiel** um das, was
an der Noppe fehlt. Fehlen 0,20 mm, trägst du `+0,20` ein und druckst neu. Der
Stein hält dann — aber sein Außenmaß stimmt weiterhin nicht ganz.

**Der saubere Weg:** Trage deine Messwerte in die Gruppe
**Druckerkalibrierung** ein (Sollwert und gemessener Wert, siehe Abschnitt 5)
oder leg dir ein eigenes Druckprofil an (Abschnitt 7). Dann stimmen auch
Außenmaß und Röhrenposition, nicht nur die Klemmung.

### Wenn die Röhre innen zu eng ist

Das ist ein Sonderfall, der viele ratlos macht: Die Röhre unten im Stein ist
innen viel zu eng, obwohl außen alles passt. **Das ist meistens gar kein Fehler
am Modell** — und Aufmaße im Dialog bringen dort nichts.

Der Grund liegt im Slicer, also dem Programm, das aus dem Modell die
Druckbefehle macht. Die Röhrenwand ist mit 0,78 mm sehr dünn. Der Slicer druckt
aber am liebsten in ganzen Linien nebeneinander, und zwei seiner Linien sind
zusammen 0,955 mm dick. Diesen Überschuss schiebt er nach innen — das Loch wird
enger.

Die Lösung gehört deshalb in den Slicer, nicht ins Modell: Stell die Wandbreite
dort auf einen Wert, der zweimal in 0,78 mm passt (z. B. 2 × 0,39 mm).

Fürs normale Stapeln ist das übrigens egal. Dabei greift nur die **Außenseite**
der Röhre — das enge Loch stört erst, wenn du eine Achse hindurchstecken willst.

---

## 7. Eigenes Druckerprofil anlegen (optional)

`Klemmbaustein.py` in einem Texteditor öffnen und im Block `PRINT_PROFILES`
(etwa ab Zeile 130) eine Zeile ergänzen:

```python
'Mein Drucker (PLA)':  dict(gap=0.20, wall=1.20, klemm=0.00,
                            rohr=0.10, hole=0.20, mesh='high',
                            komp_schrumpf=0.24,   # % XY-Schrumpf
                            komp_rund=0.23,       # mm Aufmaß auf Rundungen
                            komp_loch=0.00),      # mm Aufmaß Röhre innen
```

Bedeutung der Werte (alle in mm, außer `komp_schrumpf` in %):

| Schlüssel | Bedeutung |
|---|---|
| `gap` | Untermaß des Außenmaßes gegenüber dem Raster (Original: 0,20) |
| `wall` | Wandstärke |
| `klemm` | Vorgabewert für das Klemmspiel |
| `rohr` | Spiel im Röhren-**Innen**durchmesser (nur für Noppe-in-Röhre) |
| `hole` | Aufmaß der Technic-Querbohrung |
| `mesh` | STL-Netzqualität: `'high'`, `'medium'`, `'low'` |
| `komp_schrumpf` | XY-Schrumpf in Prozent, wirkt auf alle Rastermaße |
| `komp_rund` | Aufmaß auf konvexe Rundungen (Noppe, Stege, Röhrenaußenseite) |
| `komp_loch` | Aufmaß auf den Röhren-Innendurchmesser |

Die drei `komp_`-Werte sind optional und standardmäßig aus. Sie beschreiben nicht,
wie das Teil aussehen *soll*, sondern gleichen aus, was der Drucker daraus macht.
**Nur mit echten Messwerten füllen.**

> Bei aktiver Kompensation ist das Modell in Fusion **absichtlich größer** als die
> Maße in der Infozeile. Die Infozeile zeigt das gewünschte *End*maß nach dem
> Druck. Eine Kontrollmessung in Fusion sieht dann aus wie ein Fehler, ist aber
> keiner — der Dialog weist auch ausdrücklich darauf hin.

Nach jeder Änderung an der Datei: in Fusion `Shift`+`S` → Add-In **Stop**, dann
wieder **Run**. Ein Fusion-Neustart ist nicht nötig.

---

## 8. Slicer-Empfehlungen

* **Schichthöhe:** 0,15–0,20 mm. Feiner bringt bei der Klemmung wenig, kostet nur Zeit.
* **Perimeter:** 2–3. Bei den dünnen Röhren die *Wandbreite* prüfen (siehe oben).
* **Keine Stützen nötig** — die Geometrie ist so gebaut, dass alles druckbar ist.
* **Ausrichtung:** Noppen nach oben, Unterseite auf dem Bett. Nicht kippen.
* **Elephant Foot Compensation** aktivieren, sonst sitzt die erste Schicht zu breit
  und die Steine klemmen unten.
* **Kein Ironing** auf den Noppen.

---

## 9. Wenn etwas nicht klappt

| Problem | Ursache / Lösung |
|---|---|
| Add-In taucht unter "My Add-Ins" nicht auf | Ordnername ≠ Dateiname. Ordner, `.py` und `.manifest` müssen alle `Klemmbaustein` heißen. |
| Nach dem Kopieren nichts sichtbar | Fusion neu starten, oder über das grüne `+` im Add-Ins-Dialog manuell hinzufügen. |
| "Bitte zuerst ein Design öffnen" | Du bist nicht im Konstruktions-Arbeitsbereich. Neues Design anlegen. |
| Befehl fehlt im Menü | `Shift`+`S` → Reiter Add-Ins → Klemmbaustein → **Run**. Häkchen "Run on Startup" setzen. |
| Dialog reagiert träge | **Live-Vorschau** abschalten, besonders ab ca. 16×16 Noppen. |
| Steine halten nicht | Klemmspiel in 0,05er-Schritten erhöhen, dann kalibrieren (Abschnitt 6). |
| Steine sitzen bockfest / brechen | Klemmspiel in 0,05er-Schritten senken. Bei PLA nie über +0,05. |
| Steine klemmen nur unten | Elephant Foot Compensation im Slicer aktivieren. |
| Dialog geht nach OK immer wieder auf | Das ist der Serienbetrieb. Mit **Esc** oder **Abbrechen** beenden, oder Häkchen "Dialog offen lassen" entfernen. |
| Einstellungen zurücksetzen | Ordner `Klemmbaustein-Generator` in `%LOCALAPPDATA%` löschen (dort liegt `einstellungen.json`). |

Fehlermeldungen zeigt das Add-In immer im Klartext mit Zeilenangabe an — bei
Problemen einfach den Text posten, damit lässt sich fast alles nachvollziehen.

---

## 10. Rechtliches

**Unabhängiges Projekt.** Dieses Add-In ist ein privates, unentgeltliches
Werkzeug. Es steht in **keiner Verbindung zur LEGO Gruppe** und wird von ihr
weder gesponsert noch autorisiert oder unterstützt. LEGO® ist eine eingetragene
Marke der LEGO Gruppe; die Nennung an dieser Stelle dient allein der
beschreibenden Angabe der Kompatibilität.

**Maße.** Alle Werte basieren auf frei verfügbaren, gemessenen Nennmaßen des
Klemmbaustein-Rasters. Die zugrunde liegenden Patente sind seit Jahrzehnten
abgelaufen; die reine Steckverbindung ist technisch bedingt und deshalb nicht
formmarkenrechtlich geschützt (EuGH, Rs. C-48/09 P). Das Add-In bildet
ausschließlich generische Grundformen ab — Stein, Platte, Fliese und
Technic-Stein. Spezialteile, Figuren oder Set-spezifische Elemente sind
bewusst **nicht** enthalten.

**Weitergabe.** Das Add-In steht unter der MIT-Lizenz (siehe `LICENSE` im
Projektordner): Nutzen, Ändern und Weitergeben sind frei, auch kommerziell,
solange der Copyright-Vermerk erhalten bleibt. Über die Weitergabe zusammen
mit dieser Anleitung freue ich mich.

**Haftung.** Die Nutzung erfolgt auf eigene Gefahr. Eine Gewähr für
Maßhaltigkeit, Eignung für einen bestimmten Zweck oder für Druckergebnisse wird
nicht übernommen.

Viel Spaß beim Drucken. Über Rückmeldungen zu Druckprofilen anderer Drucker freue
ich mich — je mehr kalibrierte Profile zusammenkommen, desto besser für alle.
