# -*- coding: utf-8 -*-
"""Erzeugt die bebilderte HTML-Anleitung.

Aufruf aus dem Projektordner:

    python werkzeuge/anleitung_bauen.py

Schreibt "anleitung.html" neben die Python-Dateien. Alle Bilder sind
eingebettete SVG - die Seite laeuft ohne Netz, ohne Schriftdownload und
ohne eine einzige Fremddatei.

Die Zeichnungen entstehen aus denselben Funktionen, die auch die Geometrie
in Fusion bauen (siehe zeichnen.py). Damit kann die Anleitung nicht
veralten, ohne dass es auffaellt.
"""

import io
import os
import sys
import types

HIER = os.path.dirname(os.path.realpath(__file__))
PROJEKT = os.path.dirname(HIER)


def stub_adsk():
    """Fusion-API vortaeuschen, damit das Add-In-Modul importierbar wird.

    Gebraucht werden nur die Rechenfunktionen. Alles, was die API anfasst,
    laeuft hier nie - der Stub muss deshalb nur den Import ueberstehen.
    """
    core = types.ModuleType('adsk.core')
    fusion = types.ModuleType('adsk.fusion')
    adsk = types.ModuleType('adsk')

    class Dummy(object):
        def __init__(self, *a, **k):
            pass

        def __getattr__(self, name):
            return Dummy()

        def __call__(self, *a, **k):
            return Dummy()

    for name in ('CommandCreatedEventHandler', 'InputChangedEventHandler',
                 'ValidateInputsEventHandler', 'CommandEventHandler',
                 'ApplicationCommandEventHandler'):
        setattr(core, name, type(name, (object,), {}))
    for name in ('Point3D', 'ValueInput', 'ObjectCollection', 'Matrix3D',
                 'Vector3D', 'Circle3D', 'Arc3D', 'Line3D', 'Application',
                 'DropDownStyles', 'GroupCommandInput', 'TabCommandInput',
                 'Command', 'DialogResults', 'CommandTerminationReason'):
        setattr(core, name, Dummy())
    for name in ('Design', 'FeatureOperations', 'ExtentDirections',
                 'OffsetStartDefinition', 'DistanceExtentDefinition',
                 'MeshRefinementSettings'):
        setattr(fusion, name, Dummy())

    adsk.core, adsk.fusion = core, fusion
    sys.modules['adsk'] = adsk
    sys.modules['adsk.core'] = core
    sys.modules['adsk.fusion'] = fusion


stub_adsk()
sys.path.insert(0, PROJEKT)
sys.path.insert(0, HIER)

import Klemmbaustein as K       # noqa: E402
import zeichnen as Z            # noqa: E402


def de(zahl, nachkomma=2):
    return ('{:.' + str(nachkomma) + 'f}').format(zahl).replace('.', ',')


# ---------------------------------------------------------------------------
# Bausteine der Seite
# ---------------------------------------------------------------------------

def abschnitt(nummer, titel, inhalt, kennung=None):
    return ('<section id="{}"><h2><span class="nr">{}</span>{}</h2>{}'
            '</section>').format(kennung or 'a{}'.format(nummer), nummer,
                                 titel, inhalt)


def tafel(svg, unterschrift):
    return ('<figure><div class="zeichnung">{}</div>'
            '<figcaption>{}</figcaption></figure>').format(svg, unterschrift)


def tabelle(kopf, zeilen):
    kopf_html = ''.join('<th>{}</th>'.format(z) for z in kopf)
    leib = ''.join('<tr>{}</tr>'.format(
        ''.join('<td>{}</td>'.format(z) for z in zeile)) for zeile in zeilen)
    return ('<div class="tabelle"><table><thead><tr>{}</tr></thead>'
            '<tbody>{}</tbody></table></div>').format(kopf_html, leib)


def hinweis(text, art='info'):
    return '<div class="hinweis {}">{}</div>'.format(art, text)


# ---------------------------------------------------------------------------
# Inhalt
# ---------------------------------------------------------------------------

