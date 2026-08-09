# -*- coding: utf-8 -*-
"""
Klemmbaustein-Generator - Fusion 360 Add-In
===========================================

Erzeugt parametrische, klemmbaustein-kompatible Bauteile (Stein, Platte,
Fliese, Technic-Stein) direkt in Fusion 360 - mit Live-Vorschau und
optionalem STL-Export fuer den 3D-Druck.

Installation als Add-In
-----------------------
1. Ordner "Klemmbaustein" (mit Klemmbaustein.py + Klemmbaustein.manifest)
   nach   %APPDATA%\\Autodesk\\Autodesk Fusion 360\\API\\AddIns\\   kopieren
   (macOS: ~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/)
2. In Fusion: Utilities -> ADD-INS -> Add-Ins -> "Klemmbaustein" -> Run
3. Der Befehl liegt danach unter SOLID -> CREATE -> "Klemmbaustein-Generator".

Die Datei laeuft auch als reines Script (Utilities -> ADD-INS -> Scripts);
in dem Fall wird der Dialog sofort geoeffnet und der Prozess am Ende sauber
beendet.

Rechtlicher Hinweis
-------------------
Dieses Projekt ist ein unabhaengiges, privates und unentgeltliches Werkzeug.
Es steht in keiner Verbindung zur LEGO Gruppe und wird von ihr weder
gesponsert noch autorisiert oder unterstuetzt. LEGO(R) ist eine eingetragene
Marke der LEGO Gruppe; die Nennung dient allein der Beschreibung der
Kompatibilitaet. Alle Masse basieren auf frei verfuegbaren, gemessenen
Nennmassen des seit Jahrzehnten patentfreien Klemmbaustein-Rasters.

(C) 2026 Berthold Wolf. Lizenziert unter der MIT-Lizenz, siehe LICENSE im
Projektordner. Die Nutzung
erfolgt auf eigene Gefahr; eine Gewaehr fuer Masshaltigkeit, Eignung oder
Druckergebnisse wird nicht uebernommen.
"""

import math
import os
import sys
import traceback

import adsk.core
import adsk.fusion

