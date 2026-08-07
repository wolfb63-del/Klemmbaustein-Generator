# -*- coding: utf-8 -*-
"""Prueft die reine Rechenlogik ohne Fusion.

Die Geometrie selbst laesst sich hier nicht testen - dafuer braucht es
Fusion. Was sich testen laesst, ist alles, was vor der API passiert:
Kalibrierfaktoren, Grenzen, Namensgebung, Infotexte.
"""

import os
import sys
import types

# Projektordner ist der Ordner ueber diesem - kein fester Pfad, damit die
# Pruefungen auch nach einem Klon irgendwo sonst laufen.
HIER = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def stub_adsk():
    """Minimaler Ersatz fuer die Fusion-API - nur so viel, wie der Import braucht."""
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

    # Von diesen wird geerbt - sie muessen echte Klassen sein.
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

    # MESH greift auf konkrete Attribute zu.
    fusion.MeshRefinementSettings = Dummy()
    adsk.core = core
    adsk.fusion = fusion
    sys.modules['adsk'] = adsk
    sys.modules['adsk.core'] = core
    sys.modules['adsk.fusion'] = fusion


stub_adsk()
sys.path.insert(0, HIER)
import Klemmbaustein as K

fehler = []


def pruefe(name, ist, soll, tol=1e-6):
    ok = abs(ist - soll) <= tol if isinstance(soll, float) else ist == soll
    print('{:<52} {:<22} {}'.format(name, str(ist), 'OK' if ok else 'FEHLER -> ' + str(soll)))
    if not ok:
        fehler.append(name)


print('\n--- Kalibrierfaktor ---')
pruefe('leer = neutral', K._faktor(0.0, 0.0), 1.0)
pruefe('Ist fehlt = neutral', K._faktor(31.8, 0.0), 1.0)
pruefe('31,80 soll / 31,73 ist', K._faktor(31.8, 31.73), 1.0022062, 1e-6)
pruefe('zu gross gedruckt -> < 1', K._faktor(31.73, 31.8) < 1.0, True)
pruefe('Ausreisser wird gedeckelt', K._faktor(100.0, 50.0), K.FAKTOR_MAX)
pruefe('Ausreisser nach unten', K._faktor(50.0, 100.0), K.FAKTOR_MIN)

print('\n--- Testdruck 03.08.2026 nachgerechnet ---')
# Gemessen 31,73 statt 31,80 -> das Modell muss vorhalten.
f = K._faktor(31.8, 31.73)
pruefe('Vorhalt in Prozent', round((f - 1.0) * 100.0, 3), 0.221)
pruefe('gedruckt landet wieder auf Soll', round(31.8 * f * (31.73 / 31.8), 2), 31.8)
# Das alte Profil hatte 0,24 % - die Messung ergibt 0,221 %. Gleiche Groesse.
pruefe('nah am Profilwert 0,24 %', abs((f - 1.0) * 100.0 - 0.24) < 0.03, True)

print('\n--- Justage: Grenzen ---')
j = K.Justage(kante_noppe=99.0, kante_unten=99.0, eckradius=99.0)
pruefe('Noppe gedeckelt', j.kante_noppe, K.KANTE_NOPPE_MAX)
pruefe('unten gedeckelt', j.kante_unten, K.KANTE_MAX)
pruefe('Eckradius gedeckelt', j.eckradius, K.ECKRADIUS_MAX)
j2 = K.Justage(kante_noppe=-5.0)
pruefe('negativ wird 0', j2.kante_noppe, 0.0)

print('\n--- Justage: Roehrenwand bremst ---')
# Nennwerte: Aussen 6,51, innen 4,95 -> Wand 0,78 mm
wand = (6.51 - 4.95) / 2.0
pruefe('Wandstaerke Roehre', round(wand, 3), 0.78)
j3 = K.Justage(kante_unten=0.60)
pruefe('0,60 wird auf 45 % der Wand gebremst', round(j3.kante_roehre(wand), 4),
       round(wand * K.WAND_ANTEIL, 4))
pruefe('gebremster Wert laesst Wand stehen',
       j3.kante_roehre(wand) * 2 < wand, True)
j4 = K.Justage(kante_unten=0.20)
pruefe('kleiner Wert bleibt unangetastet', j4.kante_roehre(wand), 0.20)