def bauteiltypen():
    """Eine Tafel je Bauteiltyp, mit den Zahlen aus dem Generator."""
    vorstellung = [
        (K.TYP_STEIN, 4, 2, 1, 'Der Standardstein. 9,60 mm hoch, Noppen in '
         'jeder Rasterfeldmitte, R&ouml;hren auf den Kreuzen darunter.'),
        (K.TYP_HALBSTEIN, 4, 2, 1, 'Halbe Steinh&ouml;he. Zwei davon ergeben '
         'genau einen Stein &ndash; f&uuml;r H&ouml;hensprünge, die mit Steinen '
         'und Platten allein nicht aufgehen.'),
        (K.TYP_PLATTE, 4, 2, 1, 'Ein Drittel Steinh&ouml;he. Drei Platten '
         'stapeln sich auf 9,60 mm.'),
        (K.TYP_FLIESE, 4, 2, 1, 'Wie die Platte, aber ohne Noppen &ndash; '
         'f&uuml;r glatte Oberfl&auml;chen.'),
        (K.TYP_JUMPER, 1, 2, 1, 'Die Noppe sitzt auf dem Rasterkreuz statt in '
         'der Feldmitte. Damit l&auml;sst sich alles Aufgesteckte um ein halbes '
         'Raster versetzen.'),
        (K.TYP_TECHNIC, 4, 2, 1, 'Stein mit Querbohrungen auf 5,80 mm '
         'H&ouml;he, eine je Noppenspalte.'),
        (K.TYP_LOCHBALKEN, 4, 1, 1, 'Querbohrungen ohne Noppen. &Uuml;berall '
         'dort, wo oben nichts im Weg sein soll.'),
        (K.TYP_SCHRAEG, 4, 2, 1, 'F&auml;llt zur Vorderkante auf Plattenh&ouml;he '
         'ab. Der Winkel ergibt sich aus der L&auml;nge der Schr&auml;ge.'),
        (K.TYP_ECK, 4, 4, 2, 'L-Form aus zwei Schenkeln. Die Schenkelbreite '
         'ist einstellbar &ndash; h&ouml;chstens eine Noppe weniger als die '
         'schmalere Seite.'),
        (K.TYP_RUND, 4, 4, 1, 'Runder Grundriss. Noppen und R&ouml;hren, die zu '
         'weit &uuml;ber den Rand ragen w&uuml;rden, entfallen &ndash; hier die '
         'vier Ecknoppen.'),
        (K.TYP_GRUNDPLATTE, 6, 6, 1, 'Massiv, 1,60 mm dick, ohne Klemmung an '
         'der Unterseite.'),
    ]

    karten = []
    for typ, nx, ny, w, text in vorstellung:
        nyz = nx if K._ist_rund(typ) else ny
        noppen = len(K._noppen_stellen(typ, nx, nyz, K._schenkel(nx, nyz, w)))
        roehren = len(K._roehren_stellen(typ, nx, nyz, K._schenkel(nx, nyz, w)))
        stege = len(K._stege_stellen(typ, nx, nyz))
        unten = ('{} R&ouml;hren'.format(roehren) if roehren
                 else ('{} Stege'.format(stege) if stege else 'massiv'))
        karten.append(
            '<article class="typ"><div class="zeichnung">{svg}</div>'
            '<div class="typtext"><h3>{name}</h3><p>{text}</p>'
            '<dl><div><dt>H&ouml;he</dt><dd>{hoehe} mm</dd></div>'
            '<div><dt>gezeigt</dt><dd>{gr}</dd></div>'
            '<div><dt>Noppen</dt><dd>{noppen}</dd></div>'
            '<div><dt>Unterseite</dt><dd>{unten}</dd></div></dl>'
            '</div></article>'.format(
                svg=Z.draufsicht(K, typ, nx, ny, w, bemassen=False,
                                 skala=5.4),
                name=typ, text=text, hoehe=de(K._hoehe(typ)),
                gr=('&oslash; {}'.format(nx) if K._ist_rund(typ)
                    else '{}&times;{}'.format(nx, ny)),
                noppen=noppen or '&ndash;', unten=unten))
    return '<div class="typen">{}</div>'.format(''.join(karten))


