# -*- coding: utf-8 -*-
"""SVG-Zeichnungen aus den echten Konstruktionsdaten.

Die Bilder der Anleitung werden nicht abgemalt, sondern aus denselben
Funktionen erzeugt, die auch die Geometrie in Fusion bauen. Aendert sich
eine Noppenposition im Generator, aendert sie sich hier mit - eine Anleitung,
die etwas anderes zeigt als das Werkzeug, waere schlimmer als gar keine.

Gezeichnet wird in mm; die Umrechnung in Bildpunkte macht am Ende nur die
Skalierung. Y zeigt in der Zeichnung nach oben, in SVG nach unten - deshalb
wird gespiegelt.
"""

import math

FARBEN = {
    'material': '#d8dee9',
    'kante': '#2e3440',
    'noppe': '#88a0c0',
    'noppe_kante': '#3b5478',
    'roehre': '#b8c4d4',
    'verdeckt': '#8c98a8',
    'mass': '#bf616a',
    'hinweis': '#5e81ac',
    'hohlraum': '#eceff4',
}


class Bild(object):
    """Sammelt SVG-Elemente und rechnet mm in Bildpunkte um."""

    def __init__(self, x0, y0, x1, y1, rand=9.0, skala=7.0, titel=''):
        self.x0, self.y0 = x0 - rand, y0 - rand
        self.breite_mm = (x1 - x0) + 2 * rand
        self.hoehe_mm = (y1 - y0) + 2 * rand
        self.skala = skala
        self.titel = titel
        self.teile = []

    # -- Koordinaten --------------------------------------------------------
    def px(self, x_mm):
        return (x_mm - self.x0) * self.skala

    def py(self, y_mm):
        """Y spiegeln: in der Konstruktion zeigt Y nach oben, in SVG nach unten."""
        return (self.hoehe_mm - (y_mm - self.y0)) * self.skala

    def laenge(self, mm):
        return mm * self.skala

    # -- Elemente -----------------------------------------------------------
    def pfad(self, punkte, fuellung, linie, breite=1.2, strich=None, deckung=1.0):
        d = ' '.join(('M' if k == 0 else 'L') + '{:.2f},{:.2f}'.format(
            self.px(x), self.py(y)) for k, (x, y) in enumerate(punkte)) + ' Z'
        self.teile.append(
            '<path d="{}" fill="{}" stroke="{}" stroke-width="{:.2f}"{}{}/>'.format(
                d, fuellung, linie, breite,
                ' stroke-dasharray="{}"'.format(strich) if strich else '',
                ' opacity="{:.2f}"'.format(deckung) if deckung < 1.0 else ''))

    def rechteck(self, x, y, b, h, fuellung, linie, breite=1.2, strich=None):
        self.pfad([(x, y), (x + b, y), (x + b, y + h), (x, y + h)],
                  fuellung, linie, breite, strich)

    def kreis(self, x, y, d, fuellung, linie, breite=1.2, strich=None, deckung=1.0):
        self.teile.append(
            '<circle cx="{:.2f}" cy="{:.2f}" r="{:.2f}" fill="{}" stroke="{}" '
            'stroke-width="{:.2f}"{}{}/>'.format(
                self.px(x), self.py(y), self.laenge(d / 2.0), fuellung, linie,
                breite, ' stroke-dasharray="{}"'.format(strich) if strich else '',
                ' opacity="{:.2f}"'.format(deckung) if deckung < 1.0 else ''))

    def linie(self, x1, y1, x2, y2, farbe, breite=1.0, strich=None):
        self.teile.append(
            '<line x1="{:.2f}" y1="{:.2f}" x2="{:.2f}" y2="{:.2f}" stroke="{}" '
            'stroke-width="{:.2f}"{}/>'.format(
                self.px(x1), self.py(y1), self.px(x2), self.py(y2), farbe,
                breite, ' stroke-dasharray="{}"'.format(strich) if strich else ''))

    def text(self, x, y, inhalt, farbe=None, groesse=8.0, anker='middle',
             fett=False):
        self.teile.append(
            '<text x="{:.2f}" y="{:.2f}" fill="{}" font-size="{:.1f}" '
            'text-anchor="{}" font-family="system-ui,sans-serif"{}>{}</text>'.format(
                self.px(x), self.py(y), farbe or FARBEN['kante'], groesse,
                anker, ' font-weight="600"' if fett else '', inhalt))

    def masslinie(self, x1, y1, x2, y2, beschriftung, versatz=0.0, anker=None):
        """Bemassung mit Pfeilen an beiden Enden.

        Bei senkrechten Massen steht die Beschriftung daneben. Wohin sie
        ausgerichtet wird, muss der Aufrufer bestimmen koennen: links vom
        Bauteil braucht sie 'end', sonst laeuft sie aus dem Bild.
        """
        self.teile.append(
            '<line x1="{:.2f}" y1="{:.2f}" x2="{:.2f}" y2="{:.2f}" stroke="{}" '
            'stroke-width="0.9" marker-start="url(#pfeil)" '
            'marker-end="url(#pfeil)"/>'.format(
                self.px(x1), self.py(y1), self.px(x2), self.py(y2),
                FARBEN['mass']))
        mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        senkrecht = abs(x2 - x1) < abs(y2 - y1)
        self.text(mx + (versatz if senkrecht else 0.0),
                  my + (0.0 if senkrecht else versatz),
                  beschriftung, FARBEN['mass'], 7.5,
                  anker or ('start' if senkrecht else 'middle'))

    # -- Ausgabe ------------------------------------------------------------
    def svg(self):
        b = self.breite_mm * self.skala
        h = self.hoehe_mm * self.skala
        # Die viewBox legt nur die Proportionen fest; wie gross die Zeichnung
        # am Ende erscheint, entscheidet diese Obergrenze. Ohne sie wuerde ein
        # Detailbild mit wenigen Millimetern Motiv den halben Bildschirm
        # fuellen, ein 32er-Stein dagegen briefmarkengross bleiben.
        max_px = min(b * 2.4, 620.0)
        return (
            '<svg viewBox="0 0 {:.1f} {:.1f}" width="100%" '
            'style="max-width:{:.0f}px" role="img" aria-label="{}" '
            'xmlns="http://www.w3.org/2000/svg">'
            '<defs><marker id="pfeil" viewBox="0 0 10 10" refX="9" refY="5" '
            'markerWidth="5" markerHeight="5" orient="auto-start-reverse">'
            '<path d="M0,1 L9,5 L0,9 z" fill="{}"/></marker></defs>{}</svg>'
        ).format(b, h, max_px, self.titel, FARBEN['mass'], ''.join(self.teile))