print('\n--- Justage: Zustandsabfragen ---')
pruefe('neutral ist nicht aktiv', K.Justage().ist_aktiv, False)
pruefe('neutral bricht nichts', K.Justage().bricht_kanten, False)
pruefe('fx gesetzt = aktiv', K.Justage(fx=1.002).ist_aktiv, True)
pruefe('rund gesetzt = aktiv', K.Justage(rund=0.23).ist_aktiv, True)
pruefe('Kante gesetzt = bricht', K.Justage(kante_unten=0.2).bricht_kanten, True)

print('\n--- f_rund: Mittelwert bei getrennten Achsen ---')
j5 = K.Justage(fx=1.004, fy=1.000)
pruefe('Mittelwert', j5.f_rund, 1.002)
pruefe('ohne_kanten behaelt Kalibrierung', j5.ohne_kanten().fx, 1.004)
j6 = K.Justage(fx=1.004, kante_noppe=0.3, kante_unten=0.3, eckradius=0.5)
pruefe('ohne_kanten loescht Noppe', j6.ohne_kanten().kante_noppe, 0.0)
pruefe('ohne_kanten loescht unten', j6.ohne_kanten().kante_unten, 0.0)
pruefe('ohne_kanten behaelt Eckradius', j6.ohne_kanten().eckradius, 0.5)

print('\n--- Profil-Uebernahme: Prozent -> Messwertpaar ---')
prozent = 0.24
soll, ist = 100.0, 100.0 * (1.0 - prozent / 100.0)
pruefe('99,76 als Istwert', round(ist, 2), 99.76)
pruefe('ergibt wieder 0,24 %', round((K._faktor(soll, ist) - 1.0) * 100.0, 3), 0.241)

print('\n--- aus_profil ---')
p_kal = K.PRINT_PROFILES['PETG (Snapmaker U1, kalibriert)']
jp = K.Justage.aus_profil(p_kal)
pruefe('fx aus Profil', round(jp.fx, 5), 1.00241)
pruefe('fx == fy', jp.fx, jp.fy)
pruefe('fz bleibt neutral', jp.fz, 1.0)
pruefe('rund aus Profil', jp.rund, 0.23)
pruefe('ist aktiv', jp.ist_aktiv, True)
p_roh = K.PRINT_PROFILES['PLA (0,2 mm Schicht)']
pruefe('unkalibriertes Profil neutral', K.Justage.aus_profil(p_roh).ist_aktiv, False)

print('\n--- Kantenzahl / Vorschau-Grenze ---')


pruefe('4x2 Stein', K._kantenzahl(K.TYP_STEIN, 4, 2), 14)
pruefe('4x2 unter Grenze',
       K._kantenzahl(K.TYP_STEIN, 4, 2) <= K.VORSCHAU_KANTEN_GRENZE, True)
pruefe('8x8 Stein', K._kantenzahl(K.TYP_STEIN, 8, 8), 162)
pruefe('8x8 ueber Grenze',
       K._kantenzahl(K.TYP_STEIN, 8, 8) > K.VORSCHAU_KANTEN_GRENZE, True)
pruefe('32x32 Stein', K._kantenzahl(K.TYP_STEIN, 32, 32), 2946)
pruefe('Fliese ohne Noppen', K._kantenzahl(K.TYP_FLIESE, 4, 2), 6)
pruefe('1x1 hat nichts', K._kantenzahl(K.TYP_FLIESE, 1, 1), 0)

print('\n--- Dateiname ---')
pruefe('schlicht',
       K._dateiname(K.TYP_STEIN, 4, 2, 0.0, 'PLA (0,2 mm Schicht)'),
       'Stein_4x2_k00')
pruefe('negatives Klemmspiel',
       K._dateiname(K.TYP_STEIN, 4, 2, -0.08, 'PLA (0,2 mm Schicht)'),
       'Stein_4x2_km08')
pruefe('kalibriertes Profil markiert',
       K._dateiname(K.TYP_STEIN, 4, 2, 0.0, 'PETG (Snapmaker U1, kalibriert)'),
       'Stein_4x2_k00_komp')
pruefe('Fase im Namen',
       K._dateiname(K.TYP_STEIN, 4, 2, 0.0, 'PLA (0,2 mm Schicht)', None,
                    K.Justage(kante_unten=0.30)),
       'Stein_4x2_k00_f30')