def seite():
    normal_svg, jumper_svg = Z.jumpervergleich(K)
    p = K.PRINT_PROFILES['PLA (0,2 mm Schicht)']

    teile = []

    # -- 1. Was das Werkzeug macht -----------------------------------------
    teile.append(abschnitt(1, 'Was der Generator macht', ''.join([
        '<p class="vorspann">Ein Fusion-Add-In, das klemmbaustein-kompatible '
        'Bauteile parametrisch erzeugt &ndash; mit Live-Vorschau, '
        'Druckerkalibrierung und STL-Export.</p>',
        tafel(Z.schnitt(K, K.TYP_STEIN, 2),
              'Schnitt durch einen Stein: Deckplatte 1,00 mm, darunter der '
              'Hohlraum mit der R&ouml;hre, oben die 1,80 mm hohe Noppe.'),
        tabelle(['Ma&szlig;', 'Wert', 'wof&uuml;r'], [
            ['Raster', '{} mm'.format(de(K.PITCH)), 'Noppenabstand'],
            ['Steinh&ouml;he', '{} mm'.format(de(K.BRICK_H)), 'Standardstein'],
            ['Plattenh&ouml;he', '{} mm'.format(de(K.PLATE_H)),
             'drei ergeben einen Stein'],
            ['Noppe', '&oslash; {} mm'.format(de(K.STUD_D)), 'die Klemmstelle'],
            ['R&ouml;hre au&szlig;en', '&oslash; {} mm'.format(de(K.TUBE_OD)),
             'greift die Noppe'],
            ['Spiel', '{} mm'.format(de(p['gap'])),
             'Untermaß gegen&uuml;ber dem Raster'],
        ]),
    ])))

    # -- 2. Raster gegen Aussenmass ----------------------------------------
    teile.append(abschnitt(2, 'Rastermaß ist nicht Außenmaß', ''.join([
        '<p>Der h&auml;ufigste Messfehler &ndash; und der einzige, der eine '
        'Kalibrierung zuverl&auml;ssig ruiniert.</p>',
        tafel(Z.draufsicht(K, K.TYP_PLATTE, 2, 2, skala=9.0),
              'Eine 2&times;2-Platte belegt 16,00 mm Raster, misst aber '
              '15,80 mm.'),
        hinweis(
            '<b>Zwei Noppen sind 16,00 mm Raster, aber nur {} mm '
            'Au&szlig;enma&szlig;.</b> Die {} mm Differenz sind gewollt: ohne '
            'sie passten zwei nebeneinandergesetzte Steine nicht mehr ins '
            'Raster. Wer gegen die 16,00 misst und die Differenz '
            '&bdquo;wegkalibriert&ldquo;, zerst&ouml;rt genau dieses Spiel.'.format(
                de(2 * K.PITCH - p['gap']), de(p['gap'])), 'warnung'),
    ])))

    # -- 3. Bauteiltypen ---------------------------------------------------
    teile.append(abschnitt(3, 'Die Bauteiltypen', ''.join([
        '<p>Elf Typen, alle aus demselben Raster abgeleitet. Die Zeichnungen '
        'zeigen die Draufsicht; gestrichelt, was an der Unterseite verdeckt '
        'liegt.</p>',
        bauteiltypen(),
    ])))

    # -- 4. Jumper ---------------------------------------------------------
    teile.append(abschnitt(4, 'Die Jumper-Platte im Vergleich', ''.join([
        '<div class="paar">',
        tafel(normal_svg, 'Platte 2&times;2 &ndash; vier Noppen in den '
                          'Feldmitten.'),
        tafel(jumper_svg, 'Jumper 2&times;2 &ndash; eine Noppe auf dem '
                          'Rasterkreuz, um 4,00 mm versetzt.'),
        '</div>',
        tabelle(['Gr&ouml;&szlig;e', 'Noppen', 'Anmerkung'], [
            ['1&times;2', '1', 'genau in der Mitte &ndash; der Klassiker'],
            ['2&times;2', '1', 'zentral'],
            ['4&times;2', '3', 'l&auml;ngs versetzt'],
            ['1&times;1', '1', 'kein Versatz m&ouml;glich, = normale Platte'],
        ]),
        hinweis(
            'Ein 1&times;2-Teil greift die Jumper-Noppe mit seinem Steg. Eine '
            '<b>1&times;1-Platte klemmt dagegen nicht</b>: ihr Hohlraum ist '
            '{} mm weit, die Noppe nur {} mm dick. Daf&uuml;r br&auml;uchte es '
            '{} mm Wandst&auml;rke statt der {} mm aus dem Profil.'.format(
                de(K.PITCH - p['gap'] - 2 * p['wall']), de(K.STUD_D),
                de((K.PITCH - p['gap'] - K.STUD_D) / 2.0), de(p['wall'])),
            'warnung'),
    ])))

    # -- 5. Klemmung -------------------------------------------------------
    teile.append(abschnitt(5, 'Woher die Klemmkraft kommt', ''.join([
        tafel(Z.klemmdetail(K),
              'Noppe und R&ouml;hre ber&uuml;hren sich tangential &ndash; '
              'diagonal &uuml;ber 5,657 mm, mit 0,002 mm Rest.'),
        '<p>Gegriffen wird ausschlie&szlig;lich an der <b>Au&szlig;enseite der '
        'R&ouml;hre</b>. Die Seitenw&auml;nde haben konstruktiv {} mm Luft und '
        'klemmen nicht mit. Jede Verkleinerung der Noppe wirkt deshalb '
        '1:1 als Spiel.</p>'.format(de(p['gap'] / 2.0, 2)),
        tabelle(['Rechnung', 'Wert'], [
            ['Noppenmitte &rarr; R&ouml;hrenmitte',
             '&radic;(4&sup2;+4&sup2;) = 5,6569 mm'],
            ['Noppenradius + R&ouml;hrenau&szlig;enradius',
             '2,400 + 3,255 = 5,6550 mm'],
            ['<b>Rest</b>', '<b>0,002 mm &ndash; Linienber&uuml;hrung</b>'],
        ]),
    ])))

    # -- 6. Kanten brechen -------------------------------------------------
    verlust = [(m, m / K.STUD_H * 100.0) for m in (0.10, 0.20, 0.30, 0.40)]
    teile.append(abschnitt(6, 'Kanten brechen', ''.join([
        '<p>Bricht die scharfen Kanten, damit die Steine leichter '
        'zusammenfinden. <b>Alle Werte stehen ab Werk auf 0</b> &ndash; die '
        'Geometrie &auml;ndert sich nur, wenn man es will.</p>',
        tafel(Z.kantendetail(K),
              'Dieselbe Noppe scharf, mit Fase und mit Radius. Auf '
              'waagerechten Kanten druckt sich die Fase sauberer.'),
        tabelle(['Einstellung', 'wirkt auf', 'Empfehlung'], [
            ['Einf&uuml;hrkante unten',
             'R&ouml;hren, Stege, Technic-Bohrungen',
             '<b>0,20&ndash;0,30 mm</b> &ndash; kostet keine Klemmkraft'],
            ['Einf&uuml;hrkante Noppe', 'Oberkante der Noppe',
             '0,20 mm &ndash; sparsam, siehe unten'],
            ['Eckradius au&szlig;en', 'die vier senkrechten Kanten',
             'rein optisch, Vorgabe 0'],
        ]),
        hinweis(
            'Die Noppe ist nur {} mm hoch, und genau &uuml;ber diese H&ouml;he '
            'klemmt der Stein. Was oben weggebrochen wird, fehlt an der '
            'Klemmfl&auml;che.'.format(de(K.STUD_H)), 'warnung'),
        tabelle(['Kantenbrechung', 'verlorene Klemmfl&auml;che'],
                [[de(m) + ' mm', de(v, 0) + ' %'
                  + (' &mdash; ab hier warnt die Infozeile' if m >= 0.30 else '')]
                 for m, v in verlust]),
        hinweis(
            'Ab etwa 8&times;8 l&auml;sst die <b>Live-Vorschau</b> die '
            'Kantenbrechung weg und zeigt das Teil scharfkantig &ndash; sonst '
            'm&uuml;sste Fusion bei jedem Tastendruck tausende Kanten neu '
            'verrunden. Ein 32&times;32 h&auml;tte {} davon. '
            '&bdquo;Erzeugen&ldquo; bricht sie trotzdem.'.format(
                K._kantenzahl(K.TYP_STEIN, 32, 32))),
    ])))

    # -- 7. Technic --------------------------------------------------------
    teile.append(abschnitt(7, 'Rundloch oder Achskreuz', ''.join([
        tafel(Z.bohrungsdetail(K),
              'Das Rundloch lagert die Achse, das Achskreuz h&auml;lt sie '
              'formschl&uuml;ssig.'),
        tabelle(['Art', 'Ma&szlig;', 'Wirkung'], [
            ['Rundloch (Pin)', '&oslash; {} mm'.format(de(K.TECHNIC_HOLE_D)),
             'nimmt Pins auf, Achsen drehen frei'],
            ['Achskreuz', '{} / {} mm'.format(de(K.AXLE_SPAN), de(K.AXLE_ARM)),
             'die Achse dreht mit dem Bauteil mit'],
        ]),
        hinweis('Das Achskreuz bekommt <b>keine Kantenbrechung</b> &ndash; '
                'eine Fase an seinen zw&ouml;lf Ecken w&auml;re kaum sauber '
                'druckbar.'),
    ])))

    # -- 8. Kalibrierung ---------------------------------------------------
    teile.append(abschnitt(8, 'Den Drucker kalibrieren', ''.join([
        '<p>Nicht Prozente eintippen, sondern messen. Zwei Zahlen je Achse:</p>',
        '<pre class="eingabe">X Sollma&szlig;   31,80 mm   &larr; was laut '
        'Infozeile herauskommen soll\nX gemessen  31,73 mm   &larr; was der '
        'Messschieber sagt\n&rarr; Ergebnis: {} % Vorhalt</pre>'.format(
            de((K._faktor(31.8, 31.73) - 1.0) * 100.0, 3)),
        '<p><b>Beide Felder einer Achse leer (0) = nicht kalibriert.</b></p>',
        '<h3>Zwei verschiedene Fehler</h3>',
        tabelle(['Fehlerart', 'Verhalten', 'Werkzeug'], [
            ['Schrumpf', 'w&auml;chst mit dem Ma&szlig; (31,73 statt 31,80 '
             '= 0,22 %)', 'Soll / Gemessen'],
            ['D&uuml;senversatz', 'ist eine Konstante (Noppe 4,56 statt 4,80 '
             '= &minus;0,24 mm)', 'Rundungs-Aufma&szlig;'],
        ]),
        hinweis(
            'Beim Testdruck lag die Noppe <b>0,24 mm</b> daneben, nicht '
            '5 Prozent. So etwas f&auml;ngt kein Faktor ab &ndash; deshalb '
            'gibt es beide Felder. Und immer am gro&szlig;en Teil messen: an '
            'kleinen Ma&szlig;en &uuml;berwiegt der konstante Fehler.'),
        '<h3>X und Y</h3>',
        '<p>Der Klemmkontakt liegt diagonal und hat nur 0,002 mm Reserve. '
        'Laufen die Achsen auseinander, m&uuml;sste die Noppe elliptisch '
        'werden, um zu folgen &ndash; ab {} % Differenz warnt die '
        'Infozeile.</p>'.format(de(K.FAKTOR_DIFF_WARNUNG * 100, 2)),
        '<h3>Warum Z anders ist</h3>',
        '<p>Die H&ouml;he ist Schichtzahl mal Schichth&ouml;he. Der Slicer '
        'rundet auf ganze Schichten &ndash; kein Faktor holt das zur&uuml;ck. '
        'Eine Schichth&ouml;he w&auml;hlen, die {} mm teilt:</p>'.format(
            de(K.PLATE_H)),
        tabelle(['Schichth&ouml;he', 'Schichten f&uuml;r {} mm'.format(
            de(K.PLATE_H)), 'Ergebnis'],
            [[de(s) + ' mm', '{:.2f}'.format(K.PLATE_H / s).replace('.', ','),
              'teilt sauber' if abs(K.PLATE_H / s - round(K.PLATE_H / s)) < 1e-9
              else '<b>Slicer rundet</b>']
             for s in (0.10, 0.15, 0.16, 0.20, 0.25, 0.32)]),
    ])))

    # -- 9. Rechtliches ----------------------------------------------------
    teile.append(abschnitt(9, 'Rechtliches', ''.join([
        '<p>Dieses Projekt ist ein unabh&auml;ngiges, privates und '
        'unentgeltliches Werkzeug. Es steht in keiner Verbindung zur LEGO '
        'Gruppe und wird von ihr weder gesponsert noch autorisiert oder '
        'unterst&uuml;tzt. LEGO&reg; ist eine eingetragene Marke der LEGO '
        'Gruppe; die Nennung dient allein der Beschreibung der '
        'Kompatibilit&auml;t.</p>',
        '<p>Alle Ma&szlig;e basieren auf frei verf&uuml;gbaren, gemessenen '
        'Nennma&szlig;en des seit Jahrzehnten patentfreien '
        'Klemmbaustein-Rasters. Das Add-In steht unter der MIT-Lizenz: '
        'Nutzen, &Auml;ndern und Weitergeben sind frei, solange der '
        'Copyright-Vermerk erhalten bleibt. Die Nutzung erfolgt auf eigene '
        'Gefahr; eine Gew&auml;hr f&uuml;r Ma&szlig;haltigkeit, Eignung oder '
        'Druckergebnisse wird nicht &uuml;bernommen.</p>',
    ])))

    navigation = ''.join(
        '<a href="#a{}">{}</a>'.format(i + 1, t) for i, t in enumerate([
            'Überblick', 'Rastermaß', 'Bauteiltypen', 'Jumper', 'Klemmung',
            'Kanten', 'Technic', 'Kalibrierung', 'Rechtliches']))

    return VORLAGE.format(navigation=navigation, inhalt=''.join(teile),
                          typenzahl=len(K.TYPEN))