# ---------------------------------------------------------------------------
# Draufsicht eines Bauteils
# ---------------------------------------------------------------------------

def draufsicht(K, typ, nx, ny, schenkel=1, bemassen=True, skala=7.0):
    """Grundriss mit Noppen oben und Roehren gestrichelt darunter."""
    p = K.PRINT_PROFILES['PLA (0,2 mm Schicht)']
    gap, wall = p['gap'], p['wall']
    if K._ist_rund(typ):
        ny = nx
    w = K._schenkel(nx, ny, schenkel)

    sx = nx * K.PITCH - gap
    sy = ny * K.PITCH - gap
    # Ohne Bemassung braucht es nur so viel Rand, dass die Kante nicht am
    # Bildrand klebt - sonst steht die Zeichnung verloren im Weissraum.
    bild = Bild(0, 0, sx, sy, rand=9.0 if bemassen else 2.5, skala=skala,
                titel='Draufsicht {} {}x{}'.format(typ, nx, ny))

    def mm(n):
        return n * K.PITCH - gap / 2.0

    # --- Umriss ---
    if K._ist_rund(typ):
        bild.kreis(sx / 2.0, sy / 2.0, sx, FARBEN['material'], FARBEN['kante'], 1.4)
    elif typ == K.TYP_ECK:
        bild.pfad(K._l_polygon(sx, sy, w * K.PITCH - gap / 2.0),
                  FARBEN['material'], FARBEN['kante'], 1.4)
    else:
        bild.rechteck(0, 0, sx, sy, FARBEN['material'], FARBEN['kante'], 1.4)

    # --- Rasterlinien, damit der Versatz der Jumper-Noppen sichtbar wird ---
    for i in range(1, nx):
        bild.linie(mm(i), 0, mm(i), sy, '#ffffff', 0.7, '3,3')
    for j in range(1, ny):
        bild.linie(0, mm(j), sx, mm(j), '#ffffff', 0.7, '3,3')

    # --- Noppen ---
    for i, j in K._noppen_stellen(typ, nx, ny, w, gap):
        bild.kreis(mm(i), mm(j), K.STUD_D, FARBEN['noppe'],
                   FARBEN['noppe_kante'], 1.0)

    # --- Roehren und Stege: verdeckt, deshalb gestrichelt ---
    # Bewusst NACH den Noppen. Ein Steg misst 3,20 mm und laege sonst
    # vollstaendig unter der 4,80 mm dicken Noppe - gerade beim Jumper waere
    # dann nicht zu sehen, dass die Noppe genau ueber dem Steg sitzt.
    for i, j in K._roehren_stellen(typ, nx, ny, w, gap, wall):
        bild.kreis(mm(i), mm(j), K.TUBE_OD, 'none', FARBEN['verdeckt'], 1.1, '3,2')
        bild.kreis(mm(i), mm(j), K.TUBE_ID, 'none', FARBEN['verdeckt'], 0.7, '2,2')
    for i, j in K._stege_stellen(typ, nx, ny):
        bild.kreis(mm(i), mm(j), K.PIN_D, 'none', FARBEN['verdeckt'], 1.1, '3,2')

    if bemassen:
        bild.masslinie(0, -4.0, sx, -4.0,
                       ('&oslash; ' if K._ist_rund(typ) else '')
                       + '{:.2f} mm'.format(sx).replace('.', ','), -2.6)
        if not K._ist_rund(typ):
            bild.masslinie(-4.0, 0, -4.0, sy,
                           '{:.2f} mm'.format(sy).replace('.', ','), -3.2)
    return bild.svg()


