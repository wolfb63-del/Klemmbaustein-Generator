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
        '<p>Male einen Kreis mit einem dicken Filzstift nach: Dein Kreis wird '
        'nie genau so gro&szlig; wie die Vorlage &ndash; der Stift ist eben '
        'dick. Ein 3D-Drucker macht dasselbe. Bei einem Klemmbaustein f&auml;llt '
        'das auf, denn ob er h&auml;lt, entscheidet sich in hundertstel '
        'Millimetern &ndash; d&uuml;nner als ein Haar.</p>',
        '<p>Die gute Nachricht: Dein Drucker macht diesen Fehler immer gleich. '
        'Einmal ausmessen, eintragen, fertig. Du musst dabei <b>nichts in '
        'Prozent umrechnen</b> &ndash; du tr&auml;gst zwei Zahlen ein, das '
        'Add-In rechnet selbst:</p>',
        '<pre class="eingabe">X Sollma&szlig;   31,80 mm   &larr; was '
        'herauskommen sollte (steht in der Infozeile)\nX gemessen  31,73 mm   '
        '&larr; was dein Messschieber wirklich anzeigt\n&rarr; Ergebnis: '
        '{} % Vorhalt</pre>'.format(
            de((K._faktor(31.8, 31.73) - 1.0) * 100.0, 3)),
        '<p><b>L&auml;sst du beide Felder einer Achse auf 0, bleibt diese '
        'Achse unver&auml;ndert.</b></p>',
        '<h3>Es gibt zwei Sorten Fehler</h3>',
        '<p>Das ist der wichtigste Gedanke hier. Geht etwas schief, kann das '
        'zwei ganz verschiedene Gr&uuml;nde haben &ndash; und jeder braucht '
        'sein eigenes Gegenmittel.</p>',
        tabelle(['Sorte', 'Verhalten', 'Das richtige Feld'], [
            ['<b>Schrumpf</b><br/><span class="bild">Pullover in der '
             'W&auml;sche</span>',
             'w&auml;chst mit dem Ma&szlig;: der l&auml;ngere &Auml;rmel geht '
             'st&auml;rker ein als der Kragen (31,73 statt 31,80 = 0,22 %)',
             'Soll / Gemessen'],
            ['<b>D&uuml;senversatz</b><br/><span class="bild">dicker '
             'Filzstift</span>',
             'immer derselbe Betrag, egal wie gro&szlig; das Teil ist '
             '(Noppe 4,56 statt 4,80 = &minus;0,24 mm)',
             'Rundungs-Aufma&szlig;'],
        ]),
        hinweis(
            'Beim Testdruck fehlten an der Noppe <b>0,24 mm</b> &ndash; als '
            'fester Betrag, nicht als Prozentwert. W&uuml;rdest du das mit '
            'Prozenten wegrechnen, w&auml;ren es an der kleinen Noppe ganze '
            '5 Prozent &ndash; und der ganze Stein w&uuml;rde viel zu '
            'gro&szlig;. Deshalb zwei Felder. Und immer am gro&szlig;en Teil '
            'messen: an kleinen Ma&szlig;en f&auml;llt der feste Fehler zu '
            'stark ins Gewicht.'),
        '<h3>X und Y</h3>',
        '<p>Noppe und R&ouml;hre ber&uuml;hren sich &uuml;ber Eck, und dort '
        'ist nur 0,002 mm Platz. Behandelst du die beiden Richtungen '
        'unterschiedlich, m&uuml;sste die Noppe oval werden, um noch zu passen '
        '&ndash; das kann sie nicht. Ab {} % Unterschied warnt die '
        'Infozeile.</p>'.format(de(K.FAKTOR_DIFF_WARNUNG * 100, 2)),
        '<h3>Warum die H&ouml;he ein Sonderfall ist</h3>',
        '<p>Der Drucker arbeitet in Schichten &ndash; wie ein Stapel Papier. '
        'Du kannst nur ganze Bl&auml;tter stapeln, keine halben. Ein Faktor '
        'hilft da wenig. W&auml;hle stattdessen eine Schichth&ouml;he, mit der '
        '{} mm glatt aufgeht:</p>'.format(
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
  --grund: #ffffff;
  --karte: #ffffff;
  --flaeche: #f5f5f7;
  --text: #1d1d1f;
  --leise: #6e6e73;
  --linie: #e5e5ea;
  --akzent: #0071e3;
  --ton: #0071e3;
  --warn-rand: #ff9f0a;
  --warn-flaeche: #fff8ed;
  --info-rand: #0071e3;
  --info-flaeche: #f0f7ff;
  --radius: 18px;
  --schatten: 0 1px 2px rgba(0,0,0,.04), 0 10px 30px rgba(0,0,0,.06);
}}
/* Jedes Kapitel bekommt seine eigene Farbe. Das macht die Seite freundlicher
   und hilft beim Wiederfinden: Kapitel 6 ist "das gruene", nicht "das
   sechste von oben". Die Toene sind Apples Systemfarben. */