VORLAGE = u"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Klemmbaustein-Generator – Anleitung</title>
<style>
:root {{
  --grund: #fbfcfd;
  --karte: #ffffff;
  --text: #2e3440;
  --leise: #5b6878;
  --linie: #dde3ea;
  --akzent: #3b5478;
  --warn-rand: #bf616a;
  --warn-flaeche: #fdf3f4;
  --info-rand: #5e81ac;
  --info-flaeche: #f2f6fb;
  --radius: 10px;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --grund: #22272e;
    --karte: #2b313a;
    --text: #e6eaf0;
    --leise: #a7b2c0;
    --linie: #3a424e;
    --akzent: #9dbbe0;
    --warn-flaeche: #3a2c2e;
    --info-flaeche: #2a323d;
  }}
}}
:root[data-theme="dark"] {{
  --grund: #22272e; --karte: #2b313a; --text: #e6eaf0; --leise: #a7b2c0;
  --linie: #3a424e; --akzent: #9dbbe0; --warn-flaeche: #3a2c2e;
  --info-flaeche: #2a323d;
}}
:root[data-theme="light"] {{
  --grund: #fbfcfd; --karte: #ffffff; --text: #2e3440; --leise: #5b6878;
  --linie: #dde3ea; --akzent: #3b5478; --warn-flaeche: #fdf3f4;
  --info-flaeche: #f2f6fb;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; background: var(--grund); color: var(--text);
  font: 16px/1.65 system-ui, -apple-system, "Segoe UI", sans-serif;
}}
header {{
  padding: 3.5rem 1.5rem 2.5rem; text-align: center;
  border-bottom: 1px solid var(--linie);
}}
header h1 {{ margin: 0 0 .4rem; font-size: clamp(1.7rem, 1.1rem + 2.4vw, 2.6rem);
  letter-spacing: -.02em; }}