pruefe('Radius im Namen',
       K._dateiname(K.TYP_STEIN, 4, 2, 0.0, 'PLA (0,2 mm Schicht)', None,
                    K.Justage(kante_unten=0.25, methode=K.METHODE_RADIUS)),
       'Stein_4x2_k00_r25')
pruefe('Schraege im Namen',
       K._dateiname(K.TYP_SCHRAEG, 4, 2, 0.0, 'PLA (0,2 mm Schicht)', 2),
       'Schraegstein_4x2s2_k00')
pruefe('nur erlaubte Zeichen',
       all(c.isalnum() or c in '_-' for c in
           K._dateiname(K.TYP_TECHNIC, 4, 2, 0.05, 'PETG (Snapmaker U1)')), True)

print('\n--- Infotext ---')
txt = K._info_text(K.TYP_STEIN, 2, 2, 'PLA (0,2 mm Schicht)')
pruefe('Rasterhinweis vorhanden', 'Raster' in txt, True)
pruefe('16,00 Raster genannt', '16,00' in txt, True)
pruefe('15,80 Aussenmass genannt', '15,80' in txt, True)

txt2 = K._info_text(K.TYP_STEIN, 4, 2, 'PLA (0,2 mm Schicht)', 0.0, 1,
                    K.Justage(kante_noppe=0.40))
pruefe('Warnung bei grosser Noppenfase', 'Achtung' in txt2, True)
pruefe('Verlust in Prozent genannt', '22 %' in txt2, True)

txt3 = K._info_text(K.TYP_STEIN, 4, 2, 'PLA (0,2 mm Schicht)', 0.0, 1,
                    K.Justage(kante_noppe=0.20))
pruefe('keine Warnung bei 0,20', 'Achtung' not in txt3, True)

txt4 = K._info_text(K.TYP_STEIN, 4, 2, 'PLA (0,2 mm Schicht)', 0.0, 1,
                    K.Justage(fx=1.004, fy=1.000))
pruefe('Warnung bei X/Y-Differenz', 'diagonal' in txt4, True)
txt5 = K._info_text(K.TYP_STEIN, 4, 2, 'PLA (0,2 mm Schicht)', 0.0, 1,
                    K.Justage(fx=1.001, fy=1.000))
pruefe('keine Warnung bei kleiner Differenz', 'diagonal' not in txt5, True)

txt6 = K._info_text(K.TYP_STEIN, 8, 8, 'PLA (0,2 mm Schicht)', 0.0, 1,
                    K.Justage(kante_unten=0.3), True)
pruefe('Vorschauhinweis', 'Live-Vorschau' in txt6, True)

print('\n--- Klemmverlust durch Noppenfase ---')
for mass in (0.10, 0.20, 0.30, 0.40):
    print('   {:.2f} mm Fase -> {:5.1f} % der Noppenhoehe'.format(
        mass, mass / K.STUD_H * 100.0))
pruefe('0,30 sind rund 17 %', round(0.30 / K.STUD_H * 100.0), 17)

print('\n--- Z-Skalierung: was mitwaechst ---')
fz = 1.01
pruefe('Steinhoehe waechst', round(K.BRICK_H * fz, 3), 9.696)
pruefe('Deckplatte bleibt', K.TOP_WALL, 1.0)
pruefe('Kavitaet = Hoehe - Deckplatte', round(K.BRICK_H * fz - K.TOP_WALL, 3), 8.696)

print('\n--- Z-Quantisierung (warum ein Faktor nicht reicht) ---')
for schicht in (0.10, 0.15, 0.16, 0.20, 0.25, 0.32):
    n = K.PLATE_H / schicht
    passt = abs(n - round(n)) < 1e-9
    print('   Schicht {:.2f} mm -> {:6.2f} Schichten fuer 3,2 mm  {}'.format(
        schicht, n, 'teilt sauber' if passt else 'SLICER RUNDET'))
pruefe('0,15 teilt 3,2 nicht', abs(K.PLATE_H / 0.15 - round(K.PLATE_H / 0.15)) > 1e-9, True)
pruefe('0,20 teilt 3,2 sauber', abs(K.PLATE_H / 0.20 - round(K.PLATE_H / 0.20)) < 1e-9, True)