main > section:nth-of-type(1) {{ --ton: #0071e3; }}
main > section:nth-of-type(2) {{ --ton: #00a3a3; }}
main > section:nth-of-type(3) {{ --ton: #8b5cf6; }}
main > section:nth-of-type(4) {{ --ton: #e8590c; }}
main > section:nth-of-type(5) {{ --ton: #d6336c; }}
main > section:nth-of-type(6) {{ --ton: #2f9e44; }}
main > section:nth-of-type(7) {{ --ton: #4c6ef5; }}
main > section:nth-of-type(8) {{ --ton: #c2255c; }}
main > section:nth-of-type(9) {{ --ton: #7048e8; }}
@media (prefers-color-scheme: dark) {{
  :root {{
    --grund: #000000;
    --karte: #1c1c1e;
    --flaeche: #1c1c1e;
    --text: #f5f5f7;
    --leise: #a1a1a6;
    --linie: #2c2c2e;
    --akzent: #0a84ff;
    --warn-flaeche: #2e2415;
    --info-flaeche: #10243b;
  }}
  main > section:nth-of-type(1) {{ --ton: #0a84ff; }}
  main > section:nth-of-type(2) {{ --ton: #40c8c8; }}
  main > section:nth-of-type(3) {{ --ton: #bf5af2; }}
  main > section:nth-of-type(4) {{ --ton: #ff9f0a; }}
  main > section:nth-of-type(5) {{ --ton: #ff62a5; }}
  main > section:nth-of-type(6) {{ --ton: #30d158; }}
  main > section:nth-of-type(7) {{ --ton: #5e9eff; }}
  main > section:nth-of-type(8) {{ --ton: #ff6b9d; }}
  main > section:nth-of-type(9) {{ --ton: #a78bfa; }}
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; background: var(--grund); color: var(--text);
  font: 17px/1.7 -apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui,
        "Segoe UI", sans-serif;
  -webkit-font-smoothing: antialiased;
}}
/* Der Kopf traegt die Farbe der Seite, ohne laut zu werden: ein weicher
   Verlauf, der nach unten ins Weiss auslaeuft. */
header {{
  padding: 5.5rem 1.5rem 4rem; text-align: center; position: relative;
  background:
    radial-gradient(60rem 22rem at 30% -8rem, #dbeafe 0%, transparent 60%),
    radial-gradient(50rem 20rem at 78% -4rem, #fce7f3 0%, transparent 62%),
    var(--grund);
}}
@media (prefers-color-scheme: dark) {{
  header {{
    background:
      radial-gradient(60rem 22rem at 30% -8rem, #10243b 0%, transparent 60%),
      radial-gradient(50rem 20rem at 78% -4rem, #2b1430 0%, transparent 62%),
      var(--grund);
  }}
}}
header h1 {{
  margin: 0 0 .8rem; font-size: clamp(2.2rem, 1.2rem + 4vw, 4rem);
  letter-spacing: -.035em; line-height: 1.05; font-weight: 700;
  background: linear-gradient(96deg, #0071e3 0%, #8b5cf6 46%, #d6336c 100%);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}}
header p {{
  margin: 0 auto; max-width: 34rem; color: var(--leise);
  font-size: clamp(1rem, .9rem + .4vw, 1.2rem);
}}
nav {{
  position: sticky; top: 0; z-index: 5; display: flex; flex-wrap: wrap;
  gap: .25rem; justify-content: center; padding: .7rem 1rem;
  background: color-mix(in srgb, var(--grund) 78%, transparent);
  backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid var(--linie);
}}
nav a {{
  color: var(--leise); text-decoration: none; font-size: .84rem;
  padding: .38rem .8rem; border-radius: 99px; font-weight: 500;
  transition: background .18s ease, color .18s ease;
}}
nav a:hover {{ color: #fff; background: var(--akzent); }}
main {{ max-width: 58rem; margin: 0 auto; padding: 3.5rem 1.25rem 6rem; }}
section {{ margin-bottom: 5rem; scroll-margin-top: 4.5rem; }}
h2 {{
  display: flex; align-items: center; gap: .85rem;
  font-size: clamp(1.5rem, 1.2rem + 1.1vw, 2rem);
  letter-spacing: -.025em; font-weight: 700; margin-bottom: 1.6rem;
}}
h2 .nr {{
  font-size: .95rem; font-weight: 700; color: #fff;
  font-variant-numeric: tabular-nums;
  background: var(--ton); border-radius: 99px;
  width: 2.2rem; height: 2.2rem; display: inline-flex;
  align-items: center; justify-content: center; flex: none;
  box-shadow: 0 4px 12px color-mix(in srgb, var(--ton) 40%, transparent);
}}
h3 {{
  font-size: 1.15rem; margin: 2.2rem 0 .7rem; letter-spacing: -.015em;
  font-weight: 600; color: var(--ton);
}}
p {{ margin: 0 0 1.1rem; }}
b {{ font-weight: 600; }}
.vorspann {{
  font-size: 1.15rem; color: var(--leise); letter-spacing: -.01em;
  max-width: 44rem;
}}
figure {{ margin: 1.5rem 0; }}
/* Technische Zeichnungen bleiben in beiden Themes auf hellem Grund. Die
   Bemassung und die Kantenfarben sind auf Papier hin entworfen; auf
   dunklem Untergrund verschwaende der dunkle Text schlicht. */
.zeichnung {{
  background: #ffffff; border: 1px solid var(--linie);
  border-radius: var(--radius); padding: 1.4rem; display: flex;
  justify-content: center; overflow-x: auto; box-shadow: var(--schatten);
}}
figcaption {{
  margin-top: .7rem; font-size: .86rem; color: var(--leise);
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
  border-radius: var(--radius); padding: 1.2rem;
  box-shadow: var(--schatten);
  transition: transform .2s ease, box-shadow .2s ease;
}}
.typ:hover {{
  transform: translateY(-3px);
  box-shadow: 0 2px 4px rgba(0,0,0,.05), 0 18px 40px rgba(0,0,0,.10);
}}
/* Feste Bildhoehe je Karte: die Motive sind unterschiedlich proportioniert
   (ein 1x2-Jumper ist hoch und schmal, ein 4x2-Stein breit und flach). Ohne
   gemeinsame Hoehe wuerden die Karten im Raster unterschiedlich hoch. */
.typ .zeichnung {{ padding: .6rem; height: 11rem; align-items: center; }}
.typ .zeichnung svg {{ width: auto; height: auto; max-height: 100%; }}
.typ h3 {{ margin: 0 0 .35rem; font-size: 1.05rem; color: var(--ton); }}
.typ p {{ margin: 0 0 .7rem; font-size: .9rem; color: var(--leise); }}
.typ dl {{ margin: 0; display: grid; gap: .15rem .8rem; font-size: .84rem; }}
.typ dl div {{ display: flex; gap: .5rem; justify-content: space-between;
  border-top: 1px solid var(--linie); padding-top: .3rem; }}
.typ dt {{ color: var(--leise); }}
.typ dd {{ margin: 0; font-variant-numeric: tabular-nums; font-weight: 500; }}
.tabelle {{
  overflow-x: auto; margin: 1.4rem 0; border-radius: var(--radius);
  border: 1px solid var(--linie); background: var(--karte);
  box-shadow: var(--schatten);
}}
table {{ border-collapse: collapse; width: 100%; font-size: .92rem;
  min-width: 22rem; }}
th, td {{ text-align: left; padding: .8rem 1rem;
  border-bottom: 1px solid var(--linie); vertical-align: top; }}
tr:last-child td {{ border-bottom: none; }}
th {{
  font-size: .74rem; text-transform: uppercase; letter-spacing: .06em;
  color: var(--ton); font-weight: 700;
  background: color-mix(in srgb, var(--ton) 7%, transparent);
}}
td:not(:first-child) {{ font-variant-numeric: tabular-nums; }}
/* Der Alltagsvergleich unter einem Fachbegriff - leiser als dieser, damit
   klar ist, was Begriff und was Eselsbruecke ist. */
.bild {{ color: var(--leise); font-size: .86em; font-weight: 400; }}
/* Hinweise sind bewusst weich und rundum gefasst statt als harter Balken -
   auf der Seite sollen sie wie ein freundlicher Zuruf wirken, nicht wie
   eine Fehlermeldung. */
.hinweis {{
  background: var(--info-flaeche); border: 1px solid
    color-mix(in srgb, var(--info-rand) 22%, transparent);
  padding: 1.1rem 1.3rem; border-radius: var(--radius);
  margin: 1.4rem 0; font-size: .95rem;
}}
.hinweis.warnung {{
  background: var(--warn-flaeche);
  border-color: color-mix(in srgb, var(--warn-rand) 30%, transparent);
}}
pre.eingabe {{
  background: var(--flaeche); border: 1px solid var(--linie);
  border-radius: var(--radius); padding: 1.2rem 1.4rem; overflow-x: auto;
  font-size: .88rem; line-height: 1.75;
  font-family: "SF Mono", ui-monospace, "Cascadia Mono", Consolas, monospace;
}}
footer {{
  border-top: 1px solid var(--linie); padding: 3rem 1.25rem 4rem;
  text-align: center; color: var(--leise); font-size: .86rem;
  background: var(--flaeche);
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
  <p>&copy; 2026 Berthold Wolf &middot; MIT-Lizenz</p>
  <p>LEGO&reg; ist eine eingetragene Marke der LEGO Gruppe. Dieses Projekt
     steht in keiner Verbindung zu ihr.</p>
</footer>
</body>
</html>
"""


def main():
    ziel = os.path.join(PROJEKT, 'anleitung.html')
    # newline='\n' statt der Windows-Vorgabe CRLF: .gitattributes legt das
    # Repo auf LF fest, und ohne das schriebe der Generator die Datei bei
    # jedem Lauf in der jeweils anderen Form.
    with io.open(ziel, 'w', encoding='utf-8', newline='\n') as f:
        f.write(seite())
    groesse = os.path.getsize(ziel) / 1024.0
    print('geschrieben: {}  ({:.1f} kB)'.format(ziel, groesse))


if __name__ == '__main__':
    main()