header p {{ margin: 0; color: var(--leise); }}
nav {{
  position: sticky; top: 0; z-index: 5; display: flex; flex-wrap: wrap;
  gap: .2rem; justify-content: center; padding: .6rem 1rem;
  background: color-mix(in srgb, var(--grund) 92%, transparent);
  backdrop-filter: blur(8px); border-bottom: 1px solid var(--linie);
}}
nav a {{
  color: var(--leise); text-decoration: none; font-size: .82rem;
  padding: .3rem .6rem; border-radius: 99px;
}}
nav a:hover {{ color: var(--text); background: var(--linie); }}
main {{ max-width: 62rem; margin: 0 auto; padding: 2.5rem 1.25rem 5rem; }}
section {{ margin-bottom: 3.5rem; scroll-margin-top: 4rem; }}
h2 {{
  display: flex; align-items: baseline; gap: .7rem; font-size: 1.45rem;
  letter-spacing: -.01em; padding-bottom: .5rem;
  border-bottom: 2px solid var(--linie); margin-bottom: 1.3rem;
}}
h2 .nr {{
  font-size: .8rem; color: var(--akzent); font-variant-numeric: tabular-nums;
  border: 1px solid var(--akzent); border-radius: 99px;
  width: 1.7rem; height: 1.7rem; display: inline-flex;
  align-items: center; justify-content: center; flex: none;
}}
h3 {{ font-size: 1.05rem; margin: 1.8rem 0 .6rem; }}
p {{ margin: 0 0 1rem; }}
.vorspann {{ font-size: 1.08rem; color: var(--leise); }}
figure {{ margin: 1.5rem 0; }}
/* Technische Zeichnungen bleiben in beiden Themes auf hellem Grund. Die
   Bemassung und die Kantenfarben sind auf Papier hin entworfen; auf
   dunklem Untergrund verschwaende der dunkle Text schlicht. */