print('\n--- Jumper-Platte: Noppenraster ---')
pruefe('Jumper ist eine Platte', K._hoehe(K.TYP_JUMPER), K.PLATE_H)
pruefe('Jumper in der Typenliste', K.TYP_JUMPER in K.TYPEN, True)


def stellen(typ, nx, ny):
    return K._noppen_stellen(typ, nx, ny)


# Der Klassiker: 1x2 mit genau einer Noppe in der Mitte.
pruefe('1x2 Jumper: eine Noppe', len(stellen(K.TYP_JUMPER, 1, 2)), 1)
pruefe('1x2 Jumper: quer mittig', stellen(K.TYP_JUMPER, 1, 2)[0][0], 0.5)
pruefe('1x2 Jumper: laengs auf dem Kreuz', stellen(K.TYP_JUMPER, 1, 2)[0][1], 1.0)
pruefe('2x1 Jumper: eine Noppe', len(stellen(K.TYP_JUMPER, 2, 1)), 1)
pruefe('2x1 Jumper: laengs auf dem Kreuz', stellen(K.TYP_JUMPER, 2, 1)[0][0], 1.0)

pruefe('2x2 Jumper: eine Noppe zentral', stellen(K.TYP_JUMPER, 2, 2), [(1.0, 1.0)])
pruefe('4x2 Jumper: drei Noppen', len(stellen(K.TYP_JUMPER, 4, 2)), 3)
pruefe('3x3 Jumper: vier Noppen', len(stellen(K.TYP_JUMPER, 3, 3)), 4)
pruefe('1x1 Jumper = normale Platte', stellen(K.TYP_JUMPER, 1, 1), [(0.5, 0.5)])

print('\n--- Jumper: der halbe Rasterversatz stimmt ---')
# Feldmitte einer normalen Platte gegen Kreuz des Jumpers, in mm.
gap = K.PRINT_PROFILES['PLA (0,2 mm Schicht)']['gap']


def mm(n):
    return n * K.PITCH - gap / 2.0


normal = sorted(set(x for x, _ in stellen(K.TYP_PLATTE, 2, 2)))
jumper = sorted(set(x for x, _ in stellen(K.TYP_JUMPER, 2, 2)))
pruefe('Platte 2x2: Noppen bei 3,9 / 11,9 mm',
       [round(mm(n), 2) for n in normal], [3.9, 11.9])
pruefe('Jumper 2x2: Noppe bei 7,9 mm', [round(mm(n), 2) for n in jumper], [7.9])
pruefe('Versatz ist ein halbes Raster',
       round(mm(jumper[0]) - mm(normal[0]), 2), K.PITCH / 2.0)

print('\n--- Jumper: Noppe sitzt ueber Roehre bzw. Steg ---')
# Roehren sitzen bei nx>1 und ny>1 auf den Rasterkreuzen 1..n-1 - also
# genau unter den Jumper-Noppen. Das ist beim echten Teil auch so.
pruefe('2x2: Roehre bei 1,0 - deckt sich mit der Noppe',
       stellen(K.TYP_JUMPER, 2, 2)[0], (1.0, 1.0))
# Bei 1x2 gibt es keine Roehre, sondern einen Steg auf der Mittellinie.
sx_1 = 1 * K.PITCH - gap
pruefe('1x2: Steg liegt auf sx/2 = 3,9', round(sx_1 / 2.0, 2), 3.9)
pruefe('1x2: Noppe liegt genauso bei 3,9',
       round(mm(stellen(K.TYP_JUMPER, 1, 2)[0][0]), 2), 3.9)

print('\n--- Jumper: passt die Noppe auf die Platte? ---')
for nx, ny in ((1, 2), (2, 2), (4, 2)):
    for x, y in stellen(K.TYP_JUMPER, nx, ny):
        links = mm(x) - K.STUD_D / 2.0
        rechts = (nx * K.PITCH - gap) - (mm(x) + K.STUD_D / 2.0)
        ok = links > 0.5 and rechts > 0.5
        print('   {}x{} Noppe bei x={:5.2f}  Rand links {:.2f} / rechts {:.2f}  {}'
              .format(nx, ny, mm(x), links, rechts, 'ok' if ok else 'ZU ENG'))
        if not ok:
            fehler.append('Jumper {}x{} Noppenrand'.format(nx, ny))