# ---------------------------------------------------------------------------
# Schnitt durch einen Stein
# ---------------------------------------------------------------------------

def schnitt(K, typ, nx=2, skala=9.0):
    """Laengsschnitt: Deckplatte, Hohlraum, Roehre, Noppe."""
    p = K.PRINT_PROFILES['PLA (0,2 mm Schicht)']
    gap, wall = p['gap'], p['wall']
    hoehe = K._hoehe(typ)
    sx = nx * K.PITCH - gap
    kavitaet = hoehe - K.TOP_WALL
    hat_hohlraum = typ != K.TYP_GRUNDPLATTE

    # Grosszuegiger Rand links: dort steht die Bemassung der Deckplatte.
    bild = Bild(0, 0, sx, hoehe + K.STUD_H, rand=15.0, skala=skala,
                titel='Schnitt {}'.format(typ))

    # Vollmaterial, danach der Hohlraum als Aussparung darauf.
    bild.rechteck(0, 0, sx, hoehe, FARBEN['material'], FARBEN['kante'], 1.4)
    if hat_hohlraum:
        bild.rechteck(wall, 0, sx - 2 * wall, kavitaet,
                      FARBEN['hohlraum'], FARBEN['kante'], 1.0)
        # Roehre in der Mitte - im Schnitt zwei Wandstuecke.
        if nx > 1:
            mitte = sx / 2.0
            for vz in (-1, 1):
                aussen = mitte + vz * K.TUBE_OD / 2.0
                innen = mitte + vz * K.TUBE_ID / 2.0
                bild.rechteck(min(aussen, innen), 0, abs(aussen - innen),
                              kavitaet, FARBEN['roehre'], FARBEN['kante'], 1.0)

    # Noppen obenauf
    for i in range(nx):
        x = (i + 0.5) * K.PITCH - gap / 2.0
        bild.rechteck(x - K.STUD_D / 2.0, hoehe, K.STUD_D, K.STUD_H,
                      FARBEN['noppe'], FARBEN['noppe_kante'], 1.0)

    bild.masslinie(sx + 3.0, 0, sx + 3.0, hoehe,
                   '{:.2f} mm'.format(hoehe).replace('.', ','), 1.2)
    bild.masslinie(sx + 3.0, hoehe, sx + 3.0, hoehe + K.STUD_H,
                   'Noppe {:.2f}'.format(K.STUD_H).replace('.', ','), 1.2)
    if hat_hohlraum:
        # Links vom Bauteil: der Text muss nach innen laufen, sonst steht er
        # ausserhalb der Zeichenflaeche.
        bild.masslinie(-3.0, kavitaet, -3.0, hoehe,
                       'Deckplatte {:.2f}'.format(K.TOP_WALL).replace('.', ','),
                       -1.2, 'end')
    return bild.svg()


# ---------------------------------------------------------------------------
# Detail: wo die Klemmung entsteht
# ---------------------------------------------------------------------------