.zeichnung {{
  background: #ffffff; border: 1px solid var(--linie);
  border-radius: var(--radius); padding: 1.1rem; display: flex;
  justify-content: center; overflow-x: auto;
}}
figcaption {{
  margin-top: .55rem; font-size: .85rem; color: var(--leise);
  text-align: center;
}}
.paar {{ display: grid; gap: 1.2rem; grid-template-columns: 1fr; }}
@media (min-width: 40rem) {{ .paar {{ grid-template-columns: 1fr 1fr; }} }}
.typen {{ display: grid; gap: 1rem; grid-template-columns: 1fr; }}
@media (min-width: 46rem) {{
  .typen {{ grid-template-columns: 1fr 1fr; }}
}}
.typ {{
  display: grid; grid-template-columns: 1fr; gap: .9rem;
  background: var(--karte); border: 1px solid var(--linie);
  border-radius: var(--radius); padding: 1rem;
}}
/* Feste Bildhoehe je Karte: die Motive sind unterschiedlich proportioniert
   (ein 1x2-Jumper ist hoch und schmal, ein 4x2-Stein breit und flach). Ohne
   gemeinsame Hoehe wuerden die Karten im Raster unterschiedlich hoch. */
.typ .zeichnung {{ padding: .6rem; height: 11rem; align-items: center; }}
.typ .zeichnung svg {{ width: auto; height: auto; max-height: 100%; }}
.typ h3 {{ margin: 0 0 .35rem; font-size: 1rem; }}
.typ p {{ margin: 0 0 .7rem; font-size: .88rem; color: var(--leise); }}
.typ dl {{ margin: 0; display: grid; gap: .15rem .8rem; font-size: .82rem; }}
.typ dl div {{ display: flex; gap: .5rem; justify-content: space-between;
  border-top: 1px dotted var(--linie); padding-top: .2rem; }}