print('\n--- Jumper: 1x1 klemmt darauf nicht (bekannte Grenze) ---')
p_pla = K.PRINT_PROFILES['PLA (0,2 mm Schicht)']
innen = K.PITCH - p_pla['gap'] - 2 * p_pla['wall']
pruefe('Hohlraum einer 1x1', round(innen, 2), 5.4)
pruefe('Luft zur Noppe', round(innen - K.STUD_D, 2), 0.6)
pruefe('noetige Wandstaerke', round((K.PITCH - p_pla['gap'] - K.STUD_D) / 2.0, 2), 1.5)
txt_j = K._info_text(K.TYP_JUMPER, 1, 2, 'PLA (0,2 mm Schicht)')
pruefe('Infozeile warnt davor', '1x1-Platte klemmt' in txt_j, True)
pruefe('Infozeile nennt den Versatz', '4,00 mm' in txt_j, True)

print('\n--- Jumper: Noppenzahl in der Infozeile ---')
for nx, ny, soll in ((1, 2, 1), (2, 2, 1), (4, 2, 3), (3, 3, 4)):
    t = K._info_text(K.TYP_JUMPER, nx, ny, 'PLA (0,2 mm Schicht)')
    marke = '<b>Noppen:</b> {} '.format(soll)
    pruefe('{}x{} meldet {} Noppen'.format(nx, ny, soll), marke in t, True)

print('\n--- Bestehende Typen unveraendert ---')
pruefe('Stein 4x2 hat 8 Noppen', len(stellen(K.TYP_STEIN, 4, 2)), 8)
pruefe('Stein: erste Noppe auf Feldmitte', stellen(K.TYP_STEIN, 4, 2)[0], (0.5, 0.5))
pruefe('Platte 2x2 hat 4 Noppen', len(stellen(K.TYP_PLATTE, 2, 2)), 4)
pruefe('Kantenzahl Jumper 4x2', K._kantenzahl(K.TYP_JUMPER, 4, 2), 9)
pruefe('Kantenzahl Stein 4x2 unveraendert', K._kantenzahl(K.TYP_STEIN, 4, 2), 14)

print('\n--- Neue Typen: Hoehen ---')
pruefe('Halbstein 4,8 mm', K._hoehe(K.TYP_HALBSTEIN), 4.8)
pruefe('zwei Halbsteine = ein Stein', K._hoehe(K.TYP_HALBSTEIN) * 2, K.BRICK_H)
pruefe('drei Platten = ein Stein', round(K._hoehe(K.TYP_PLATTE) * 3, 4), K.BRICK_H)
pruefe('Lochbalken hat Steinhoehe', K._hoehe(K.TYP_LOCHBALKEN), K.BRICK_H)
pruefe('alle Typen eindeutig', len(K.TYPEN), len(set(K.TYPEN)))

print('\n--- Eckstein: L-Form ---')
pruefe('Schenkel begrenzt auf min-1', K._schenkel(2, 2, 5), 1)
pruefe('Schenkel mindestens 1', K._schenkel(4, 4, 0), 1)
pruefe('Schenkel 2 bei 4x4 erlaubt', K._schenkel(4, 4, 2), 2)

# 2x2 mit Schenkel 1 = der klassische Eckstein aus drei Feldern.
eck22 = K._noppen_stellen(K.TYP_ECK, 2, 2, 1)
pruefe('2x2 Eckstein: 3 Noppen', len(eck22), 3)
pruefe('2x2 Eckstein: Aussenecke fehlt', (1.5, 1.5) not in eck22, True)
pruefe('2x2 Eckstein: Innenecke da', (0.5, 0.5) in eck22, True)

eck44 = K._noppen_stellen(K.TYP_ECK, 4, 4, 2)
pruefe('4x4 Schenkel 2: 12 Noppen', len(eck44), 12)
pruefe('4x4: Feld (3,3) fehlt', (3.5, 3.5) not in eck44, True)
pruefe('4x4: Feld (3,0) da', (3.5, 0.5) in eck44, True)
pruefe('4x4: Feld (0,3) da', (0.5, 3.5) in eck44, True)