# Das Basismodul liegt neben dieser Datei. Fusion nimmt den Add-In-Ordner
# nicht zuverlaessig in den Suchpfad auf, deshalb hier selbst eintragen.
_THIS_DIR = os.path.dirname(os.path.realpath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

import bausteinbasis as b

# Fusion haelt einmal importierte Module ueber die ganze Sitzung fest.
# Ohne das Neuladen wuerde eine Aenderung am Basismodul erst nach einem
# Fusion-Neustart wirken.
try:
    import importlib
    importlib.reload(b)
except Exception:
    pass

# Kurznamen fuer die haeufig gebrauchten Helfer. Die Implementierung liegt
# jetzt einmalig im Basismodul, das sich beide Add-Ins teilen.
_pt = b.pt
_val = b.val
_de = b.de
_rechteck = b.rechteck
_rundrechteck = b.rundrechteck
_kreis = b.kreis
_alle_profile = b.alle_profile
_extrude = b.extrude
_durchbruch = b.durchbruch
_finde = b.finde
_dokument_schluessel = b.dokument_schluessel
_schrumpf_faktor = b.schrumpf_faktor
_kreiskanten = b.kreiskanten
_brich_kanten = b.brich_kanten


# ---------------------------------------------------------------------------
# Globale Objekte
# ---------------------------------------------------------------------------

app = None
ui = None

# Handler muessen global referenziert bleiben, sonst raeumt der Python-GC sie
# weg und Fusion verliert die Callbacks (klassischer Fusion-API-Stolperstein).
_handlers = []

# Zuletzt benutzte Dialogwerte - damit der Dialog beim Wiederoeffnen genau
# dort weitermacht, wo man aufgehoert hat. _letzte zeigt bewusst auf
# dieselbe Ablage wie die Konfiguration, damit jede Aenderung automatisch
# mitgespeichert wird.
_konfig = b.Konfig('Klemmbaustein-Generator')
_letzte = _konfig.werte
_ganzzahl = _konfig.ganzzahl
_konfig_laden = _konfig.laden
_konfig_speichern = _konfig.speichern

# Ablageposition je Dokument (Y-Versatz in mm), damit mehrere Bausteine
# nebeneinander statt uebereinander landen.
_platz = {}

# Steuerflagge fuer das automatische Wiederoeffnen nach OK.
_wiederholen_aktiv = False

CMD_ID = 'KlemmbausteinGeneratorCmd'
CMD_NAME = 'Klemmbaustein-Generator'
CMD_TOOLTIP = ('Erzeugt parametrische, klemmbaustein-kompatible Bauteile '
               '(Stein, Platte, Fliese, Technic-Stein) mit Live-Vorschau '
               'und STL-Export.')

WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidCreatePanel'

# Wird die Datei ohne Manifest ausgefuehrt, laeuft sie als Script und muss
# sich selbst am Leben halten bzw. am Ende terminieren.
_SCRIPT_MODE = not os.path.isfile(os.path.join(_THIS_DIR, 'Klemmbaustein.manifest'))


# ---------------------------------------------------------------------------
# Geometrie-Konstanten (alle Werte in mm - Umrechnung nach cm ueber MM)
# ---------------------------------------------------------------------------

MM = 0.1              # Fusion rechnet intern in cm -> 1 mm = 0.1 cm

PITCH = 8.0           # Rastermass (Noppenabstand)
BRICK_H = 9.6         # Hoehe Stein
PLATE_H = 3.2         # Hoehe Platte / Fliese
TOP_WALL = 1.0        # Dicke der Deckplatte
STUD_D = 4.8          # Noppendurchmesser
STUD_H = 1.8          # Noppenhoehe
TUBE_OD = 6.51        # Aussendurchmesser der Unterseiten-Roehren
TUBE_ID = 4.8         # Innendurchmesser der Unterseiten-Roehren
PIN_D = 3.2           # Durchmesser der Stege bei 1xN-Teilen
TECHNIC_HOLE_D = 4.8  # Durchmesser der Technic-Querbohrung
TECHNIC_AXIS_Z = 5.8  # Hoehe der Bohrungsachse ueber der Unterkante

# Kreuzprofil der Technic-Achse: 4,8 mm ueber die Spitzen, 1,8 mm Stegbreite.
# Damit dreht die Achse nicht durch, waehrend das Rundloch sie lagert.
AXLE_SPAN = 4.8
AXLE_ARM = 1.8

# Woher die Klemmkraft kommt (wichtig fuer jede Toleranzaenderung):
#   Noppenmitte -> Roehrenmitte = sqrt(4^2 + 4^2)   = 5.6569 mm
#   Noppenradius + Roehrenaussenradius = 2.4 + 3.255 = 5.6550 mm
#   -> 0.002 mm Rest: die Nennmasse liegen auf Linienberuehrung.
# Gegriffen wird ausschliesslich an der Roehren-AUSSENseite (bzw. bei 1xN an
# den Stegen, dort Abstand 4.0 = 1.6 + 2.4, ebenfalls tangential). Die
# Seitenwaende haben konstruktiv 0.3 mm Luft und klemmen nicht mit.
# Jede Verkleinerung der Noppe wirkt also 1:1 als Spiel.
KLEMM_TANGENTE = 5.6569   # nur zur Anzeige / Kontrolle

# Farben der Infozeile. Fusion rendert dort Qt-Rich-Text, also reicht ein
# span mit color - mehr Gestaltung laesst der Dialog nicht zu.
#
# Bewusst mittelhelle Toene: der Dialog kann hell oder dunkel stehen, und
# ein zartes Pastellgruen waere auf weissem Grund unlesbar, ein sattes
# Dunkelrot auf schwarzem.
FARBE_GUT = '#2fa84f'      # Nennmass getroffen
FARBE_WARN = '#d98324'     # zu locker - haelt, aber nicht gut
FARBE_FEHLER = '#d64541'   # zu stramm oder echte Warnung
FARBE_LEISE = '#8a8f98'    # Nebeninformation


def _farbig(text, farbe):
    return '<span style="color:{}">{}</span>'.format(farbe, text)

GRUNDPLATTE_H = 1.6   # Hoehe der grossen Grundplatte (ohne Klemmung unten)
HALBSTEIN_H = 4.8     # halbe Steinhoehe - passt auf 1,5 Platten
SCHRAEG_ENDE = PLATE_H  # Hoehe, auf die eine Schraege auslaeuft
MAX_SCHRAEGE = 6      # laengste zulaessige Schraege in Noppen
MAX_SCHENKEL = 8      # breitester zulaessiger Schenkel beim Eckstein

TYP_STEIN = 'Stein'
TYP_PLATTE = 'Platte'
TYP_FLIESE = 'Fliese'
TYP_TECHNIC = 'Technic-Stein'
TYP_SCHRAEG = 'Schraegstein'
TYP_GRUNDPLATTE = 'Grundplatte'
TYP_JUMPER = 'Jumper-Platte'
TYP_HALBSTEIN = 'Halbstein'
TYP_LOCHBALKEN = 'Technic-Lochbalken'
TYP_RUND = 'Rundstein'
TYP_RUNDPLATTE = 'Rundplatte'
TYP_RUNDFLIESE = 'Rundfliese'
TYP_ECK = 'Eckstein'
TYP_SCHRAEG_INV = 'Schraegstein umgekehrt'
TYPEN = [TYP_STEIN, TYP_HALBSTEIN, TYP_PLATTE, TYP_FLIESE, TYP_JUMPER,
         TYP_TECHNIC, TYP_LOCHBALKEN, TYP_SCHRAEG, TYP_SCHRAEG_INV, TYP_ECK,
         TYP_RUND, TYP_RUNDPLATTE, TYP_RUNDFLIESE, TYP_GRUNDPLATTE]

# Typen, die keine Noppen tragen.
TYPEN_OHNE_NOPPEN = (TYP_FLIESE, TYP_LOCHBALKEN, TYP_RUNDFLIESE)

# Typen mit einer Schraege. Beim umgekehrten faellt sie an der Unterseite
# weg statt an der Oberseite - oben bleibt die volle Noppenflaeche stehen.
TYPEN_MIT_SCHRAEGE = (TYP_SCHRAEG, TYP_SCHRAEG_INV)

# Typen mit Technic-Querbohrungen.
TYPEN_MIT_BOHRUNG = (TYP_TECHNIC, TYP_LOCHBALKEN)

BOHRUNG_RUND = 'Rundloch (Pin)'
BOHRUNG_ACHSE = 'Achskreuz'
BOHRUNGEN = [BOHRUNG_RUND, BOHRUNG_ACHSE]

# Druckprofile: Toleranzen in mm.
#   gap   - Untermass des Aussenmasses gegenueber dem Raster (Nennwert 0.20)
#   wall  - Wandstaerke
#   klemm - Aufmass auf Noppe und Stege: POSITIV = fester, negativ = loser.
#           0.00 = Nennmass = Linienberuehrung wie beim Original.
#   rohr  - Spiel im Roehren-INNENdurchmesser (nur fuer Noppe-in-Roehre,
#           ohne Einfluss auf die normale Klemmung beim Stapeln)
#   hole  - Aufmass Technic-Bohrung
#   mesh  - Netzqualitaet fuer den STL-Export
#
# Druckerkompensation (optional, Vorgabe 0 = aus). Die Werte oben beschreiben,
# was herauskommen SOLL; die Werte hier gleichen aus, was ein konkreter Drucker
# daraus macht. Nur mit Messwerten aus einem Testdruck fuellen:
#   komp_schrumpf - XY-Schrumpf in Prozent, wirkt als Faktor auf alle
#                   Rastermasse (Aussenmass, Noppen- und Roehrenpositionen).
#   komp_rund     - Aufmass auf konvexe Rundungen (Noppe, Stege,
#                   Roehrenaussenseite). Absolut, weil der Fehler an kleinen
#                   Features eine Konstante ist und nicht mit dem Mass waechst.
#   komp_loch     - Aufmass auf den Roehren-INNENdurchmesser. Nur sinnvoll,
#                   wenn der Slicer der modellierten Wanddicke ueberhaupt
#                   folgt: rundet er die duenne Ringwand auf ganze Perimeter
#                   auf, ergibt sich der Innendurchmesser aus Aussenmass minus
#                   zwei Perimeterbreiten und laesst sich vom Modell aus nicht
#                   steuern. Dann gehoert die Wandbreite in den Slicer.
PRINT_PROFILES = {
    # PETG laeuft an kleinen Features leicht nach: Bohrungen fallen enger,
    # Zapfen dicker aus. Deshalb mehr Spiel in den Loechern, aber Nennmass
    # an der Klemmstelle - die Feinjustage macht das Feld "Klemmspiel".
    'PETG (Snapmaker U1)':           dict(gap=0.20, wall=1.20, klemm=0.00,
                                          rohr=0.15, hole=0.25, mesh='high'),
    # Wie oben, aber mit den Messwerten aus dem Testdruck vom 03.08.2026
    # (4x2-Stein, PETG 0,20 mm) kompensiert. Gemessen wurde:
    #   Aussenmass  31,73 / 15,76  statt 31,80 / 15,80  -> 0,24 % Schrumpf
    #   Noppe       4,56           statt 4,80           -> -0,23 (nach Schrumpf)
    #   Roehre aus  6,31           statt 6,51           -> -0,20
    #   Roehre in   4,40           statt 4,95           -> -0,55
    # Der Klemmkontakt hatte damit 0,21 mm Luft statt Linienberuehrung, der
    # Stein hielt nicht. Klemmspiel bleibt 0,00: die Kompensation trifft das
    # Nennmass jetzt selbst, die Feinjustage bleibt fuer den Rest frei.
    #
    # komp_loch bleibt bewusst auf 0, obwohl der Innendurchmesser um 0,55 mm
    # danebenlag: die Roehrenwand kam mit 0,955 mm aus dem Drucker - das sind
    # 2 Perimeter a 0,478 mm, also nicht die modellierten 0,78 mm. Der Slicer
    # rundet die duenne Ringwand auf ganze Perimeter auf, und diese Wanddicke
    # bleibt unabhaengig davon, was das Modell vorgibt. Ein Aufmass im Modell
    # verpufft deshalb; die Wandbreite gehoert im Slicer korrigiert (2 x 0,39).
    'PETG (Snapmaker U1, kalibriert)':
                                     dict(gap=0.20, wall=1.20, klemm=0.00,
                                          rohr=0.15, hole=0.25, mesh='high',
                                          komp_schrumpf=0.24, komp_rund=0.23,
                                          komp_loch=0.00),
    # PLA laeuft weniger nach als PETG und ist steifer. Loecher fallen naeher
    # am Nennmass aus, dafuer vertragen die duennen Roehren kaum Uebermass -
    # sie reissen eher, als dass sie federn. Klemmspiel deshalb nicht ueber
    # +0,05 treiben.
    'PLA (0,2 mm Schicht)':          dict(gap=0.20, wall=1.20, klemm=0.00,
                                          rohr=0.10, hole=0.20, mesh='high'),
    'PLA fein (0,1 mm Schicht)':     dict(gap=0.20, wall=1.20, klemm=0.00,
                                          rohr=0.08, hole=0.15, mesh='high'),
    'Resin / SLA':                   dict(gap=0.20, wall=1.00, klemm=0.02,
                                          rohr=0.05, hole=0.10, mesh='high'),
    'Locker (leichtgaengig)':        dict(gap=0.25, wall=1.40, klemm=-0.08,
                                          rohr=0.15, hole=0.30, mesh='medium'),
}

KLEMM_MIN = -0.25     # Grenzen fuer die manuelle Feinjustage (mm)
KLEMM_MAX = 0.25

MAX_NOPPEN = 32
ABSTAND = 5.0         # Luecke zwischen nebeneinander abgelegten Bausteinen (mm)

# --- Kanten brechen --------------------------------------------------------
# Vorgabe ueberall 0: eine Kantenbrechung ist eine bewusste Entscheidung,
# kein stiller Eingriff in die Geometrie.
#
# Die Noppe ist nur 1,8 mm hoch, und die Klemmung lebt von der Beruehrung
# ueber genau diese Hoehe. Jeder Millimeter Kantenbrechung oben geht davon
# ab: 0,30 mm sind bereits 17 % weniger Kontakt. Deshalb eine eigene,
# engere Grenze fuer die Noppe - unten darf man grosszuegiger sein, dort
# kostet die Einfuehrhilfe nichts.
KANTE_MAX = 0.60          # Einfuehrkante unten (Roehre, Steg, Bohrung)
KANTE_NOPPE_MAX = 0.40    # Einfuehrkante Noppe
KANTE_NOPPE_WARNUNG = 0.30
ECKRADIUS_MAX = 1.50      # Eckradius der senkrechten Aussenkanten

METHODE_FASE = 'Fase (45 Grad)'
METHODE_RADIUS = 'Radius'
METHODEN = [METHODE_FASE, METHODE_RADIUS]

# Wie viel der Roehrenwand eine Kantenbrechung hoechstens aufbrauchen darf.
# Innen- und Aussenkante zehren beide an derselben duennen Wand; bleibt
# nichts stehen, scheitert das Feature oder es entsteht eine Schneide.
WAND_ANTEIL = 0.45

# --- Druckerkalibrierung ---------------------------------------------------
# Der Faktor entsteht aus Soll geteilt durch Gemessen: ein zu klein
# gedrucktes Teil ergibt einen Faktor groesser 1, das Modell wird also
# vorgehalten. Beide Felder auf 0 = Achse unkalibriert.
#
# Grenzen bewusst eng: mehr als 2 % Abweichung ist kein Schrumpf mehr,
# sondern ein falsch eingestellter Drucker (Schrittweite, Extrusionsbreite).
# Solche Fehler gehoeren in den Slicer, nicht ins Modell.
FAKTOR_MIN = 0.98
FAKTOR_MAX = 1.02

# Ab dieser Differenz zwischen X und Y wird gewarnt. Der Klemmkontakt liegt
# diagonal (5,6569 mm) und hat nur 0,002 mm Reserve - laufen die Achsen
# auseinander, muesste die Noppe elliptisch werden, um zu folgen.
FAKTOR_DIFF_WARNUNG = 0.0015   # 0,15 %

MAX_RUND = 0.60       # Grenze fuer das absolute Rundungs-Aufmass

# Ab so vielen zu brechenden Rundkanten laesst die Live-Vorschau die
# Kantenbrechung weg. Ein 32x32 haette 961 Roehren und 1024 Noppen - jede
# Kante einzeln zu verrunden dauert Sekunden, und die Vorschau baut bei
# jedem Tastendruck neu auf. Der Eckradius bleibt, der kostet nichts:
# er sitzt in der Skizze und nicht in einem Feature.
VORSCHAU_KANTEN_GRENZE = 150

# Eingabe-IDs
IN_TYP = 'kbTyp'
IN_LAENGE = 'kbLaenge'
IN_BREITE = 'kbBreite'
IN_SCHRAEGE = 'kbSchraege'
IN_PROFIL = 'kbProfil'
IN_KLEMM = 'kbKlemm'
IN_VORSCHAU = 'kbVorschau'
IN_INFO = 'kbInfo'
IN_SERIE_GRP = 'kbSerieGruppe'
IN_WIEDERHOLEN = 'kbWiederholen'
IN_ANORDNEN = 'kbAnordnen'
IN_STL_GRP = 'kbStlGruppe'
IN_STL_AN = 'kbStlAn'
IN_STL_ORDNER = 'kbStlOrdner'
IN_STL_BROWSE = 'kbStlBrowse'

IN_KANTE_GRP = 'kbKanteGruppe'
IN_KANTE_METHODE = 'kbKanteMethode'
IN_KANTE_UNTEN = 'kbKanteUnten'
IN_KANTE_NOPPE = 'kbKanteNoppe'
IN_ECKRADIUS = 'kbEckradius'

IN_KAL_GRP = 'kbKalGruppe'
IN_KAL_KOPPELN = 'kbKalKoppeln'
IN_KAL_X_SOLL = 'kbKalXSoll'
IN_KAL_X_IST = 'kbKalXIst'
IN_KAL_Y_SOLL = 'kbKalYSoll'
IN_KAL_Y_IST = 'kbKalYIst'
IN_KAL_Z_SOLL = 'kbKalZSoll'
IN_KAL_Z_IST = 'kbKalZIst'
IN_KAL_RUND = 'kbKalRund'
IN_KAL_UEBERNEHMEN = 'kbKalUebernehmen'
IN_KAL_INFO = 'kbKalInfo'

IN_SCHENKEL = 'kbSchenkel'
IN_BOHRUNG = 'kbBohrung'


# ---------------------------------------------------------------------------
# Kleine Helfer
# ---------------------------------------------------------------------------
# Die allgemeinen Helfer liegen im Basismodul und sind oben unter ihren
# gewohnten Namen eingebunden. Hier steht nur noch, was wirklich
# klemmbausteinspezifisch ist.

def _hoehe(typ):
    if typ == TYP_GRUNDPLATTE:
        return GRUNDPLATTE_H
    if typ == TYP_HALBSTEIN:
        return HALBSTEIN_H
    return PLATE_H if typ in (TYP_PLATTE, TYP_FLIESE, TYP_JUMPER,
                              TYP_RUNDPLATTE, TYP_RUNDFLIESE) else BRICK_H


def _ist_rund(typ):
    return typ in (TYP_RUND, TYP_RUNDPLATTE, TYP_RUNDFLIESE)


def _schenkel(nx, ny, w):
    """Gueltige Schenkelbreite des Ecksteins in Noppen.

    Ein Schenkel so breit wie das Teil selbst waere kein L mehr, sondern
    ein Quader - dann waere der Typ die falsche Wahl. Deshalb hoechstens
    eine Noppe weniger als die schmalere Seite.
    """
    return max(1, min(w, min(nx, ny) - 1))


def _im_eck(i, j, nx, ny, w):
    """Liegt das Rasterfeld (i, j) noch im L?

    Das L besteht aus zwei Schenkeln: einer laeuft entlang X am unteren
    Rand, der andere entlang Y am linken. Ein Feld gehoert dazu, sobald es
    in einem der beiden liegt - die Ueberlappung in der Ecke zaehlt einfach.
    """
    return j < w or i < w


def _roehren_stellen(typ, nx, ny, w=1, gap=0.20, wall=1.20):
    """Rasterkreuze mit Roehre, als Noppen-Koordinaten.

    Wie _noppen_stellen die eine Quelle fuer Geometrie und Darstellung.
    Roehren gibt es nur ab 2x2; bei 1xN treten Stege an ihre Stelle.
    """
    if typ == TYP_GRUNDPLATTE or nx < 2 or ny < 2:
        return []

    aussen_r = (nx * PITCH - gap) / 2.0
    innen_r = aussen_r - wall
    stellen = []
    for i in range(1, nx):
        for j in range(1, ny):
            # Eine Roehre steht auf einem Rasterkreuz und wird von vier
            # Feldern getragen. Fehlt eines, haengt sie halb in der Luft.
            if typ == TYP_ECK and not all(_im_eck(a, b, nx, ny, w)
                                          for a in (i - 1, i)
                                          for b in (j - 1, j)):
                continue
            if _ist_rund(typ):
                x = i * PITCH - gap / 2.0
                y = j * PITCH - gap / 2.0
                if not _rund_passt(x, y, aussen_r, innen_r, TUBE_OD / 2.0):
                    continue
            stellen.append((i, j))
    return stellen


# Luft ueber einer Noppe, damit ein Hohlraum sie noch aufnimmt statt sie
# nur eben zu streifen.
NOPPEN_LUFT = 0.2


def _roehren_hoehe(x_mitte, tube_od, schraege_l, kavitaet, flach_tiefe, stud_h):
    """Wie hoch eine Roehre an dieser Stelle in X werden darf.

    Unter einer Schraege steht nicht die volle Bauhoehe zur Verfuegung: die
    Schraegflaeche ist vorher schon weggeschnitten, und eine auf volle
    Kavitaetshoehe gezogene Roehre ragte einfach oben durch sie hindurch -
    die Schraege waere dann nicht mehr glatt.

    Massgeblich ist die vorderste Stelle der Roehre, nicht ihre Mitte: dort
    ist die Schraege am niedrigsten. Wo sie hineinragt, wird die Roehre auf
    die Tiefe des flachen Hohlraums gekuerzt. Das reicht: geklemmt wird an
    den obersten knapp zwei Millimetern der Noppe, nicht ueber die ganze
    Laenge. Sie haengt dann an der Decke dieses flachen Hohlraums.

    Rueckgabe 0.0 heisst: hier passt keine Roehre mehr.
    """
    if schraege_l <= 1e-9 or x_mitte - tube_od / 2.0 >= schraege_l - 1e-9:
        return kavitaet
    if flach_tiefe > stud_h + NOPPEN_LUFT:
        return flach_tiefe
    return 0.0


def _stege_stellen(typ, nx, ny):
    """Stegpositionen bei 1xN-Teilen, als Noppen-Koordinaten.

    Ein 1xN-Teil hat keinen Platz fuer Roehren; dort greifen schmale Stege
    auf der Mittellinie, tangential im Abstand 4,0 = 1,6 + 2,4.
    """
    if typ == TYP_GRUNDPLATTE or (nx > 1 and ny > 1):
        return []
    if nx > 1:
        return [(float(i), ny / 2.0) for i in range(1, nx)]
    if ny > 1:
        return [(nx / 2.0, float(j)) for j in range(1, ny)]
    return []


def _noppen_stellen(typ, nx, ny, w=1, gap=0.20, schraege_noppen=0):
    """Alle Rasterstellen mit Noppe, als Noppen-Koordinaten.

    Eine Quelle fuer Geometrie und Infozeile. Haetten beide ihre eigene
    Zaehlung, wuerden sie frueher oder spaeter auseinanderlaufen - und die
    Infozeile ist genau das, worauf man sich vor dem Druck verlaesst.

    Der Rundfilter rechnet mit Nennmassen ohne Kalibrierung. Der Vorhalt
    liegt bei Bruchteilen eines Prozents und hat noch nie darueber
    entschieden, ob eine Noppe passt oder nicht.
    """
    if typ in TYPEN_OHNE_NOPPEN:
        return []

    xs, ys = _noppen_raster(typ, nx, ny)
    aussen_r = (nx * PITCH - gap) / 2.0
    mitte = aussen_r

    stellen = []
    for i in xs:
        for j in ys:
            if typ == TYP_SCHRAEG and i < schraege_noppen:
                continue
            if typ == TYP_ECK and not _im_eck(int(i), int(j), nx, ny, w):
                continue
            if _ist_rund(typ):
                x = i * PITCH - gap / 2.0
                y = j * PITCH - gap / 2.0
                if not _rund_passt(x, y, mitte, aussen_r, STUD_D / 2.0):
                    continue
            stellen.append((i, j))
    return stellen


# Wie viel des eigenen Radius ein Merkmal ueber den Rand des Rundsteins
# ragen darf. Streng gerechnet (voller Radius) verloere ausgerechnet der
# 2x2-Rundstein alle vier Noppen: sie sitzen 5,657 mm aus der Mitte, plus
# 2,4 mm Noppenradius sind 8,06 mm gegen 7,90 mm Aussenradius - 0,16 mm zu
# viel. Genauso sitzt aber auch das echte Teil, dort verschmilzt die Noppe
# einfach mit der Zylinderwand. Der halbe Radius laesst das zu und wirft
# trotzdem alles raus, was wirklich in der Luft haengt.
RUND_UEBERSTAND = 0.5


def _rund_passt(x, y, mitte, rand_r, eigen_r):
    """Sitzt ein rundes Merkmal noch tragfaehig im Rundstein?

    Beim Rundstein wird der rechteckige Grundriss zum Kreis beschnitten.
    Was dabei zum grossen Teil ins Leere ragen wuerde, entfaellt - ein halb
    abgeschnittener Zylinder waere weder schoen noch klemmfaehig. Ein
    knapper Ueberstand darf dagegen bleiben und verschmilzt mit der Wand.
    """
    abstand = math.hypot(x - mitte, y - mitte)
    return abstand + eigen_r * RUND_UEBERSTAND <= rand_r + 1e-9


def _l_polygon(sx, sy, w_mm):
    """Eckpunkte der L-Form, gegen den Uhrzeigersinn.

    Bewusst als geschlossener Linienzug statt als zwei sich ueberlappende
    Rechtecke: zwei Rechtecke ergaeben in der Ueberlappung mehrere Profile,
    und dann muesste man raten, welches das gemeinte ist.
    """
    return [(0.0, 0.0), (sx, 0.0), (sx, w_mm), (w_mm, w_mm),
            (w_mm, sy), (0.0, sy)]


def _achskreuz(spanne, arm):
    """Eckpunkte des Technic-Achsprofils, gegen den Uhrzeigersinn.

    Ein Kreuz aus zwei Rechtecken: spanne ueber die Spitzen, arm als
    Stegbreite. Anders als das Rundloch haelt es die Achse gegen Verdrehen.
    """
    a = spanne / 2.0
    b = arm / 2.0
    return [(a, b), (b, b), (b, a), (-b, a), (-b, b), (-a, b),
            (-a, -b), (-b, -b), (-b, -a), (b, -a), (b, -b), (a, -b)]


def _polygon(sketch, punkte, nach_sketch=None):
    """Geschlossener Linienzug aus mm-Koordinaten."""
    linien = sketch.sketchCurves.sketchLines
    wandeln = nach_sketch or (lambda x, y: _pt(x, y))
    for k in range(len(punkte)):
        x1, y1 = punkte[k]
        x2, y2 = punkte[(k + 1) % len(punkte)]
        linien.addByTwoPoints(wandeln(x1, y1), wandeln(x2, y2))


def _noppen_raster(typ, nx, ny):
    """Die Rasterstellen, an denen Noppen sitzen - als Noppen-Koordinaten.

    Normalerweise sitzt eine Noppe in der Mitte jedes Rasterfeldes: 0,5 /
    1,5 / 2,5 ... Die Jumper-Platte verschiebt sie auf die Rasterkreuze
    dazwischen: 1 / 2 / 3 ... Damit liegt ihre Noppe um ein halbes Raster
    (4 mm) versetzt, und genau das macht sie beim Bauen so nuetzlich.

    Der Versatz greift nur dort, wo es ueberhaupt ein Kreuz gibt. Bei einer
    Breite von einer Noppe existiert keines, also bleibt es dort bei der
    Feldmitte - beim klassischen 1x2-Jumper sitzt die Noppe deshalb quer
    mittig und laengs auf dem Kreuz, also genau einmal in der Mitte.
    """
    if typ == TYP_JUMPER:
        xs = [float(i) for i in range(1, nx)] or [0.5]
        ys = [float(j) for j in range(1, ny)] or [0.5]
    else:
        xs = [i + 0.5 for i in range(nx)]
        ys = [j + 0.5 for j in range(ny)]
    return xs, ys


def _schraegen_winkel(ns, hoehe_oben, hoehe_unten):
    """Neigungswinkel der Schraege in Grad.

    Bewusst aus der Geometrie gerechnet statt fest vorgegeben: eine Schraege
    muss ueber ganze Noppen laufen, sonst sitzen die Noppen der Oberseite
    nicht mehr im Raster. Der Winkel ist damit das Ergebnis, nicht die
    Vorgabe - deshalb weichen die Werte von den gerundeten Zahlen ab, die
    man aus dem Handel kennt.
    """
    return math.degrees(math.atan2(hoehe_oben - hoehe_unten, ns * PITCH))


def _kantenzahl(typ, nx, ny, schenkel=1):
    """Grobe Zahl der Rundkanten, die eine Kantenbrechung anfassen muesste.

    Eine Obergrenze reicht: sie entscheidet nur, ob die Live-Vorschau die
    Kantenbrechung noch mitmacht. Lieber einmal zu vorsichtig geschaetzt als
    ein eingefrorenes Fusion.
    """
    if _ist_rund(typ):
        ny = nx
    roehren = max(nx - 1, 0) * max(ny - 1, 0)
    noppen = len(_noppen_stellen(typ, nx, ny, _schenkel(nx, ny, schenkel)))
    return roehren * 2 + noppen


def _faktor(soll, ist):
    """Kalibrierfaktor aus einem Messwertpaar.

    Beide Felder leer (0) heisst: diese Achse ist nicht kalibriert. Ein Ist
    von 0 bei gesetztem Soll waere eine Division durch null - das ist keine
    Messung, sondern ein Tippfehler, und wird genauso behandelt.
    """
    if soll <= 1e-9 or ist <= 1e-9:
        return 1.0
    return max(FAKTOR_MIN, min(FAKTOR_MAX, soll / ist))


class Justage(object):
    """Vorhalt und Kantenbrechung - alles, was vom Nennmass abweicht.

    Als eigenes Objekt statt als weitere Parameter an baue_stein: die
    Signatur dort ist schon lang genug, und diese Werte gehoeren inhaltlich
    zusammen. Ohne Justage baut baue_stein weiterhin auf Nennmass, damit
    aeltere Aufrufe von aussen unveraendert funktionieren.
    """

    def __init__(self, fx=1.0, fy=1.0, fz=1.0, rund=0.0, loch=0.0,
                 methode=METHODE_FASE, kante_unten=0.0, kante_noppe=0.0,
                 eckradius=0.0):
        self.fx = fx
        self.fy = fy
        self.fz = fz
        self.rund = rund
        self.loch = loch
        self.methode = methode
        self.kante_unten = max(0.0, min(KANTE_MAX, kante_unten))
        self.kante_noppe = max(0.0, min(KANTE_NOPPE_MAX, kante_noppe))
        self.eckradius = max(0.0, min(ECKRADIUS_MAX, eckradius))

    @property
    def f_rund(self):
        """Faktor fuer runde Merkmale (Noppe, Roehre, Steg).

        Ein Kreis kann nur einem Faktor folgen. Laufen X und Y auseinander,
        muesste er zur Ellipse werden - das waere gegenueber echten Steinen
        falsch. Der Mittelwert haelt den Fehler auf beide Achsen verteilt.
        """
        return (self.fx + self.fy) / 2.0

    @property
    def ist_aktiv(self):
        return (self.fx != 1.0 or self.fy != 1.0 or self.fz != 1.0
                or abs(self.rund) > 1e-9 or abs(self.loch) > 1e-9)

    @property
    def bricht_kanten(self):
        return (self.kante_unten > 1e-9 or self.kante_noppe > 1e-9
                or self.eckradius > 1e-9)

    def ohne_kanten(self):
        """Dieselbe Kalibrierung, aber ohne Kantenbrechung.

        Fuer die Live-Vorschau grosser Bausteine: ein Fillet ueber tausend
        Kanten laeuft dort bei jedem Tastendruck neu und laesst Fusion
        stehen. Die Masse stimmen trotzdem - es fehlt nur die Optik, und
        das fertige Teil aus "Erzeugen" bekommt sie ohnehin.
        """
        return Justage(fx=self.fx, fy=self.fy, fz=self.fz,
                       rund=self.rund, loch=self.loch,
                       methode=self.methode, eckradius=self.eckradius)

    def kante_roehre(self, wandstaerke):
        """Kantenbrechung an der Roehre, begrenzt durch ihre eigene Wand.

        Innen- und Aussenkante zehren beide an derselben Ringwand von rund
        0,78 mm. Ohne diese Bremse verlangt schon eine 0,4-mm-Brechung mehr
        Material, als da ist: Fusion verweigert das Feature, und im besten
        Fall bleibt eine Schneide statt einer Wand stehen.
        """
        return min(self.kante_unten, max(0.0, wandstaerke * WAND_ANTEIL))

    @classmethod
    def aus_profil(cls, profil):
        """Nur die im Profil hinterlegten Werte - fuer Aufrufe ohne Dialog."""
        f = _schrumpf_faktor(profil)
        return cls(fx=f, fy=f, rund=profil.get('komp_rund', 0.0),
                   loch=profil.get('komp_loch', 0.0))


# ---------------------------------------------------------------------------
# Geometrie-Aufbau
# ---------------------------------------------------------------------------

def baue_stein(design, typ, nx, ny, profil_name, y_versatz=0.0, klemm=None,
               ns=1, lage=None, justage=None, schenkel=1,
               bohrung=BOHRUNG_RUND):
    """Baut den Stein und raeumt auf, wenn dabei etwas schiefgeht.

    Scheitert ein Extrude mitten im Aufbau, bleibt sonst die halbfertige
    Komponente im Dokument stehen - mit Grundkoerper, Hohlraum und allem, was
    bis dahin geklappt hat. Weil die Vorschau bei jeder Eingabe neu laeuft,
    sammeln sich bei einem dauerhaft fehlschlagenden Zustand binnen Sekunden
    mehrere solcher Leichen im Browserbaum an.

    Der Fehler selbst wird weitergereicht: Die Vorschau meldet ihn, und
    stillschweigend ein halbes Teil zu liefern waere schlimmer.
    """
    root = design.rootComponent
    vorher = root.occurrences.count
    try:
        return _baue_stein(design, typ, nx, ny, profil_name, y_versatz, klemm,
                           ns, lage, justage, schenkel, bohrung)
    except Exception:
        try:
            while root.occurrences.count > vorher:
                root.occurrences.item(root.occurrences.count - 1).deleteMe()
        except Exception:
            # Das Aufraeumen darf den eigentlichen Fehler nicht verdecken.
            pass
        raise


def _baue_stein(design, typ, nx, ny, profil_name, y_versatz=0.0, klemm=None,
                ns=1, lage=None, justage=None, schenkel=1,
               bohrung=BOHRUNG_RUND):
    """Baut den Baustein als neue Komponente. Gibt (Occurrence, BRepBody) zurueck.

    Der Ursprung der Komponente liegt in der unteren, vorderen, linken Ecke:
    X = Laenge (Noppen), Y = Breite (Noppen), Z = Hoehe.

    Die Platzierung geht ueber eine vollstaendige Transformation: y_versatz
    ist nur die bequeme Abkuerzung fuer das Ablegen nebeneinander. Wer ein
    ganzes Modell zusammensetzen will, uebergibt stattdessen eine fertige
    Matrix in "lage" - inklusive Drehung. Die Geometrie selbst bleibt immer
    im Komponentenursprung.

    ns ist die Laenge der Schraege in Noppen und wirkt nur beim Schraegstein.

    justage traegt Druckerkalibrierung und Kantenbrechung. Ohne Angabe
    gelten die Werte aus dem Druckprofil - so verhaelt sich der Aufruf
    genau wie vor der Einfuehrung des Objekts.
    """
    p = PRINT_PROFILES[profil_name]
    gap = p['gap']
    wall = p['wall']
    if klemm is None:
        klemm = p['klemm']
    if justage is None:
        justage = Justage.aus_profil(p)

    # Ein Rundstein hat nur einen Durchmesser - zwei verschiedene Kantenlaengen
    # gaeben eine Ellipse, und die passt in kein Raster.
    if _ist_rund(typ):
        ny = nx
    w = _schenkel(nx, ny, schenkel)

    # Druckerkompensation. Ab hier ist jedes Mass ein MODELLmass, also das
    # gewuenschte Endmass plus Vorhalt - in Fusion nachgemessen faellt es
    # entsprechend groesser aus als die Werte in der Infozeile.
    fx, fy, fz = justage.fx, justage.fy, justage.fz
    fr = justage.f_rund
    k_rund = justage.rund
    k_loch = justage.loch

    # Klemmspiel wirkt auf die greifenden Flaechen: Noppe und Stege.
    # Die Roehren-AUSSENseite bleibt beim Nennmass, damit das Teil zu echten
    # Steinen passt; der Roehren-INNENdurchmesser folgt der Noppe, damit die
    # Noppe-in-Roehre-Verbindung weiter funktioniert.
    noppen_d = (STUD_D + klemm) * fr + k_rund
    steg_d = (PIN_D + klemm) * fr + k_rund
    tube_od = TUBE_OD * fr + k_rund
    rohr_id = (STUD_D + klemm + p['rohr']) * fr + k_loch

    # Hoehen folgen der Z-Achse, die Deckplatte aber NICHT: sie ist ein
    # Fertigungsmass und soll ihre Dicke behalten. Wuerde sie mitwachsen,
    # verschoebe sich die Kavitaetstiefe mit jeder Kalibrierung.
    hoehe = _hoehe(typ) * fz
    stud_h = STUD_H * fz
    schraeg_ende = SCHRAEG_ENDE * fz
    technic_z = TECHNIC_AXIS_Z * fz

    sx = (nx * PITCH - gap) * fx    # Aussenmass in X
    sy = (ny * PITCH - gap) * fy    # Aussenmass in Y
    kavitaet = hoehe - TOP_WALL     # Hoehe des Hohlraums an der Unterseite

    def raster_x(n):
        """Rasterposition in X (in Noppen gezaehlt) als Modellkoordinate."""
        return (n * PITCH - gap / 2.0) * fx

    def raster_y(n):
        return (n * PITCH - gap / 2.0) * fy

    root = design.rootComponent
    if lage is None:
        lage = adsk.core.Matrix3D.create()
        if abs(y_versatz) > 1e-9:
            lage.translation = adsk.core.Vector3D.create(0.0, y_versatz * MM, 0.0)
    occ = root.occurrences.addNewComponent(lage)
    comp = occ.component
    comp.name = '{} {}x{}'.format(typ, nx, ny)
    if typ in TYPEN_MIT_SCHRAEGE:
        comp.name += ' ({} Noppen Schraege)'.format(ns)

    op_neu = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    op_add = adsk.fusion.FeatureOperations.JoinFeatureOperation
    op_cut = adsk.fusion.FeatureOperations.CutFeatureOperation

    # --- 1. Grundkoerper -----------------------------------------------------
    # Der Eckradius sitzt bewusst schon in der Skizze und nicht in einem
    # Fillet hinterher: die senkrechte Aussenkante ist von Anfang an
    # bekannt, und eine verrundete Skizze kostet keine Rechenzeit.
    sk_basis = comp.sketches.add(comp.xYConstructionPlane)
    sk_basis.name = 'Grundriss'
    schenkel_mm = w * PITCH - gap / 2.0        # Aussenkante des L-Schenkels
    mitte = sx / 2.0                            # nur beim Rundstein gebraucht
    if _ist_rund(typ):
        # Der Eckradius ergibt beim Kreis keinen Sinn und wird still
        # uebergangen - die Kante ist ohnehin rundum gekruemmt.
        _kreis(sk_basis, mitte, mitte, sx)
    elif typ == TYP_ECK:
        _polygon(sk_basis, _l_polygon(sx, sy, schenkel_mm))
    elif justage.eckradius > 1e-9:
        _rundrechteck(sk_basis, 0.0, 0.0, sx, sy, justage.eckradius)
    else:
        _rechteck(sk_basis, 0.0, 0.0, sx, sy)
    body = _extrude(comp, sk_basis.profiles.item(0), 0.0, hoehe, op_neu).bodies.item(0)
    body.name = comp.name
    koerper = [body]

    # --- 1b. Schraege --------------------------------------------------------
    # Beim normalen Schraegstein faellt die Schraege zur Vorderkante (x = 0)
    # hin ab und laeuft auf Plattenhoehe aus; weggeschnitten wird oben.
    #
    # Der umgekehrte Schraegstein ist derselbe Keil an der Unterseite: oben
    # bleibt die volle Flaeche mit allen Noppen stehen, vorn bleibt nur noch
    # ein Streifen von Plattenhoehe. So schliessen die beiden Typen eine
    # Dachkante von oben und von unten ab.
    #
    # Das Schnittprofil steht absichtlich ueber den Koerper hinaus, damit der
    # Schnitt nicht tangential auf einer Flaeche endet - das mag kein
    # B-Rep-Kern.
    schraege_l = 0.0
    schraege_unten = (typ == TYP_SCHRAEG_INV)
    if typ in TYPEN_MIT_SCHRAEGE:
        schraege_l = min(ns, nx) * PITCH * fx
        sk_schraeg = comp.sketches.add(comp.xZConstructionPlane)
        sk_schraeg.name = 'Schraege'

        def _sp(x_mm, z_mm):
            return sk_schraeg.modelToSketchSpace(_pt(x_mm, 0.0, z_mm))

        if schraege_unten:
            ecken = [_sp(0.0, hoehe - schraeg_ende), _sp(schraege_l, 0.0),
                     _sp(schraege_l, -2.0), _sp(0.0, -2.0)]
        else:
            ecken = [_sp(0.0, schraeg_ende), _sp(schraege_l, hoehe),
                     _sp(schraege_l, hoehe + 2.0), _sp(0.0, hoehe + 2.0)]
        linien = sk_schraeg.sketchCurves.sketchLines
        for k in range(len(ecken)):
            linien.addByTwoPoints(ecken[k], ecken[(k + 1) % len(ecken)])
        _durchbruch(comp, _alle_profile(sk_schraeg), koerper)

    # --- 2. Hohlraum an der Unterseite --------------------------------------
    # Die Grundplatte bleibt massiv: sie ist zu duenn fuer Roehren und soll
    # nur von oben klemmen.
    #
    # Unter einer Schraege ist kein Platz fuer den vollen Hohlraum - die
    # Decke waere dort duenner als null. Statt den Bereich massiv zu lassen
    # (dann klemmt der Stein vorn nicht mehr) wird der Hohlraum abgestuft:
    # unter der Schraege nur so tief, wie die niedrigste Stelle es zulaesst.
    # Das reicht fuer die Noppe des darunterliegenden Steins mit Abstand,
    # und eine ebene Decke druckt sich ohnehin besser als eine schraege.
    #
    # Bei der umgekehrten Schraege ist unten vorn ueberhaupt kein Material
    # mehr - es wurde ja gerade weggeschnitten. Dort gibt es also nichts
    # auszuhoehlen und nichts, woran eine Roehre haengen koennte: flach_tiefe
    # null laesst beides von selbst entfallen.
    hat_hohlraum = (typ != TYP_GRUNDPLATTE and sx - 2 * wall > 0.1)
    flach_tiefe = 0.0 if schraege_unten else max(schraeg_ende - TOP_WALL, 0.0)
    if hat_hohlraum and _ist_rund(typ):
        sk_hohl = comp.sketches.add(comp.xYConstructionPlane)
        sk_hohl.name = 'Hohlraum'
        _kreis(sk_hohl, mitte, mitte, sx - 2 * wall)
        _extrude(comp, sk_hohl.profiles.item(0), 0.0, kavitaet, op_cut, koerper)

    elif hat_hohlraum and typ == TYP_ECK:
        # Dieselbe L-Form, jede Kante um die Wandstaerke nach innen. Bei
        # achsparallelen Kanten ist das schlicht ein Versatz der Koordinaten -
        # auch an der einspringenden Innenecke.
        sk_hohl = comp.sketches.add(comp.xYConstructionPlane)
        sk_hohl.name = 'Hohlraum'
        _polygon(sk_hohl, [(wall, wall), (sx - wall, wall),
                           (sx - wall, schenkel_mm - wall),
                           (schenkel_mm - wall, schenkel_mm - wall),
                           (schenkel_mm - wall, sy - wall), (wall, sy - wall)])
        _extrude(comp, sk_hohl.profiles.item(0), 0.0, kavitaet, op_cut, koerper)

    elif hat_hohlraum:
        stufen = []
        if typ in TYPEN_MIT_SCHRAEGE and schraege_l > wall:
            grenze = min(schraege_l, sx - wall)
            if flach_tiefe > stud_h + NOPPEN_LUFT:
                stufen.append((wall, grenze, flach_tiefe))
            if sx - wall > grenze + 0.1:
                stufen.append((grenze, sx - wall, kavitaet))
        else:
            stufen.append((wall, sx - wall, kavitaet))

        for index, (x0, x1, tiefe) in enumerate(stufen):
            sk_hohl = comp.sketches.add(comp.xYConstructionPlane)
            sk_hohl.name = 'Hohlraum {}'.format(index + 1) if len(stufen) > 1 else 'Hohlraum'
            _rechteck(sk_hohl, x0, wall, x1, sy - wall)
            _extrude(comp, sk_hohl.profiles.item(0), 0.0, tiefe, op_cut, koerper)

    # --- 3. Klemmgeometrie an der Unterseite ---------------------------------
    # Ab 2x2: Roehren auf den inneren Rasterkreuzen. Bei 1xN: schmale Stege.
    # Ueberall dort, wo ueber der Roehre volles Material steht, wird sie auf
    # volle Kavitaetshoehe gezogen; der Ueberstand verschmilzt einfach mit
    # dem Material darueber - die freie Laenge unten bleibt, und nur die
    # zaehlt. Unter einer Schraege gilt das nicht, siehe _roehren_hoehe.
    roehren = []
    stege = []
    if hat_hohlraum:
        roehren = [(raster_x(i), raster_y(j))
                   for i, j in _roehren_stellen(typ, nx, ny, w, gap, wall)]
        stege = [(raster_x(i), raster_y(j))
                 for i, j in _stege_stellen(typ, nx, ny)]

    # Nach Bauhoehe gruppieren: ohne Schraege ist das eine einzige Gruppe und
    # damit genau ein Skizzenpaar wie bisher.
    hoehen = {}
    for (x, y) in roehren:
        h = _roehren_hoehe(x, tube_od, schraege_l, kavitaet, flach_tiefe, stud_h)
        if h > 1e-9:
            hoehen.setdefault(round(h, 6), []).append((x, y))
    roehren = [stelle for gruppe in hoehen.values() for stelle in gruppe]

    for index, h in enumerate(sorted(hoehen)):
        zusatz = ' {}'.format(index + 1) if len(hoehen) > 1 else ''
        sk_aussen = comp.sketches.add(comp.xYConstructionPlane)
        sk_aussen.name = 'Roehren aussen' + zusatz
        for (x, y) in hoehen[h]:
            _kreis(sk_aussen, x, y, tube_od)
        _extrude(comp, _alle_profile(sk_aussen), 0.0, h, op_add, koerper)

        sk_innen = comp.sketches.add(comp.xYConstructionPlane)
        sk_innen.name = 'Roehren innen' + zusatz
        for (x, y) in hoehen[h]:
            _kreis(sk_innen, x, y, rohr_id)
        _extrude(comp, _alle_profile(sk_innen), 0.0, h, op_cut, koerper)

    if stege:
        sk_stege = comp.sketches.add(comp.xYConstructionPlane)
        sk_stege.name = 'Stege'
        for (x, y) in stege:
            _kreis(sk_stege, x, y, steg_d)
        _extrude(comp, _alle_profile(sk_stege), 0.0, kavitaet, op_add, koerper)

    # --- 4. Noppen (entfallen bei der Fliese) --------------------------------
    # Beim Schraegstein nur auf dem flachen Teil: eine Noppe auf der Schraege
    # waere weder rasterhaltig noch druckbar. Bei der umgekehrten Schraege
    # entfaellt dieser Filter - dort ist die Oberseite vollstaendig erhalten,
    # und gerade das macht den Typ nuetzlich.
    hat_noppen = False
    if typ not in TYPEN_OHNE_NOPPEN:
        # Der Schraegstein filtert ueber die Modellkoordinate, weil dort die
        # Kalibrierung mitspielt; alle anderen Filter stecken in _noppen_stellen.
        noppen_ab = 0.0 if schraege_unten else schraege_l
        stellen = [(raster_x(i), raster_y(j))
                   for i, j in _noppen_stellen(typ, nx, ny, w, gap)
                   if raster_x(i) >= noppen_ab]
        if stellen:
            sk_noppen = comp.sketches.add(comp.xYConstructionPlane)
            sk_noppen.name = 'Noppen'
            for (x, y) in stellen:
                _kreis(sk_noppen, x, y, noppen_d)
            _extrude(comp, _alle_profile(sk_noppen), hoehe, stud_h, op_add,
                     koerper)
            hat_noppen = True

    # --- 5. Technic-Querbohrungen -------------------------------------------
    # Skizze auf der XZ-Ebene (= vordere Stirnflaeche bei y = 0), Schnitt in Y.
    if typ in TYPEN_MIT_BOHRUNG:
        sk_loecher = comp.sketches.add(comp.xZConstructionPlane)
        sk_loecher.name = 'Technic-Bohrungen'
        # Nur der Schrumpf wird kompensiert: komp_loch beschreibt die duenne
        # Roehrenwand, die Querbohrung sitzt dagegen in vollem Material und
        # verhaelt sich anders. Solange dafuer keine Messung vorliegt, bleibt
        # es beim Spielmass aus dem Profil.
        technic_d = (TECHNIC_HOLE_D + p['hole']) * fr
        radius = technic_d / 2.0 * MM
        # Das Spielmass wirkt auf beide Bohrungsarten gleich: es beschreibt,
        # was der Drucker an einem Loch dieser Groesse zulegt.
        spanne = AXLE_SPAN * fr + p['hole']
        arm = AXLE_ARM * fr + p['hole']

        for i in range(nx):
            x = raster_x(i + 0.5)
            # Weltkoordinaten -> Skizzenkoordinaten: unabhaengig von der
            # Orientierung der XZ-Ebene und damit robust.
            if bohrung == BOHRUNG_ACHSE:
                _polygon(sk_loecher, _achskreuz(spanne, arm),
                         lambda dx, dz, _x=x: sk_loecher.modelToSketchSpace(
                             _pt(_x + dx, 0.0, technic_z + dz)))
            else:
                mittelpunkt = sk_loecher.modelToSketchSpace(
                    _pt(x, 0.0, technic_z))
                sk_loecher.sketchCurves.sketchCircles.addByCenterRadius(
                    mittelpunkt, radius)
        _durchbruch(comp, _alle_profile(sk_loecher), koerper)

    # --- 6. Kanten brechen ---------------------------------------------------
    # Ganz am Ende, damit die Kanten in ihrer endgueltigen Form vorliegen.
    # Jede Gruppe wird einzeln gesucht und einzeln angewendet: ein Feature
    # veraendert die Kantenliste des Koerpers, gemerkte Referenzen waeren
    # danach wertlos. Die geometrische Suche findet dagegen auch nach dem
    # vorigen Schritt noch, was sie sucht.
    if justage.bricht_kanten:
        wandstaerke = max((tube_od - rohr_id) / 2.0, 0.0)
        gruppen = []

        if roehren:
            mass = justage.kante_roehre(wandstaerke)
            gruppen.append(('Roehren unten', [(tube_od, 'z', 0.0),
                                              (rohr_id, 'z', 0.0)], mass))
        if stege:
            gruppen.append(('Stege unten', [(steg_d, 'z', 0.0)],
                            justage.kante_unten))
        if typ in TYPEN_MIT_BOHRUNG and bohrung == BOHRUNG_RUND:
            # Volles Material rundherum - hier bremst keine duenne Wand.
            # Das Achskreuz hat keine Kreiskanten und bleibt aussen vor;
            # eine Fase an seinen zwoelf Ecken waere ohnehin kaum druckbar.
            gruppen.append(('Technic-Bohrungen',
                            [(technic_d, 'y', 0.0), (technic_d, 'y', sy)],
                            justage.kante_unten))
        if hat_noppen:
            gruppen.append(('Noppen oben', [(noppen_d, 'z', hoehe + stud_h)],
                            justage.kante_noppe))

        misslungen = []
        for name, suchen, mass in gruppen:
            if mass <= 1e-9:
                continue
            kanten = []
            for durchmesser, achse, lage in suchen:
                kanten.extend(_kreiskanten(body, durchmesser, achse, lage))
            if kanten and not _brich_kanten(comp, kanten, mass, justage.methode):
                misslungen.append(name)

        # Scharf gebliebene Kanten sind aergerlich, aber kein Grund, das
        # fertige Teil wegzuwerfen. Gemeldet wird trotzdem - stillschweigend
        # ein anderes Ergebnis zu liefern waere schlimmer als die Meldung.
        if misslungen and app:
            app.log('Klemmbaustein: Kantenbrechung fehlgeschlagen bei {} '
                    '(Mass zu gross fuer die Geometrie?)'.format(
                        ', '.join(misslungen)))

    return occ, body


# ---------------------------------------------------------------------------
# STL-Export
# ---------------------------------------------------------------------------
# Der Export selbst liegt im Basismodul; hier steht nur noch die Namensgebung.

def _dateiname(typ, nx, ny, klemm=0.0, profil_name=None, ns=None, justage=None,
               schenkel=None, bohrung=BOHRUNG_RUND):
    # Klemmspiel im Namen, damit Kalibrierdrucke unterscheidbar bleiben:
    # k00 = Nennmass, k05 = +0,05 mm, km08 = -0,08 mm.
    kuerzel = 'k{}{:02d}'.format('m' if klemm < 0 else '', int(round(abs(klemm) * 100)))
    masse = '{}x{}'.format(nx, ny) if not _ist_rund(typ) else 'd{}'.format(nx)
    if typ in TYPEN_MIT_SCHRAEGE and ns:
        masse += 's{}'.format(min(ns, nx))
    if typ == TYP_ECK and schenkel:
        masse += 'L{}'.format(_schenkel(nx, ny, schenkel))
    if typ in TYPEN_MIT_BOHRUNG and bohrung == BOHRUNG_ACHSE:
        masse += 'ax'
    basis = '{}_{}_{}'.format(typ.replace(' ', '_'), masse, kuerzel)
    # Kompensierte und gebrochene Teile markieren, sonst landet der
    # Vergleichsdruck aus zwei Einstellungen unter demselben Namen und wird
    # nur durchnummeriert - beim Auswerten weiss dann niemand mehr, welche
    # Datei welche Variante war.
    if justage is None:
        p = PRINT_PROFILES.get(profil_name or '', {})
        justage = Justage.aus_profil(p)
    if justage.ist_aktiv:
        basis += '_komp'
    if justage.bricht_kanten:
        grob = max(justage.kante_unten, justage.kante_noppe, justage.eckradius)
        basis += '_{}{:02d}'.format(
            'r' if justage.methode == METHODE_RADIUS else 'f',
            int(round(grob * 100)))
    return ''.join(c for c in basis if c.isalnum() or c in ('_', '-'))


# ---------------------------------------------------------------------------
# Zustand aus dem Dialog lesen
# ---------------------------------------------------------------------------

class Einstellungen(object):
    def __init__(self, inputs):
        def mm(ident):
            return _finde(inputs, ident).value / MM   # intern cm -> mm

        self.typ = _finde(inputs, IN_TYP).selectedItem.name
        self.nx = _finde(inputs, IN_LAENGE).value
        self.ny = _finde(inputs, IN_BREITE).value
        self.ns = _finde(inputs, IN_SCHRAEGE).value
        self.schenkel = _finde(inputs, IN_SCHENKEL).value
        self.bohrung = _finde(inputs, IN_BOHRUNG).selectedItem.name
        self.profil = _finde(inputs, IN_PROFIL).selectedItem.name
        self.klemm = mm(IN_KLEMM)
        self.vorschau = _finde(inputs, IN_VORSCHAU).value
        self.wiederholen = _finde(inputs, IN_WIEDERHOLEN).value
        self.anordnen = _finde(inputs, IN_ANORDNEN).value
        self.stl_an = _finde(inputs, IN_STL_AN).value
        self.stl_ordner = _finde(inputs, IN_STL_ORDNER).value.strip()

        self.methode = _finde(inputs, IN_KANTE_METHODE).selectedItem.name
        self.kante_unten = mm(IN_KANTE_UNTEN)
        self.kante_noppe = mm(IN_KANTE_NOPPE)
        self.eckradius = mm(IN_ECKRADIUS)

        self.kal_koppeln = _finde(inputs, IN_KAL_KOPPELN).value
        self.kal_x_soll = mm(IN_KAL_X_SOLL)
        self.kal_x_ist = mm(IN_KAL_X_IST)
        self.kal_y_soll = mm(IN_KAL_Y_SOLL)
        self.kal_y_ist = mm(IN_KAL_Y_IST)
        self.kal_z_soll = mm(IN_KAL_Z_SOLL)
        self.kal_z_ist = mm(IN_KAL_Z_IST)
        self.kal_rund = mm(IN_KAL_RUND)

        # Werte merken, damit der naechste Dialog damit startet.
        _letzte.update(self.__dict__)

    def justage(self):
        """Baut daraus das Objekt, mit dem die Geometrie arbeitet.

        Die Kalibrierfelder gewinnen immer gegen das Druckprofil: sie
        beschreiben den Drucker, der vor dem Nutzer steht. Das Profil liefert
        beim Wechseln nur noch Startwerte - stuenden beide gleichzeitig in
        Kraft, wuerde doppelt kompensiert.
        """
        fx = _faktor(self.kal_x_soll, self.kal_x_ist)
        fy = fx if self.kal_koppeln else _faktor(self.kal_y_soll, self.kal_y_ist)
        fz = _faktor(self.kal_z_soll, self.kal_z_ist)
        p = PRINT_PROFILES[self.profil]
        return Justage(fx=fx, fy=fy, fz=fz,
                       rund=self.kal_rund, loch=p.get('komp_loch', 0.0),
                       methode=self.methode,
                       kante_unten=self.kante_unten,
                       kante_noppe=self.kante_noppe,
                       eckradius=self.eckradius)


def _info_text(typ, nx, ny, profil_name, klemm=None, ns=1, justage=None,
               vorschau_reduziert=False, schenkel=1, bohrung=BOHRUNG_RUND):
    p = PRINT_PROFILES[profil_name]
    if klemm is None:
        klemm = p['klemm']
    if justage is None:
        justage = Justage.aus_profil(p)
    if _ist_rund(typ):
        ny = nx
    w = _schenkel(nx, ny, schenkel)
    noppen = len(_noppen_stellen(typ, nx, ny, w, p['gap'], min(ns, nx)))

    # Alle Masse hier sind die des Modells, also mit Kalibrierung - sonst
    # zeigte die Zeile weiter das Nennmass an, waehrend Fusion laengst etwas
    # anderes baut, und man saehe der Kalibrierung nicht an, ob sie wirkt.
    fr, k_rund = justage.f_rund, justage.rund
    soll_x = nx * PITCH - p['gap']
    soll_y = ny * PITCH - p['gap']
    soll_h = _hoehe(typ)
    sx = soll_x * justage.fx
    sy = soll_y * justage.fy
    hoehe = soll_h * justage.fz
    noppen_d = (STUD_D + klemm) * fr + k_rund

    # Rest zwischen Noppe und Roehre: positiv = Luft, negativ = Uebermass.
    # Der Abstand der beiden Mittelpunkte waechst mit der Kalibrierung mit,
    # die Durchmesser ebenso - ein reiner Prozentfaktor verschiebt die
    # Klemmung deshalb kaum. Das Rundungs-Aufmass ist dagegen ein fester
    # Betrag und schlaegt voll durch.
    rest = KLEMM_TANGENTE * fr - (noppen_d / 2.0 + (TUBE_OD * fr + k_rund) / 2.0)
    if rest > 0.015:
        urteil, farbe = 'locker', FARBE_WARN
    elif rest < -0.015:
        urteil, farbe = 'stramm', FARBE_FEHLER
    else:
        urteil, farbe = 'Nennmass', FARBE_GUT

    kopf = ('<b>Aussenmass:</b> &oslash; {} &times; {} mm hoch'.format(
                _de(sx), _de(hoehe)) if _ist_rund(typ) else
            '<b>Aussenmass:</b> {} &times; {} &times; {} mm'.format(
                _de(sx), _de(sy), _de(hoehe)))
    zeilen = [
        kopf,
        # Rastermass daneben, weil sonst genau der Denkfehler passiert, der
        # eine Kalibrierung ruiniert: 2 Noppen sind 16,00 mm Raster, aber
        # 15,80 mm Aussenmass. Die 0,20 mm sind gewollt, damit Steine
        # nebeneinander passen - wer dagegen misst, korrigiert ein Spielmass
        # weg, das der Konstruktion gehoert.
        '<b>Raster:</b> {} &times; {} mm &ndash; das Aussenmass liegt '
        'konstruktiv {} mm darunter'.format(
            _de(nx * PITCH), _de(ny * PITCH), _de(p['gap'])),
        '<b>Noppen:</b> {} &times; &oslash; {} mm &nbsp;|&nbsp; '
        '<b>Wand:</b> {} mm'.format(noppen, _de(noppen_d), _de(p['wall'])),
        '<b>Klemmung:</b> {}'.format(
            _farbig('{} mm Luft am Kontakt ({})'.format(_de(rest, 3), urteil),
                    farbe)),
    ]
    # Die Masse oben sind die des MODELLS, also das, was Fusion tatsaechlich
    # baut und was ein Messen im Modell ergibt. Bei aktiver Kompensation ist
    # das absichtlich groesser als das Zielmass - deshalb steht das Zielmass
    # hier daneben, sonst weiss man nicht mehr, worauf man hinauswill.
    if justage.ist_aktiv:
        zeilen.append(
            '<b>Nach dem Druck erwartet:</b> {} mm &ndash; {}'.format(
                '{} &times; {} mm hoch'.format(_de(soll_x), _de(soll_h))
                if _ist_rund(typ) else
                '{} &times; {} &times; {}'.format(
                    _de(soll_x), _de(soll_y), _de(soll_h)),
                _farbig('so viel kleiner druckt dein Drucker das Modell '
                        'wieder.', FARBE_LEISE)))
        zeilen.append(
            '<b>Kalibrierung:</b> X {} % &nbsp;|&nbsp; Y {} % &nbsp;|&nbsp; '
            'Z {} % &nbsp;|&nbsp; Rundungen +{} mm '
            '(im Modell bereits aufgeschlagen)'.format(
                _de((justage.fx - 1.0) * 100.0, 3),
                _de((justage.fy - 1.0) * 100.0, 3),
                _de((justage.fz - 1.0) * 100.0, 3),
                _de(justage.rund)))
        if abs(justage.fx - justage.fy) > FAKTOR_DIFF_WARNUNG:
            zeilen.append(_farbig(
                '<b>Achtung:</b> X und Y weichen um {} % voneinander ab. Der '
                'Klemmkontakt liegt diagonal und hat nur 0,002 mm Reserve &ndash; '
                'ab hier passt die runde Noppe nicht mehr sauber zur Roehre.'.format(
                    _de(abs(justage.fx - justage.fy) * 100.0, 3)), FARBE_FEHLER))

    if justage.bricht_kanten:
        art = 'Radius' if justage.methode == METHODE_RADIUS else 'Fase'
        teile = []
        if justage.kante_unten > 1e-9:
            teile.append('unten {} mm'.format(_de(justage.kante_unten)))
        if justage.kante_noppe > 1e-9:
            teile.append('Noppe {} mm'.format(_de(justage.kante_noppe)))
        if justage.eckradius > 1e-9:
            teile.append('Ecken r{} mm'.format(_de(justage.eckradius)))
        zeilen.append('<b>Kanten ({}):</b> {}'.format(art, ' &nbsp;|&nbsp; '.join(teile)))

        if justage.kante_noppe > KANTE_NOPPE_WARNUNG:
            verlust = justage.kante_noppe / STUD_H * 100.0
            zeilen.append(_farbig(
                '<b>Achtung:</b> Die Noppe ist nur {} mm hoch &ndash; die '
                'Kantenbrechung nimmt {} % der Klemmflaeche weg.'.format(
                    _de(STUD_H), _de(verlust, 0)), FARBE_WARN))

        if vorschau_reduziert:
            zeilen.append(
                'Zu viele Kanten fuer die Live-Vorschau &ndash; sie zeigt das '
                'Teil scharfkantig. "Erzeugen" bricht die Kanten trotzdem.')
    if typ in TYPEN_MIT_BOHRUNG:
        if bohrung == BOHRUNG_ACHSE:
            zeilen.append(
                '<b>Achskreuz:</b> {} &times; {} mm Spannweite, {} mm Stegbreite, '
                'auf {} mm Hoehe &ndash; haelt die Achse formschluessig.'.format(
                    nx, _de(AXLE_SPAN + p['hole']), _de(AXLE_ARM + p['hole']),
                    _de(TECHNIC_AXIS_Z)))
        else:
            zeilen.append(
                '<b>Querbohrungen:</b> {} &times; &oslash; {} mm auf {} mm Hoehe'.format(
                    nx, _de(TECHNIC_HOLE_D + p['hole']), _de(TECHNIC_AXIS_Z)))
        if hoehe - TECHNIC_AXIS_Z < TECHNIC_HOLE_D / 2.0:
            zeilen.append(_farbig(
                '<b>Achtung:</b> Die Bohrungsachse liegt auf {} mm, das Teil ist '
                'nur {} mm hoch &ndash; die Bohrung bricht oben aus.'.format(
                    _de(TECHNIC_AXIS_Z), _de(hoehe)), FARBE_FEHLER))
    if typ == TYP_FLIESE:
        zeilen.append('Glatte Oberseite ohne Noppen.')
    if typ == TYP_LOCHBALKEN:
        zeilen.append('Glatte Oberseite ohne Noppen, Klemmung nur an der Unterseite.')
    if typ == TYP_HALBSTEIN:
        zeilen.append('Halbe Steinhoehe &ndash; zwei davon ergeben einen Stein, '
                      'drei Platten ergeben ebenfalls {} mm.'.format(_de(BRICK_H)))
    if typ == TYP_ECK:
        zeilen.append(
            '<b>L-Form:</b> Schenkelbreite {} Noppen ({} mm). Ein Schenkel '
            'laeuft ueber die volle Laenge, der andere ueber die volle Breite.'.format(
                w, _de(w * PITCH - p['gap'] / 2.0)))
        if w != schenkel:
            zeilen.append(
                'Die Schenkelbreite wurde auf {} begrenzt &ndash; breiter waere '
                'es kein L mehr.'.format(w))
    if _ist_rund(typ):
        zeilen.append(
            'Runder Grundriss, {} Noppen im Durchmesser. Breite folgt der '
            'Laenge; Noppen und Roehren, die ueber den Rand ragen wuerden, '
            'entfallen.'.format(nx))
    if typ in TYPEN_MIT_SCHRAEGE:
        wirksam = min(ns, nx)
        zeilen.append(
            '<b>Schraege:</b> {} Noppen, {}&deg; &nbsp;|&nbsp; {} von {} '
            'auf {} mm'.format(wirksam,
                               _de(_schraegen_winkel(wirksam, hoehe, SCHRAEG_ENDE), 1),
                               'steigt' if typ == TYP_SCHRAEG_INV else 'faellt',
                               _de(hoehe), _de(SCHRAEG_ENDE)))
        if typ == TYP_SCHRAEG_INV:
            zeilen.append(
                'Weggeschnitten wird an der <b>Unterseite</b> - oben bleibt '
                'die volle Flaeche mit allen Noppen. Unter der Schraege gibt '
                'es dafuer keine Roehren, dort klemmt das Teil nicht.')
        elif wirksam >= nx:
            zeilen.append('Die Schraege nimmt die ganze Laenge ein - keine '
                          'Noppen auf der Oberseite.')
    if typ == TYP_GRUNDPLATTE:
        zeilen.append('Massiv, {} mm dick, ohne Klemmung an der Unterseite.'.format(
            _de(GRUNDPLATTE_H)))
    if typ == TYP_JUMPER:
        zeilen.append(
            'Noppen um ein halbes Raster ({} mm) versetzt - sie sitzen auf den '
            'Rasterkreuzen statt in den Feldmitten.'.format(_de(PITCH / 2.0)))
        # Wer einen Jumper baut, will etwas Kleines daraufsetzen. Dass die
        # 1x1-Platte dafuer nicht taugt, faellt sonst erst nach dem Druck auf.
        innen = PITCH - p['gap'] - 2 * p['wall']
        luft = innen - (STUD_D + klemm)
        if luft > 0.05:
            zeilen.append(
                '<b>Beachte:</b> Eine 1x1-Platte klemmt auf dieser Noppe nicht &ndash; '
                'ihr Hohlraum ist {} mm weit, die Noppe {} mm dick ({} mm Luft). '
                'Dafuer braeuchte es {} mm Wandstaerke statt {} mm. '
                'Ein 1x2-Teil greift dagegen mit seinem Steg.'.format(
                    _de(innen), _de(STUD_D + klemm), _de(luft),
                    _de((PITCH - p['gap'] - (STUD_D + klemm)) / 2.0), _de(p['wall'])))
    return '<br/>'.join(zeilen)


def _aktualisiere_info(inputs):
    try:
        cfg = Einstellungen(inputs)
        justage = cfg.justage()
        reduziert = (cfg.vorschau and justage.bricht_kanten
                     and _kantenzahl(cfg.typ, cfg.nx, cfg.ny,
                                     cfg.schenkel) > VORSCHAU_KANTEN_GRENZE)
        _finde(inputs, IN_INFO).formattedText = _info_text(
            cfg.typ, cfg.nx, cfg.ny, cfg.profil, cfg.klemm, cfg.ns,
            justage, reduziert, cfg.schenkel, cfg.bohrung)
        _finde(inputs, IN_KAL_INFO).formattedText = _kalibrier_text(cfg)
    except Exception:
        pass


def _kalibrier_text(cfg):
    """Zeigt, was aus den Messwerten geworden ist.

    Ohne diese Rueckmeldung tippt man Zahlenpaare ein und sieht nie, ob
    daraus ein plausibler Faktor wurde oder ob die Grenze gegriffen hat.
    """
    j = cfg.justage()
    if not j.ist_aktiv:
        return ('Beide Felder einer Achse leer lassen = nicht kalibriert. '
                'Sonst links das Mass eintragen, das im Modell steht '
                '(Zeile "Aussenmass"), rechts das nachgemessene.')

    zeilen = ['<b>X</b> {} % &nbsp;|&nbsp; <b>Y</b> {} % &nbsp;|&nbsp; '
              '<b>Z</b> {} % Vorhalt'.format(
                  _de((j.fx - 1.0) * 100.0, 3),
                  _de((j.fy - 1.0) * 100.0, 3),
                  _de((j.fz - 1.0) * 100.0, 3))]

    # Wer an die Grenze stoesst, hat kein Schrumpfproblem, sondern ein
    # Druckerproblem. Das im Modell auszugleichen verschiebt den Fehler nur.
    for name, faktor in (('X', j.fx), ('Y', j.fy), ('Z', j.fz)):
        if faktor in (FAKTOR_MIN, FAKTOR_MAX):
            zeilen.append(
                '<b>{}:</b> Grenze von 2 % erreicht. Eine so grosse Abweichung '
                'ist kein Schrumpf mehr &ndash; das gehoert in die '
                'Schrittweite oder die Extrusionsbreite des Druckers.'.format(name))

    if abs(j.fz - 1.0) > 1e-9:
        zeilen.append(
            'Z laesst sich nur begrenzt korrigieren: die Hoehe ist '
            'Schichtzahl mal Schichthoehe. Eine Schichthoehe waehlen, die '
            '3,2 mm teilt (0,10 / 0,16 / 0,20 / 0,32) &ndash; sonst rundet der '
            'Slicer, und kein Faktor holt das zurueck.')

    return '<br/>'.join(zeilen)


def _profil_uebernehmen(inputs, profil):
    """Schreibt die Vorgabewerte eines Druckprofils in die Felder.

    Die Profile bringen ihre Kompensation als Prozentwert mit, der Dialog
    arbeitet mit Messwertpaaren. Umgerechnet auf 100 mm ist der Zusammenhang
    fuer jeden nachvollziehbar: 0,24 % Schrumpf heisst, aus 100,00 mm werden
    99,76 mm.

    Wichtig ist vor allem, dass hier ueberhaupt geschrieben wird - auch die
    Nullen. Sonst blieben die Felder eines kalibrierten Profils stehen,
    nachdem man auf ein unkalibriertes gewechselt hat, und der Vorhalt
    wirkte weiter, ohne dass ihn noch jemand im Profil vermutet.
    """
    klemm_in = _finde(inputs, IN_KLEMM)
    if klemm_in:
        klemm_in.value = profil['klemm'] * MM

    prozent = profil.get('komp_schrumpf', 0.0)
    if abs(prozent) > 1e-9:
        soll, ist = 100.0, 100.0 * (1.0 - prozent / 100.0)
    else:
        soll, ist = 0.0, 0.0

    for ident, wert in ((IN_KAL_X_SOLL, soll), (IN_KAL_X_IST, ist),
                        (IN_KAL_Y_SOLL, soll), (IN_KAL_Y_IST, ist),
                        (IN_KAL_RUND, profil.get('komp_rund', 0.0))):
        feld = _finde(inputs, ident)
        if feld:
            feld.value = wert * MM


def _uebernahme_werte(typ, nx, ny, profil_name, justage):
    """Welche Werte der Knopf "Modellmass uebernehmen" eintragen wuerde.

    Als eigene Funktion, weil hier der Fehler steckte, der sich real gezeigt
    hat: Wird nur das Sollmass gesetzt, waechst der Faktor bei jedem Druck.
    Eine Pruefung, die bloss die Formel danebenrechnet, faengt einen Rueckfall
    nicht - sie muss diese Rechnung selbst durchlaufen.

    Liefert je Achse (Feld-ID Soll, Feld-ID Ist, Modellmass, Faktor). Das
    Istmass ergibt sich als Modellmass/Faktor und haelt den Faktor damit
    konstant: der Knopf verschiebt nur die Bezugsgroesse.
    """
    p = PRINT_PROFILES[profil_name]
    ny = nx if _ist_rund(typ) else ny
    return ((IN_KAL_X_SOLL, IN_KAL_X_IST,
             (nx * PITCH - p['gap']) * justage.fx, justage.fx),
            (IN_KAL_Y_SOLL, IN_KAL_Y_IST,
             (ny * PITCH - p['gap']) * justage.fy, justage.fy),
            (IN_KAL_Z_SOLL, IN_KAL_Z_IST,
             _hoehe(typ) * justage.fz, justage.fz))


def _modellmass_uebernehmen(inputs):
    """Traegt die aktuellen Modellmasse in die drei Soll-Felder ein.

    Beim Nachkalibrieren braucht der Faktor als Bezug das Mass, das Fusion
    gerade baut - nicht das gewuenschte Endmass. Wer dort das Endmass
    eintraegt, wirft den bisherigen Vorhalt weg und kompensiert nur noch den
    Rest. Von Hand ist das eine Fehlerquelle, also uebernimmt es der Knopf.

    Bewusst nur auf Knopfdruck und nicht automatisch: gemessen wird oft an
    einem anderen Teil als dem gerade eingestellten, und ein stilles
    Ueberschreiben der Referenz waere schlimmer als eine Handeingabe.

    Beide Felder werden gesetzt, nicht nur das linke - sonst schaukelt sich
    der Knopf hoch: Das neue Sollmass enthaelt bereits den geltenden Faktor,
    das alte Istmass stammt aber noch vom Druck davor. Aus dem Paar wuerde
    ein groesserer Faktor, daraus beim naechsten Druck ein noch groesseres
    Modellmass, und so fort. Indem das Istmass im selben Verhaeltnis
    mitwandert, bleibt der Faktor exakt, wo er war: Der Knopf aendert dann
    nur die Bezugsgroesse, und mehrfaches Druecken tut nichts.
    """
    cfg = Einstellungen(inputs)
    for ident_soll, ident_ist, modell, faktor in _uebernahme_werte(
            cfg.typ, cfg.nx, cfg.ny, cfg.profil, cfg.justage()):
        f_soll = _finde(inputs, ident_soll)
        f_ist = _finde(inputs, ident_ist)
        if not f_soll or not f_ist:
            continue
        # Eine Achse mit zwei leeren Feldern ist bewusst nicht kalibriert -
        # etwa die Hoehe, wenn der Fehler dort aus der ersten Schicht kommt
        # und ein Faktor nur schaden wuerde. Die bleibt leer.
        if f_soll.value <= 1e-9 and f_ist.value <= 1e-9:
            continue
        f_soll.value = modell * MM
        # faktor ist nie 0: _faktor liefert bei leeren Feldern 1,0.
        f_ist.value = modell / faktor * MM


def _sichtbarkeit(inputs):
    """Blendet aus, was zum gewaehlten Typ nicht passt."""
    try:
        typ = _finde(inputs, IN_TYP).selectedItem.name
        _finde(inputs, IN_SCHRAEGE).isVisible = (typ in TYPEN_MIT_SCHRAEGE)
        _finde(inputs, IN_SCHENKEL).isVisible = (typ == TYP_ECK)
        _finde(inputs, IN_BOHRUNG).isVisible = (typ in TYPEN_MIT_BOHRUNG)
        # Die Noppen-Kantenbrechung braucht Noppen.
        _finde(inputs, IN_KANTE_NOPPE).isVisible = (typ not in TYPEN_OHNE_NOPPEN)
        # Der Rundstein ist rundum gekruemmt - ein Eckradius findet dort
        # keine Kante, und die Breite folgt zwangslaeufig der Laenge.
        _finde(inputs, IN_ECKRADIUS).isVisible = not _ist_rund(typ)
        _finde(inputs, IN_BREITE).isVisible = not _ist_rund(typ)

        # Bei gekoppelten Achsen sind die Y-Felder nur Anzeige - sie
        # bearbeitbar zu lassen, waere eine stille Luege.
        gekoppelt = _finde(inputs, IN_KAL_KOPPELN).value
        _finde(inputs, IN_KAL_Y_SOLL).isEnabled = not gekoppelt
        _finde(inputs, IN_KAL_Y_IST).isEnabled = not gekoppelt
        # Die Grundplatte klemmt nur von oben - das Klemmspiel wirkt dort
        # ausschliesslich auf die Noppen, bleibt also sinnvoll.
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Event-Handler
# ---------------------------------------------------------------------------

class KlemmbausteinCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    """Baut den Dialog auf und registriert alle weiteren Handler."""

    def notify(self, args):
        try:
            cmd = adsk.core.Command.cast(args.command)
            cmd.okButtonText = 'Erzeugen'
            cmd.isExecutedWhenPreEmpted = False
            cmd.helpFile = ''
            inputs = cmd.commandInputs

            profil_namen = list(PRINT_PROFILES.keys())
            start_typ = _letzte.get('typ', TYP_STEIN)
            if start_typ not in TYPEN:
                start_typ = TYP_STEIN
            start_profil = _letzte.get('profil', profil_namen[0])
            if start_profil not in PRINT_PROFILES:
                start_profil = profil_namen[0]
            start_nx = _ganzzahl('nx', 4, 1, MAX_NOPPEN)
            start_ny = _ganzzahl('ny', 2, 1, MAX_NOPPEN)

            # --- Bauteiltyp -------------------------------------------------
            typ_dd = inputs.addDropDownCommandInput(
                IN_TYP, 'Bauteiltyp',
                adsk.core.DropDownStyles.TextListDropDownStyle)
            for name in TYPEN:
                typ_dd.listItems.add(name, name == start_typ, '')
            # Alle Typen, nicht nur die gelaeufigen: gerade die exotischen
            # brauchen die Erklaerung schon beim Durchblaettern der Liste,
            # nicht erst nach dem Auswaehlen.
            typ_dd.tooltip = (
                'Stein = 9,6 mm hoch  |  Halbstein = 4,8 mm, zwei ergeben '
                'einen Stein  |  Platte = 3,2 mm, drei ergeben einen Stein  |  '
                'Fliese = Platte ohne Noppen  |  Jumper-Platte = Noppen um ein '
                'halbes Raster (4 mm) versetzt\n\n'
                'Technic-Stein = Stein mit Querbohrungen  |  '
                'Technic-Lochbalken = Querbohrungen ohne Noppen\n\n'
                'Schraegstein = faellt zur Vorderkante ab, ergibt die '
                'Dachflaeche  |  Schraegstein umgekehrt = derselbe Keil an der '
                'Unterseite, schliesst die Dachkante von unten ab und behaelt '
                'oben alle Noppen\n\n'
                'Eckstein = L-Form, die Schenkelbreite ist einstellbar  |  '
                'Rundstein = runder Grundriss, die Breite folgt der Laenge  |  '
                'Rundplatte = flach mit Noppen  |  Rundfliese = flach und '
                'glatt  |  Grundplatte = 1,6 mm massiv, klemmt nur von oben.')

            # --- Groesse ----------------------------------------------------
            laenge = inputs.addIntegerSpinnerCommandInput(
                IN_LAENGE, 'Laenge (Noppen)', 1, MAX_NOPPEN, 1, start_nx)
            laenge.tooltip = 'Anzahl Noppen in X-Richtung (Rastermass 8 mm).'

            breite = inputs.addIntegerSpinnerCommandInput(
                IN_BREITE, 'Breite (Noppen)', 1, MAX_NOPPEN, 1, start_ny)
            breite.tooltip = 'Anzahl Noppen in Y-Richtung (Rastermass 8 mm).'

            # --- Schraege ---------------------------------------------------
            schraege = inputs.addIntegerSpinnerCommandInput(
                IN_SCHRAEGE, 'Schraege (Noppen)', 1, MAX_SCHRAEGE, 1,
                _ganzzahl('ns', 2, 1, MAX_SCHRAEGE))
            schraege.tooltip = (
                'Ueber wie viele Noppen die Schraege abfaellt. Der Winkel '
                'ergibt sich daraus und wird unten angezeigt - die Schraege '
                'muss ueber ganze Noppen laufen, sonst sitzen die Noppen der '
                'Oberseite nicht mehr im Raster.')

            # --- Schenkel (Eckstein) ----------------------------------------
            schenkel_in = inputs.addIntegerSpinnerCommandInput(
                IN_SCHENKEL, 'Schenkelbreite (Noppen)', 1, MAX_SCHENKEL, 1,
                _ganzzahl('schenkel', 1, 1, MAX_SCHENKEL))
            schenkel_in.tooltip = (
                'Wie breit die beiden Schenkel des L sind. Hoechstens eine '
                'Noppe weniger als die schmalere Seite - sonst waere es kein '
                'L mehr, sondern ein Quader.')

            # --- Bohrungsart (Technic) --------------------------------------
            start_bohrung = _letzte.get('bohrung', BOHRUNG_RUND)
            if start_bohrung not in BOHRUNGEN:
                start_bohrung = BOHRUNG_RUND
            bohrung_dd = inputs.addDropDownCommandInput(
                IN_BOHRUNG, 'Bohrung',
                adsk.core.DropDownStyles.TextListDropDownStyle)
            for name in BOHRUNGEN:
                bohrung_dd.listItems.add(name, name == start_bohrung, '')
            bohrung_dd.tooltip = (
                'Rundloch nimmt Pins auf und laesst Achsen frei drehen. '
                'Das Achskreuz greift die Achse formschluessig - sie dreht '
                'dann mit dem Bauteil mit.')

            # --- Druckprofil ------------------------------------------------
            profil_dd = inputs.addDropDownCommandInput(
                IN_PROFIL, 'Druckprofil',
                adsk.core.DropDownStyles.TextListDropDownStyle)
            for name in profil_namen:
                profil_dd.listItems.add(name, name == start_profil, '')
            profil_dd.tooltip = ('Legt Spielmasse, Wandstaerke und '
                                 'STL-Netzqualitaet fest. Setzt beim Wechseln '
                                 'auch das Klemmspiel auf seinen Vorgabewert.')

            # --- Klemmspiel -------------------------------------------------
            try:
                start_klemm = float(_letzte.get('klemm',
                                                PRINT_PROFILES[start_profil]['klemm']))
            except (TypeError, ValueError):
                start_klemm = PRINT_PROFILES[start_profil]['klemm']
            start_klemm = max(KLEMM_MIN, min(KLEMM_MAX, start_klemm))
            klemm_in = inputs.addValueInput(
                IN_KLEMM, 'Klemmspiel', 'mm',
                adsk.core.ValueInput.createByReal(start_klemm * MM))
            klemm_in.tooltip = (
                'Aufmass auf Noppen und Stege. 0 = Nennmass des '
                'Klemmbaustein-Rasters (Noppe 4,80 mm), dort beruehren sich '
                'Noppe und Roehre gerade eben. '
                'Positiv = strammer, negativ = leichtgaengiger. '
                'Sinnvoller Bereich: -0,10 bis +0,10 mm.')

            # --- Vorschau ---------------------------------------------------
            vorschau = inputs.addBoolValueInput(IN_VORSCHAU, 'Live-Vorschau', True, '',
                                                _letzte.get('vorschau', True))
            vorschau.tooltip = ('Zeigt das Ergebnis waehrend der Eingabe. Bei sehr '
                                'grossen Bausteinen zum Beschleunigen abschalten.')

            # --- Infozeile --------------------------------------------------
            inputs.addTextBoxCommandInput(
                IN_INFO, 'Abmessungen',
                _info_text(start_typ, start_nx, start_ny, start_profil,
                           start_klemm, _ganzzahl('ns', 2, 1, MAX_SCHRAEGE)),
                8, True)

            # --- Kanten brechen ---------------------------------------------
            kanten = inputs.addGroupCommandInput(IN_KANTE_GRP, 'Kanten brechen')
            kanten_kinder = kanten.children

            start_methode = _letzte.get('methode', METHODE_FASE)
            if start_methode not in METHODEN:
                start_methode = METHODE_FASE
            methode_dd = kanten_kinder.addDropDownCommandInput(
                IN_KANTE_METHODE, 'Art',
                adsk.core.DropDownStyles.TextListDropDownStyle)
            for name in METHODEN:
                methode_dd.listItems.add(name, name == start_methode, '')
            methode_dd.tooltip = (
                'Fase druckt sich an waagerechten Kanten sauberer: ein Radius '
                'wird dort zur Stufentreppe. Radius sieht besser aus und ist '
                'an den senkrechten Aussenkanten die richtige Wahl.')

            k_unten = kanten_kinder.addValueInput(
                IN_KANTE_UNTEN, 'Einfuehrkante unten', 'mm',
                adsk.core.ValueInput.createByReal(
                    _konfig.zahl('kante_unten', 0.0, 0.0, KANTE_MAX) * MM))
            k_unten.tooltip = (
                'Bricht die Unterkante von Roehren, Stegen und Technic-Bohrungen. '
                'Das ist die Einfuehrhilfe, die das Zusammenstecken leichtgaengig '
                'macht - hier kostet sie nichts, weil die Kavitaet mit 8,6 mm '
                'viel tiefer ist als die 1,8 mm hohe Noppe. '
                'Sinnvoll: 0,20 bis 0,30 mm.')

            k_noppe = kanten_kinder.addValueInput(
                IN_KANTE_NOPPE, 'Einfuehrkante Noppe', 'mm',
                adsk.core.ValueInput.createByReal(
                    _konfig.zahl('kante_noppe', 0.0, 0.0, KANTE_NOPPE_MAX) * MM))
            k_noppe.tooltip = (
                'Bricht die Oberkante der Noppe, damit sie in die Roehre findet. '
                'Sparsam einsetzen: die Noppe ist nur 1,8 mm hoch, und genau '
                'ueber diese Hoehe klemmt der Stein. 0,20 mm sind ein guter Wert, '
                'ab 0,30 mm wird die Klemmung spuerbar schwaecher.')

            eck = kanten_kinder.addValueInput(
                IN_ECKRADIUS, 'Eckradius aussen', 'mm',
                adsk.core.ValueInput.createByReal(
                    _konfig.zahl('eckradius', 0.0, 0.0, ECKRADIUS_MAX) * MM))
            eck.tooltip = (
                'Verrundet die vier senkrechten Aussenkanten. Rein optisch - '
                'Vorsicht: nebeneinandergesetzte Steine zeigen dann sichtbare '
                'Spalten an den Ecken. Echte Steine sind hier scharfkantig.')

            # --- Druckerkalibrierung ----------------------------------------
            kal = inputs.addGroupCommandInput(IN_KAL_GRP, 'Druckerkalibrierung')
            kal.isExpanded = False
            kal_kinder = kal.children

            koppeln = kal_kinder.addBoolValueInput(
                IN_KAL_KOPPELN, 'X und Y koppeln', True, '',
                bool(_letzte.get('kal_koppeln', True)))
            koppeln.tooltip = (
                'Uebernimmt den X-Faktor auch fuer Y. Getrennte Achsen nur, wenn '
                'wirklich gemessen - der Klemmkontakt liegt diagonal und vertraegt '
                'kaum Unterschied zwischen den Achsen.')

            # Vor den Messfeldern, nicht dahinter: wer von oben nach unten
            # liest, haette sie sonst laengst von Hand ausgefuellt, bevor er
            # den Knopf sieht, der genau das erledigt.
            uebernehmen = kal_kinder.addBoolValueInput(
                IN_KAL_UEBERNEHMEN, 'Modellmass uebernehmen', False, '', False)
            uebernehmen.tooltip = (
                'Traegt die aktuellen Modellmasse in die Felder "im Modell" '
                'ein - genau das, was Fusion gerade baut.\n\n'
                'Ablauf beim Nachkalibrieren: Teil drucken, hier druecken, '
                'dann die gemessenen Werte daneben eintragen.\n\n'
                'Achsen, deren beide Felder leer sind, bleiben unberuehrt.')

            def _messfeld(ident, beschriftung, schluessel):
                feld = kal_kinder.addValueInput(
                    ident, beschriftung, 'mm',
                    adsk.core.ValueInput.createByReal(
                        _konfig.zahl(schluessel, 0.0, 0.0, 1000.0) * MM))
                return feld

            _messfeld(IN_KAL_X_SOLL, 'X im Modell', 'kal_x_soll').tooltip = (
                'Das Mass, das im Modell steht - also die Zahl aus der Zeile '
                '"Aussenmass" oben, NICHT das gewuenschte Endmass.\n\n'
                'Beim ersten, noch unkalibrierten Druck ist beides dasselbe '
                '(z. B. 31,80 mm beim 4er-Stein). Sobald eine Kalibrierung '
                'wirkt, baut Fusion groesser - dann gehoert dieses groessere '
                'Mass hier hinein, sonst geht der bisherige Vorhalt verloren. '
                'Der Knopf darunter traegt es fuer dich ein.')
            _messfeld(IN_KAL_X_IST, 'X gemessen', 'kal_x_ist').tooltip = (
                'Was am gedruckten Teil tatsaechlich mit dem Messschieber '
                'herauskommt. Moeglichst an einem grossen Teil messen: an '
                'kleinen Massen ueberwiegt der konstante Duesenfehler, und '
                'daraus wird ein falscher Prozentwert.')
            _messfeld(IN_KAL_Y_SOLL, 'Y im Modell', 'kal_y_soll')
            _messfeld(IN_KAL_Y_IST, 'Y gemessen', 'kal_y_ist')
            _messfeld(IN_KAL_Z_SOLL, 'Z im Modell', 'kal_z_soll').tooltip = (
                'Die Bauhoehe aus der Zeile "Aussenmass", z. B. 9,60 mm beim '
                'unkalibrierten Stein. Achtung: die Hoehe, nicht Laenge oder '
                'Breite.')
            _messfeld(IN_KAL_Z_IST, 'Z gemessen', 'kal_z_ist')


            rund_in = kal_kinder.addValueInput(
                IN_KAL_RUND, 'Rundungs-Aufmass', 'mm',
                adsk.core.ValueInput.createByReal(
                    _konfig.zahl('kal_rund',
                                 PRINT_PROFILES[start_profil].get('komp_rund', 0.0),
                                 0.0, MAX_RUND) * MM))
            rund_in.tooltip = (
                'Absolutes Aufmass auf Noppen, Stege und Roehrenaussenseite. '
                'Der zweite, ganz andere Fehler: der Duesenversatz ist eine '
                'Konstante und waechst nicht mit dem Mass. Beim Testdruck lag '
                'die Noppe 0,24 mm daneben, nicht 5 Prozent - so etwas faengt '
                'kein Faktor ab.')

            kal_kinder.addTextBoxCommandInput(
                IN_KAL_INFO, 'Ergebnis', '', 3, True)

            # --- Serie ------------------------------------------------------
            serie = inputs.addGroupCommandInput(IN_SERIE_GRP, 'Serie')
            serie.isExpanded = True
            serie_kinder = serie.children

            wiederholen = serie_kinder.addBoolValueInput(
                IN_WIEDERHOLEN, 'Dialog offen lassen', True, '',
                _letzte.get('wiederholen', True))
            wiederholen.tooltip = ('Nach "Erzeugen" oeffnet sich der Dialog sofort '
                                   'wieder mit denselben Werten. Zum Beenden '
                                   'Abbrechen oder Esc druecken.')

            anordnen = serie_kinder.addBoolValueInput(
                IN_ANORDNEN, 'Nebeneinander ablegen', True, '',
                _letzte.get('anordnen', True))
            anordnen.tooltip = ('Legt jeden neuen Baustein mit {} mm Abstand neben '
                                'den vorherigen, statt alle in den Ursprung zu '
                                'stapeln.'.format(_de(ABSTAND, 0)))

            # --- STL-Export -------------------------------------------------
            gruppe = inputs.addGroupCommandInput(IN_STL_GRP, 'STL-Export')
            gruppe.isExpanded = bool(_letzte.get('stl_an', False))
            kinder = gruppe.children

            stl_an_wert = bool(_letzte.get('stl_an', False))
            stl_an = kinder.addBoolValueInput(IN_STL_AN, 'STL beim Erzeugen schreiben',
                                              True, '', stl_an_wert)
            stl_an.tooltip = ('Exportiert den fertigen Koerper direkt als binaeres '
                              'STL. Vorhandene Dateien werden nicht ueberschrieben, '
                              'sondern durchnummeriert.')

            start_ordner = _letzte.get('stl_ordner') or os.path.join(
                os.path.expanduser('~'), 'Documents')
            ordner = kinder.addStringValueInput(IN_STL_ORDNER, 'Zielordner', start_ordner)
            ordner.isEnabled = stl_an_wert

            browse = kinder.addBoolValueInput(IN_STL_BROWSE, 'Ordner waehlen ...',
                                              False, '', False)
            browse.isEnabled = stl_an_wert

            # Erst jetzt, wo alle Eingaben stehen: beide Helfer greifen quer
            # durch den Dialog und wuerden weiter oben ins Leere laufen.
            _sichtbarkeit(inputs)
            _aktualisiere_info(inputs)

            # --- Handler registrieren ---------------------------------------
            on_execute = KlemmbausteinExecuteHandler()
            cmd.execute.add(on_execute)
            _handlers.append(on_execute)

            on_preview = KlemmbausteinExecutePreviewHandler()
            cmd.executePreview.add(on_preview)
            _handlers.append(on_preview)

            on_changed = KlemmbausteinInputChangedHandler()
            cmd.inputChanged.add(on_changed)
            _handlers.append(on_changed)

            on_validate = KlemmbausteinValidateInputsHandler()
            cmd.validateInputs.add(on_validate)
            _handlers.append(on_validate)

            on_destroy = KlemmbausteinDestroyHandler()
            cmd.destroy.add(on_destroy)
            _handlers.append(on_destroy)

        except Exception:
            if ui:
                ui.messageBox('Fehler beim Aufbau des Dialogs:\n{}'.format(traceback.format_exc()))


class KlemmbausteinInputChangedHandler(adsk.core.InputChangedEventHandler):
    """Reagiert auf Aenderungen: Ordnerdialog, Ein-/Ausgrauen, Infozeile."""

    def notify(self, args):
        try:
            geaendert = args.input
            cmd = adsk.core.Command.cast(args.firingEvent.sender)
            inputs = cmd.commandInputs

            stl_an = _finde(inputs, IN_STL_AN)
            ordner = _finde(inputs, IN_STL_ORDNER)
            browse = _finde(inputs, IN_STL_BROWSE)

            if geaendert.id == IN_STL_AN:
                ordner.isEnabled = stl_an.value
                browse.isEnabled = stl_an.value

            elif geaendert.id == IN_STL_BROWSE and browse.value:
                browse.value = False  # Button-Zustand sofort zuruecksetzen
                dialog = ui.createFolderDialog()
                dialog.title = 'Zielordner fuer den STL-Export'
                if os.path.isdir(ordner.value):
                    dialog.initialDirectory = ordner.value
                if dialog.showDialog() == adsk.core.DialogResults.DialogOK:
                    ordner.value = dialog.folder

            elif geaendert.id == IN_PROFIL:
                # Profilwechsel setzt Klemmspiel und Kalibrierung auf die
                # Vorgabewerte des Profils.
                profil = geaendert.selectedItem.name
                if profil in PRINT_PROFILES:
                    _profil_uebernehmen(inputs, PRINT_PROFILES[profil])

            elif geaendert.id in (IN_TYP, IN_KAL_KOPPELN):
                _sichtbarkeit(inputs)

            elif geaendert.id == IN_KAL_UEBERNEHMEN and geaendert.value:
                # Ein Knopf, kein Schalter: sofort wieder ausrasten, sonst
                # bliebe er gedrueckt stehen und liesse sich nicht erneut
                # betaetigen.
                geaendert.value = False
                _modellmass_uebernehmen(inputs)

            # Bei jeder Aenderung die berechneten Masse nachziehen. Die Liste
            # bewusst explizit: der Ordnerdialog und die Serienschalter
            # aendern nichts an der Geometrie.
            if geaendert.id in (IN_TYP, IN_LAENGE, IN_BREITE, IN_SCHRAEGE,
                                IN_PROFIL, IN_KLEMM, IN_KANTE_METHODE,
                                IN_KANTE_UNTEN, IN_KANTE_NOPPE, IN_ECKRADIUS,
                                IN_KAL_KOPPELN, IN_KAL_X_SOLL, IN_KAL_X_IST,
                                IN_KAL_Y_SOLL, IN_KAL_Y_IST, IN_KAL_Z_SOLL,
                                IN_KAL_Z_IST, IN_KAL_RUND, IN_KAL_UEBERNEHMEN):
                _aktualisiere_info(inputs)

        except Exception:
            if ui:
                ui.messageBox('Fehler in inputChanged:\n{}'.format(traceback.format_exc()))


class KlemmbausteinValidateInputsHandler(adsk.core.ValidateInputsEventHandler):
    """Sperrt OK, solange die Eingaben nicht sinnvoll sind."""

    def notify(self, args):
        try:
            inputs = adsk.core.Command.cast(args.firingEvent.sender).commandInputs
            cfg = Einstellungen(inputs)

            gueltig = 1 <= cfg.nx <= MAX_NOPPEN and 1 <= cfg.ny <= MAX_NOPPEN
            if not (KLEMM_MIN <= cfg.klemm <= KLEMM_MAX):
                gueltig = False
            if cfg.stl_an and not cfg.stl_ordner:
                gueltig = False

            if not (0.0 <= cfg.kante_unten <= KANTE_MAX):
                gueltig = False
            if not (0.0 <= cfg.kante_noppe <= KANTE_NOPPE_MAX):
                gueltig = False
            if not (0.0 <= cfg.eckradius <= ECKRADIUS_MAX):
                gueltig = False
            if not (0.0 <= cfg.kal_rund <= MAX_RUND):
                gueltig = False

            # Ein Eckradius kann sich selbst ueberschneiden, wenn er breiter
            # wird als das halbe Teil. rundrechteck faengt das zwar ab, aber
            # dann stimmt das Ergebnis nicht mehr mit der Eingabe ueberein -
            # besser hier ehrlich sperren.
            p = PRINT_PROFILES[cfg.profil]
            kleinste_seite = min(cfg.nx, cfg.ny) * PITCH - p['gap']
            if cfg.eckradius > kleinste_seite / 2.0 and not _ist_rund(cfg.typ):
                gueltig = False

            # Ein L braucht zwei Seiten von mindestens zwei Noppen, sonst
            # gibt es keine Ecke, um die es herumlaufen koennte.
            if cfg.typ == TYP_ECK and min(cfg.nx, cfg.ny) < 2:
                gueltig = False

            # Eine Querbohrung auf 5,8 mm Hoehe braucht ein Teil, das hoch
            # genug ist - sonst schneidet sie die Oberseite auf.
            if cfg.typ in TYPEN_MIT_BOHRUNG:
                if _hoehe(cfg.typ) - TECHNIC_AXIS_Z < TECHNIC_HOLE_D / 2.0:
                    gueltig = False

            # Messwertpaare: eines von beiden gefuellt ist immer ein
            # Versehen - so entstuende ein stiller Faktor 1,0.
            for soll, ist in ((cfg.kal_x_soll, cfg.kal_x_ist),
                              (cfg.kal_y_soll, cfg.kal_y_ist),
                              (cfg.kal_z_soll, cfg.kal_z_ist)):
                if (soll > 1e-9) != (ist > 1e-9):
                    gueltig = False

            args.areInputsValid = gueltig
        except Exception:
            args.areInputsValid = False


class KlemmbausteinExecutePreviewHandler(adsk.core.CommandEventHandler):
    """Live-Vorschau: baut die Geometrie bei jeder Aenderung neu auf."""

    def notify(self, args):
        try:
            inputs = adsk.core.Command.cast(args.firingEvent.sender).commandInputs
            cfg = Einstellungen(inputs)
            if not cfg.vorschau:
                return

            design = adsk.fusion.Design.cast(app.activeProduct)
            if not design:
                return

            versatz = _platz.get(_dokument_schluessel(design), 0.0) if cfg.anordnen else 0.0
            justage = cfg.justage()
            if _kantenzahl(cfg.typ, cfg.nx, cfg.ny,
                           cfg.schenkel) > VORSCHAU_KANTEN_GRENZE:
                justage = justage.ohne_kanten()
            baue_stein(design, cfg.typ, cfg.nx, cfg.ny, cfg.profil, versatz,
                       cfg.klemm, cfg.ns, justage=justage,
                       schenkel=cfg.schenkel, bohrung=cfg.bohrung)

            # Bewusst False: das endgueltige Ergebnis wird in execute() erzeugt,
            # damit der STL-Export auf einem realen Koerper arbeiten kann.
            args.isValidResult = False

        except Exception:
            if ui:
                ui.messageBox('Fehler in der Vorschau:\n{}'.format(traceback.format_exc()))


class KlemmbausteinExecuteHandler(adsk.core.CommandEventHandler):
    """Erzeugt das endgueltige Bauteil und exportiert optional das STL."""

    def notify(self, args):
        global _wiederholen_aktiv
        try:
            inputs = adsk.core.Command.cast(args.firingEvent.sender).commandInputs
            cfg = Einstellungen(inputs)

            design = adsk.fusion.Design.cast(app.activeProduct)
            if not design:
                ui.messageBox('Bitte zuerst ein Design oeffnen (Konstruktions-Arbeitsbereich).')
                return

            schluessel = _dokument_schluessel(design)
            versatz = _platz.get(schluessel, 0.0) if cfg.anordnen else 0.0

            justage = cfg.justage()
            occ, body = baue_stein(design, cfg.typ, cfg.nx, cfg.ny, cfg.profil,
                                   versatz, cfg.klemm, cfg.ns, justage=justage,
                                   schenkel=cfg.schenkel, bohrung=cfg.bohrung)

            if cfg.anordnen:
                p_cfg = PRINT_PROFILES[cfg.profil]
                # Der Rundstein ist so breit wie lang - sonst legt der
                # naechste Baustein sich in ihn hinein.
                ny_echt = cfg.nx if _ist_rund(cfg.typ) else cfg.ny
                breite_mm = (ny_echt * PITCH - p_cfg['gap']) * justage.fy
                _platz[schluessel] = versatz + breite_mm + ABSTAND

            if cfg.stl_an:
                mesh = PRINT_PROFILES[cfg.profil]['mesh']
                pfad = b.exportiere_stl(design, body, cfg.stl_ordner,
                                        _dateiname(cfg.typ, cfg.nx, cfg.ny,
                                                   cfg.klemm, cfg.profil,
                                                   cfg.ns, justage,
                                                   cfg.schenkel, cfg.bohrung),
                                        mesh)
                # Bei Serienbetrieb nur ins Textkommando-Fenster loggen - eine
                # Messagebox pro Baustein wuerde den Ablauf staendig stoppen.
                app.log('Klemmbaustein exportiert: {}'.format(pfad))
                if not cfg.wiederholen:
                    ui.messageBox('STL geschrieben:\n{}'.format(pfad), CMD_NAME)

            # Merkt sich, ob der Dialog gleich wieder aufgehen soll.
            _wiederholen_aktiv = cfg.wiederholen

        except Exception:
            _wiederholen_aktiv = False
            if ui:
                ui.messageBox('Fehler beim Erzeugen:\n{}'.format(traceback.format_exc()))


class KlemmbausteinCommandTerminatedHandler(adsk.core.ApplicationCommandEventHandler):
    """Oeffnet den Dialog nach OK sofort wieder - fuer Serien von Bausteinen."""

    def notify(self, args):
        global _wiederholen_aktiv
        try:
            if args.commandId != CMD_ID:
                return
            if not _wiederholen_aktiv:
                return
            # Nur nach einem echten OK weitermachen, nicht nach Abbrechen/Esc.
            if args.terminationReason != adsk.core.CommandTerminationReason.CompletedTerminationReason:
                _wiederholen_aktiv = False
                return

            _wiederholen_aktiv = False  # Schutz gegen Endlosschleife
            cmd_def = ui.commandDefinitions.itemById(CMD_ID)
            if cmd_def:
                cmd_def.execute()

        except Exception:
            _wiederholen_aktiv = False
            if ui:
                ui.messageBox('Fehler beim Wiederoeffnen:\n{}'.format(traceback.format_exc()))


class KlemmbausteinDestroyHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            # Beim Schliessen des Dialogs die Werte dauerhaft sichern -
            # auch bei Abbrechen, damit der Zielordner erhalten bleibt.
            _konfig_speichern()
        except Exception:
            pass
        try:
            # Im Script-Modus erst beenden, wenn der Dialog nicht gleich
            # wieder aufgeht (Serienbetrieb).
            if _SCRIPT_MODE and not _wiederholen_aktiv:
                adsk.terminate()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Add-In Ein- und Ausstieg
# ---------------------------------------------------------------------------

def run(context):
    global app, ui
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        # Gemerkte Einstellungen der letzten Sitzung holen.
        _konfig_laden()

        # Alte Definition sauber entfernen (z. B. nach einem Reload).
        alt = ui.commandDefinitions.itemById(CMD_ID)
        if alt:
            alt.deleteMe()

        # Symbolordner neben dieser Datei; fehlt er, bleibt der Button ohne Icon.
        symbole = os.path.join(_THIS_DIR, 'resources')
        if not os.path.isdir(symbole):
            symbole = ''

        cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME,
                                                            CMD_TOOLTIP, symbole)

        on_created = KlemmbausteinCommandCreatedHandler()
        cmd_def.commandCreated.add(on_created)
        _handlers.append(on_created)

        # Fuer das Wiederoeffnen nach OK (Serienbetrieb).
        on_terminated = KlemmbausteinCommandTerminatedHandler()
        ui.commandTerminated.add(on_terminated)
        _handlers.append(on_terminated)

        panel = ui.allToolbarPanels.itemById(PANEL_ID)
        if panel and not panel.controls.itemById(CMD_ID):
            steuerung = panel.controls.addCommand(cmd_def)
            steuerung.isPromoted = True

        if _SCRIPT_MODE:
            # Als Script muss der Prozess bis zum Schliessen des Dialogs laufen.
            adsk.autoTerminate(False)

        # Beim manuellen Start (Run-Button) direkt den Dialog oeffnen,
        # beim Fusion-Start dagegen nur den Befehl registrieren.
        if _SCRIPT_MODE or not context.get('IsApplicationStartup', False):
            cmd_def.execute()

    except Exception:
        if ui:
            ui.messageBox('Klemmbaustein-Generator konnte nicht gestartet werden:\n{}'.format(
                traceback.format_exc()))


def stop(context):
    try:
        if not ui:
            return

        panel = ui.allToolbarPanels.itemById(PANEL_ID)
        if panel:
            steuerung = panel.controls.itemById(CMD_ID)
            if steuerung:
                steuerung.deleteMe()

        cmd_def = ui.commandDefinitions.itemById(CMD_ID)
        if cmd_def:
            cmd_def.deleteMe()

        # Anwendungsweites Ereignis wieder abmelden, sonst haengt es an Fusion.
        for handler in _handlers:
            if isinstance(handler, KlemmbausteinCommandTerminatedHandler):
                ui.commandTerminated.remove(handler)

        del _handlers[:]
        _platz.clear()

    except Exception:
        if ui:
            ui.messageBox('Fehler beim Beenden:\n{}'.format(traceback.format_exc()))