.typ dt {{ color: var(--leise); }}
.typ dd {{ margin: 0; font-variant-numeric: tabular-nums; }}
.tabelle {{ overflow-x: auto; margin: 1.1rem 0; }}
table {{ border-collapse: collapse; width: 100%; font-size: .9rem;
  min-width: 22rem; }}
th, td {{ text-align: left; padding: .5rem .7rem;
  border-bottom: 1px solid var(--linie); vertical-align: top; }}
th {{ font-size: .78rem; text-transform: uppercase; letter-spacing: .04em;
  color: var(--leise); font-weight: 600; }}
td:not(:first-child) {{ font-variant-numeric: tabular-nums; }}
.hinweis {{
  border-left: 3px solid var(--info-rand); background: var(--info-flaeche);
  padding: .85rem 1rem; border-radius: 0 var(--radius) var(--radius) 0;
  margin: 1.1rem 0; font-size: .92rem;
}}
.hinweis.warnung {{ border-left-color: var(--warn-rand);
  background: var(--warn-flaeche); }}
pre.eingabe {{
  background: var(--karte); border: 1px solid var(--linie);
  border-radius: var(--radius); padding: 1rem; overflow-x: auto;
  font-size: .85rem; line-height: 1.6;
}}
footer {{
  border-top: 1px solid var(--linie); padding: 2rem 1.25rem 3rem;
  text-align: center; color: var(--leise); font-size: .85rem;
}}
</style>
</head>
<body>
<header>
  <h1>Klemmbaustein-Generator</h1>
  <p>Parametrische, klemmbaustein-kompatible Bauteile f&uuml;r Fusion –
     {typenzahl} Bauteiltypen, Druckerkalibrierung, STL-Export</p>
</header>
<nav>{navigation}</nav>
<main>{inhalt}</main>
<footer>
  <p>Alle Zeichnungen sind aus den Konstruktionsdaten des Generators erzeugt
     und damit immer auf demselben Stand wie das Add-In.</p>
  <p>LEGO&reg; ist eine eingetragene Marke der LEGO Gruppe. Dieses Projekt
     steht in keiner Verbindung zu ihr.</p>
</footer>
</body>
</html>
"""


def main():
    ziel = os.path.join(PROJEKT, 'anleitung.html')
    with io.open(ziel, 'w', encoding='utf-8') as f:
        f.write(seite())
    groesse = os.path.getsize(ziel) / 1024.0
    print('geschrieben: {}  ({:.1f} kB)'.format(ziel, groesse))


if __name__ == '__main__':
    main()