print('\n--- Eckstein: L-Polygon schliesst sich ---')
poly = K._l_polygon(31.8, 31.8, 7.9)
pruefe('sechs Ecken', len(poly), 6)
pruefe('startet im Ursprung', poly[0], (0.0, 0.0))
pruefe('einspringende Ecke vorhanden', (7.9, 7.9) in poly, True)
# Flaeche ueber die Gauss-Formel: muss der L-Flaeche entsprechen.
flaeche = abs(sum(poly[i][0] * poly[(i + 1) % 6][1] - poly[(i + 1) % 6][0] * poly[i][1]
                  for i in range(6))) / 2.0
soll_flaeche = 31.8 * 7.9 + 7.9 * (31.8 - 7.9)
pruefe('Flaeche stimmt', round(flaeche, 4), round(soll_flaeche, 4))

print('\n--- Rundstein ---')
pruefe('Rundstein erkannt', K._ist_rund(K.TYP_RUND), True)
pruefe('Stein nicht rund', K._ist_rund(K.TYP_STEIN), False)
rund2 = K._noppen_stellen(K.TYP_RUND, 2, 2)
pruefe('2x2 rund: 4 Noppen passen', len(rund2), 4)
rund4 = K._noppen_stellen(K.TYP_RUND, 4, 4)
pruefe('4x4 rund: Eckennoppen entfallen', len(rund4) < 16, True)
print('   4x4 rund behaelt {} von 16 Noppen'.format(len(rund4)))
pruefe('4x4 rund: Eckfeld (0,0) faellt weg', (0.5, 0.5) not in rund4, True)
pruefe('4x4 rund: Mittelfeld bleibt', (1.5, 1.5) in rund4, True)
# Nachrechnen: Noppe in der Ecke, Rand des Kreises.
r = (4 * K.PITCH - 0.2) / 2.0
d_ecke = ((0.5 * K.PITCH - 0.1 - r) ** 2 * 2) ** 0.5
print('   Eckfeld-Mitte {:.2f} mm vom Zentrum, Radius {:.2f} mm'.format(d_ecke, r))
pruefe('Eckfeld ragt hinaus', d_ecke + K.STUD_D / 2.0 > r, True)

print('\n--- Achskreuz ---')
kreuz = K._achskreuz(4.8, 1.8)
pruefe('zwoelf Ecken', len(kreuz), 12)
xs_k = [x for x, _ in kreuz]
ys_k = [y for _, y in kreuz]
pruefe('Spannweite X', round(max(xs_k) - min(xs_k), 3), 4.8)
pruefe('Spannweite Y', round(max(ys_k) - min(ys_k), 3), 4.8)
pruefe('symmetrisch um null', round(max(xs_k) + min(xs_k), 9), 0.0)
# Flaeche = zwei Rechtecke minus die Ueberlappung in der Mitte.
fl_k = abs(sum(kreuz[i][0] * kreuz[(i + 1) % 12][1] - kreuz[(i + 1) % 12][0] * kreuz[i][1]
               for i in range(12))) / 2.0
pruefe('Kreuzflaeche', round(fl_k, 4), round(4.8 * 1.8 * 2 - 1.8 * 1.8, 4))

print('\n--- Bohrung passt in die Bauteilhoehe ---')
for typ in (K.TYP_TECHNIC, K.TYP_LOCHBALKEN):
    rest = K._hoehe(typ) - K.TECHNIC_AXIS_Z
    ok = rest >= K.TECHNIC_HOLE_D / 2.0
    print('   {:<22} Achse {:.1f} / Hoehe {:.1f} -> {:.1f} mm Rest  {}'.format(
        typ, K.TECHNIC_AXIS_Z, K._hoehe(typ), rest, 'ok' if ok else 'BRICHT AUS'))
    if not ok:
        fehler.append('Bohrung {}'.format(typ))
# Gegenprobe: eine Platte waere zu flach - die Validierung muss das sperren.
pruefe('Platte waere zu flach fuer eine Bohrung',
       K._hoehe(K.TYP_PLATTE) - K.TECHNIC_AXIS_Z < K.TECHNIC_HOLE_D / 2.0, True)

print('\n--- Lochbalken hat keine Noppen ---')
pruefe('Lochbalken ohne Noppen', K._noppen_stellen(K.TYP_LOCHBALKEN, 4, 2), [])
pruefe('Fliese ohne Noppen', K._noppen_stellen(K.TYP_FLIESE, 4, 2), [])
pruefe('Halbstein mit Noppen', len(K._noppen_stellen(K.TYP_HALBSTEIN, 4, 2)), 8)