def klemmdetail(K, skala=17.0):
    """Noppe und Roehre in Draufsicht - der tangentiale Kontakt."""
    bild = Bild(-1.0, -1.0, 9.0, 9.0, rand=5.0, skala=skala,
                titel='Klemmkontakt zwischen Noppe und Roehre')

    # Noppe im Ursprung, Roehre auf dem diagonal benachbarten Rasterkreuz.
    bild.kreis(4.0, 4.0, K.TUBE_OD, FARBEN['roehre'], FARBEN['kante'], 1.2)
    bild.kreis(4.0, 4.0, K.TUBE_ID, '#ffffff', FARBEN['kante'], 1.0)
    bild.kreis(0.0, 0.0, K.STUD_D, FARBEN['noppe'], FARBEN['noppe_kante'], 1.2)

    bild.linie(0.0, 0.0, 4.0, 4.0, FARBEN['mass'], 1.0, '3,2')
    bild.text(2.4, 1.5, '5,657 mm', FARBEN['mass'], 7.0, 'middle')
    bild.text(0.0, -3.6, 'Noppe &oslash; 4,80', FARBEN['noppe_kante'], 7.0)
    bild.text(4.0, 8.4, 'R&ouml;hre &oslash; 6,51', FARBEN['kante'], 7.0)

    # Der Beruehrpunkt liegt auf der Diagonalen, 2,4 mm von der Noppenmitte.
    bx = by = 2.4 / math.sqrt(2.0)
    bild.kreis(bx, by, 0.5, FARBEN['mass'], FARBEN['mass'], 0.5)
    bild.text(6.6, 3.0, '0,002 mm Rest', FARBEN['mass'], 7.0, 'start')
    return bild.svg()


# ---------------------------------------------------------------------------
# Detail: Kantenbrechung
# ---------------------------------------------------------------------------

def kantendetail(K, mass=0.3, skala=34.0):
    """Noppenoberkante als Fase und als Radius, im Schnitt."""
    bild = Bild(0, 0, 13.0, 3.2, rand=2.4, skala=skala,
                titel='Fase und Radius an der Noppenoberkante')
    d, h = K.STUD_D, K.STUD_H

    def noppe(x0, art):
        if art == 'scharf':
            punkte = [(x0, 0), (x0 + d, 0), (x0 + d, h), (x0, h)]
        elif art == 'fase':
            punkte = [(x0, 0), (x0 + d, 0), (x0 + d, h - mass),
                      (x0 + d - mass, h), (x0 + mass, h), (x0, h - mass)]
        else:
            punkte = [(x0, 0), (x0 + d, 0), (x0 + d, h - mass), (x0, h - mass)]
        bild.pfad(punkte, FARBEN['noppe'], FARBEN['noppe_kante'], 1.2)
        if art == 'radius':
            # Viertelkreise als Ersatz fuer die abgerundeten Ecken.
            for vz, cx in ((1, x0 + d - mass), (-1, x0 + mass)):
                bogen = [(cx + vz * mass * math.cos(math.radians(g)),
                          h - mass + mass * math.sin(math.radians(g)))
                         for g in range(0, 91, 9)]
                bild.pfad([(cx, h - mass)] + bogen, FARBEN['noppe'],
                          FARBEN['noppe_kante'], 1.2)

    for x0, art, name in ((0.0, 'scharf', 'scharf (0,00)'),
                          (4.4, 'fase', 'Fase 0,30'),
                          (8.8, 'radius', 'Radius 0,30')):
        noppe(x0, art)
        bild.text(x0 + d / 2.0, -1.4, name, FARBEN['kante'], 7.0)
    bild.text(6.5, 3.7, 'Klemmung wirkt &uuml;ber die volle Noppenh&ouml;he von 1,80 mm',
              FARBEN['hinweis'], 7.0)
    return bild.svg()


# ---------------------------------------------------------------------------
# Detail: Achskreuz gegen Rundloch
# ---------------------------------------------------------------------------

def bohrungsdetail(K, skala=17.0):
    bild = Bild(0, 0, 16.0, 7.0, rand=3.0, skala=skala,
                titel='Rundloch und Achskreuz im Vergleich')
    for mx, art in ((3.5, 'rund'), (12.0, 'kreuz')):
        bild.rechteck(mx - 3.5, 0, 7.0, 7.0, FARBEN['material'],
                      FARBEN['kante'], 1.2)
        if art == 'rund':
            bild.kreis(mx, 3.5, K.TECHNIC_HOLE_D, '#ffffff', FARBEN['kante'], 1.2)
            bild.text(mx, -1.6, 'Rundloch &oslash; 4,80', FARBEN['kante'], 7.0)
        else:
            bild.pfad([(mx + dx, 3.5 + dy)
                       for dx, dy in K._achskreuz(K.AXLE_SPAN, K.AXLE_ARM)],
                      '#ffffff', FARBEN['kante'], 1.2)
            bild.text(mx, -1.6, 'Achskreuz 4,80 / 1,80', FARBEN['kante'], 7.0)
    return bild.svg()


# ---------------------------------------------------------------------------
# Vergleich: Noppenraster normal gegen Jumper
# ---------------------------------------------------------------------------

def jumpervergleich(K, skala=7.0):
    return (draufsicht(K, K.TYP_PLATTE, 2, 2, skala=skala),
            draufsicht(K, K.TYP_JUMPER, 2, 2, skala=skala))