print('\n--- Infozeile fuer die neuen Typen ---')
for typ, nx, ny in ((K.TYP_HALBSTEIN, 4, 2), (K.TYP_LOCHBALKEN, 4, 1),
                    (K.TYP_ECK, 2, 2), (K.TYP_RUND, 2, 2), (K.TYP_JUMPER, 1, 2)):
    t = K._info_text(typ, nx, ny, 'PLA (0,2 mm Schicht)')
    ok = len(t) > 50 and 'Aussenmass' in t
    print('   {:<22} {} Zeichen  {}'.format(typ, len(t), 'ok' if ok else 'LEER'))
    if not ok:
        fehler.append('Infotext ' + typ)

t_rund = K._info_text(K.TYP_RUND, 2, 2, 'PLA (0,2 mm Schicht)')
pruefe('Rundstein meldet Durchmesser', 'oslash' in t_rund.split('<br/>')[0], True)
t_ax = K._info_text(K.TYP_TECHNIC, 4, 2, 'PLA (0,2 mm Schicht)', 0.0, 1, None,
                    False, 1, K.BOHRUNG_ACHSE)
pruefe('Achskreuz in der Infozeile', 'Achskreuz' in t_ax, True)
t_eck = K._info_text(K.TYP_ECK, 2, 2, 'PLA (0,2 mm Schicht)', 0.0, 1, None,
                     False, 9)
pruefe('gekappte Schenkelbreite gemeldet', 'begrenzt' in t_eck, True)

print('\n--- Dateinamen der neuen Typen ---')
pruefe('Rundstein', K._dateiname(K.TYP_RUND, 2, 2, 0.0, 'PLA (0,2 mm Schicht)'),
       'Rundstein_d2_k00')
pruefe('Eckstein mit Schenkel',
       K._dateiname(K.TYP_ECK, 4, 4, 0.0, 'PLA (0,2 mm Schicht)', None, None, 2),
       'Eckstein_4x4L2_k00')
pruefe('Achskreuz markiert',
       K._dateiname(K.TYP_TECHNIC, 4, 2, 0.0, 'PLA (0,2 mm Schicht)', None,
                    None, None, K.BOHRUNG_ACHSE),
       'Technic-Stein_4x2ax_k00')
pruefe('Halbstein', K._dateiname(K.TYP_HALBSTEIN, 4, 2, 0.0, 'PLA (0,2 mm Schicht)'),
       'Halbstein_4x2_k00')

print('\n--- Kantenzahl mit neuer Signatur ---')
pruefe('Stein 4x2 unveraendert', K._kantenzahl(K.TYP_STEIN, 4, 2), 14)
pruefe('Jumper 4x2', K._kantenzahl(K.TYP_JUMPER, 4, 2), 9)
pruefe('Lochbalken ohne Noppen', K._kantenzahl(K.TYP_LOCHBALKEN, 4, 2), 6)
pruefe('Eckstein 2x2 Schenkel 1', K._kantenzahl(K.TYP_ECK, 2, 2, 1), 5)
pruefe('Rundstein nutzt nx fuer beide', K._kantenzahl(K.TYP_RUND, 2, 9), 6)

print('\n--- Bestehende Typen weiterhin unveraendert ---')
pruefe('Stein 4x2 hat 8 Noppen', len(K._noppen_stellen(K.TYP_STEIN, 4, 2)), 8)
pruefe('Platte 2x2 hat 4 Noppen', len(K._noppen_stellen(K.TYP_PLATTE, 2, 2)), 4)
pruefe('Jumper 1x2 hat 1 Noppe', len(K._noppen_stellen(K.TYP_JUMPER, 1, 2)), 1)
pruefe('Schraegstein 4x2 mit 2er-Schraege',
       len(K._noppen_stellen(K.TYP_SCHRAEG, 4, 2, 1, 0.20, 2)), 4)
pruefe('Technic 4x2 hat 8 Noppen', len(K._noppen_stellen(K.TYP_TECHNIC, 4, 2)), 8)

print('\n' + '=' * 70)
if fehler:
    print('FEHLGESCHLAGEN: {}'.format(len(fehler)))
    for f_ in fehler:
        print('  - ' + f_)
    sys.exit(1)
print('Alle Pruefungen bestanden.')
