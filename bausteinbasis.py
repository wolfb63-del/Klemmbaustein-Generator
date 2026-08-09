# -*- coding: utf-8 -*-
"""
bausteinbasis - gemeinsamer Unterbau fuer die Generator-Add-Ins
===============================================================

Enthaelt alles, was nicht von der konkreten Geometrie abhaengt:
Einheitenumrechnung, Skizzenhelfer, Extrusionen, Dialogsuche,
Einstellungsspeicher, Druckerkompensation und STL-Export.

Dieses Modul liegt bewusst als Kopie im jeweiligen Add-In-Ordner, damit
jedes Add-In fuer sich allein lauffaehig und weitergebbar bleibt.
Aenderungen gehoeren in die Quelle im Projektordner und werden von dort
in die Add-Ins verteilt.
"""

import json
import math
import os

import adsk.core
import adsk.fusion


# ---------------------------------------------------------------------------
# Einheiten
# ---------------------------------------------------------------------------

MM = 0.1   # Fusion rechnet intern in cm -> 1 mm = 0.1 cm

# Grenzen fuer den Schrumpfvorhalt aus einem Druckprofil. Bewusst dieselben
# Werte wie FAKTOR_MIN/MAX im Klemmbaustein-Add-In: Beide beschreiben, was ein
# Drucker plausibel danebenliegt. Alles darueber ist ein Tippfehler, kein
# Messergebnis.
SCHRUMPF_MIN = 0.98
SCHRUMPF_MAX = 1.02


def pt(x_mm, y_mm, z_mm=0.0):
    """Point3D aus mm-Angaben."""
    return adsk.core.Point3D.create(x_mm * MM, y_mm * MM, z_mm * MM)


def val(mm):
    """ValueInput in Fusion-Interneinheiten aus einer mm-Angabe."""
    return adsk.core.ValueInput.createByReal(mm * MM)


def winkel(grad):
    """ValueInput fuer einen Winkel. Ueber den String-Weg, weil
    createByReal Winkel im Bogenmass erwartet - eine beliebte Fehlerquelle."""
    return adsk.core.ValueInput.createByString('{} deg'.format(grad))


def de(zahl, nachkomma=2):
    """Zahl mit deutschem Dezimalkomma."""
    return ('{:.' + str(nachkomma) + 'f}').format(zahl).replace('.', ',')


# ---------------------------------------------------------------------------
# Skizzenhelfer
# ---------------------------------------------------------------------------

def rechteck(sketch, x1, y1, x2, y2):
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(pt(x1, y1), pt(x2, y2))


def rundrechteck(sketch, x1, y1, x2, y2, r):
    """Achsparalleles Rechteck mit verrundeten Ecken.

    Bewusst aus vier Linien und vier Boegen mit festen Koordinaten gebaut
    statt ueber Skizzen-Fillets: keine Constraints, kein Trimmen, damit
    voellig deterministisch. Genau das braucht die verjuengte Extrusion,
    denn dort muss der Eckradius von unten nach oben exakt mitwachsen.
    """
    if r <= 1e-9:
        rechteck(sketch, x1, y1, x2, y2)
        return

    # Sicherheitsnetz: ein zu grosser Radius wuerde sich selbst ueberschneiden.
    r = min(r, (x2 - x1) / 2.0 - 1e-6, (y2 - y1) / 2.0 - 1e-6)

    linien = sketch.sketchCurves.sketchLines
    boegen = sketch.sketchCurves.sketchArcs
    viertel = math.pi / 2.0

    linien.addByTwoPoints(pt(x1 + r, y1), pt(x2 - r, y1))   # unten
    linien.addByTwoPoints(pt(x2, y1 + r), pt(x2, y2 - r))   # rechts
    linien.addByTwoPoints(pt(x2 - r, y2), pt(x1 + r, y2))   # oben
    linien.addByTwoPoints(pt(x1, y2 - r), pt(x1, y1 + r))   # links

    # Jeder Bogen laeuft gegen den Uhrzeigersinn vom Ende der einen zur
    # Anfangskante der naechsten Geraden.
    boegen.addByCenterStartSweep(pt(x2 - r, y1 + r), pt(x2 - r, y1), viertel)
    boegen.addByCenterStartSweep(pt(x2 - r, y2 - r), pt(x2, y2 - r), viertel)
    boegen.addByCenterStartSweep(pt(x1 + r, y2 - r), pt(x1 + r, y2), viertel)
    boegen.addByCenterStartSweep(pt(x1 + r, y1 + r), pt(x1, y1 + r), viertel)


def kreis(sketch, x, y, durchmesser):
    sketch.sketchCurves.sketchCircles.addByCenterRadius(pt(x, y), durchmesser / 2.0 * MM)


def alle_profile(sketch):
    coll = adsk.core.ObjectCollection.create()
    for prof in sketch.profiles:
        coll.add(prof)
    return coll


def sammle(objekte):
    coll = adsk.core.ObjectCollection.create()
    for o in objekte:
        coll.add(o)
    return coll


# ---------------------------------------------------------------------------
# Extrusionen
# ---------------------------------------------------------------------------

# Vorzeichen des Verjuengungswinkels. Positiv = die Extrusion wird in
# Richtung der Extrusion breiter. Sollte sich Fusion hier je andersherum
# verhalten, ist das die eine Stelle zum Umdrehen.
TAPER_VZ = 1.0


def extrude(comp, profile, start_mm, dist_mm, operation,
            participants=None, taper_grad=0.0, nach_unten=False):
    """Extrusion senkrecht zur Skizzenebene.

    start_mm      Versatz der Startflaeche gegenueber der Skizzenebene
    dist_mm       Laenge der Extrusion (immer positiv angeben)
    taper_grad    Verjuengungswinkel; positiv = wird breiter
    nach_unten    extrudiert entgegen der Flaechennormalen
    """
    extrudes = comp.features.extrudeFeatures
    ext_input = extrudes.createInput(profile, operation)

    if abs(start_mm) > 1e-9:
        ext_input.startExtent = adsk.fusion.OffsetStartDefinition.create(val(start_mm))

    richtung = (adsk.fusion.ExtentDirections.NegativeExtentDirection if nach_unten
                else adsk.fusion.ExtentDirections.PositiveExtentDirection)
    weite = adsk.fusion.DistanceExtentDefinition.create(val(dist_mm))

    if abs(taper_grad) > 1e-9:
        ext_input.setOneSideExtent(weite, richtung, winkel(taper_grad * TAPER_VZ))
    else:
        ext_input.setOneSideExtent(weite, richtung)

    if participants:
        ext_input.participantBodies = participants

    return extrudes.add(ext_input)


def durchbruch(comp, profile, participants):
    """Schnitt durch alles, in beide Richtungen ab der Skizzenebene."""
    extrudes = comp.features.extrudeFeatures
    ext_input = extrudes.createInput(
        profile, adsk.fusion.FeatureOperations.CutFeatureOperation)
    ext_input.setAllExtent(adsk.fusion.ExtentDirections.SymmetricExtentDirection)
    ext_input.participantBodies = participants
    return extrudes.add(ext_input)


def kreiskanten(body, durchmesser_mm, achse='z', lage_mm=0.0, tol_mm=0.05):
    """Sucht Kreis- und Bogenkanten nach Durchmesser und Lage.

    Bewusst geometrisch gesucht statt ueber gemerkte Indizes: die Kanten
    entstehen erst beim Bau, und ihre Reihenfolge im BRep ist nichts, worauf
    man sich verlassen sollte. Durchmesser plus Achslage sind dagegen genau
    das, was wir beim Konstruieren selbst vorgegeben haben.

    achse    Koordinate, in der die Kante liegt ('x', 'y' oder 'z')
    lage_mm  Wert dieser Koordinate (z. B. 0.0 fuer die Unterseite)
    """
    treffer = []
    r_soll = durchmesser_mm / 2.0 * MM
    lage_soll = lage_mm * MM
    tol = tol_mm * MM

    for kante in body.edges:
        geo = kante.geometry
        kreis = adsk.core.Circle3D.cast(geo)
        bogen = adsk.core.Arc3D.cast(geo)
        if kreis:
            radius, mitte = kreis.radius, kreis.center
        elif bogen:
            radius, mitte = bogen.radius, bogen.center
        else:
            continue

        wert = {'x': mitte.x, 'y': mitte.y, 'z': mitte.z}[achse]
        if abs(radius - r_soll) <= tol and abs(wert - lage_soll) <= tol:
            treffer.append(kante)

    return treffer


def verrunde(comp, kanten, mass_mm):
    """Konstanter Radius auf die uebergebenen Kanten."""
    fillets = comp.features.filletFeatures
    inp = fillets.createInput()
    inp.isRollingBallCorner = True
    # Keine Tangentenkette: an einer Roehre, die mit der Seitenwand
    # verschmilzt, wuerde die Verrundung sonst unkontrolliert weiterlaufen.
    inp.edgeSetInputs.addConstantRadiusEdgeSet(sammle(kanten), val(mass_mm), False)
    return fillets.add(inp)


def fase(comp, kanten, mass_mm):
    """Gleichschenklige 45-Grad-Fase auf die uebergebenen Kanten."""
    chamfers = comp.features.chamferFeatures
    inp = chamfers.createInput2()
    inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        sammle(kanten), val(mass_mm), False)
    return chamfers.add(inp)


def brich_kanten(comp, kanten, mass_mm, methode='fase'):
    """Fase oder Radius, je nach Methode. Gibt zurueck, ob es geklappt hat.

    Ein gescheitertes Fillet ist hier kein Grund, das ganze Bauteil
    fallenzulassen - der Koerper ist zu dem Zeitpunkt fertig und brauchbar,
    nur eben mit scharfer Kante. Der Aufrufer sammelt die Fehlschlaege ein
    und meldet sie gebuendelt, statt die Live-Vorschau zu unterbrechen.
    """
    if not kanten or mass_mm <= 1e-9:
        return True
    try:
        if methode == 'radius':
            verrunde(comp, kanten, mass_mm)
        else:
            fase(comp, kanten, mass_mm)
        return True
    except Exception:
        return False


def abziehen(comp, ziel_body, werkzeug_bodies):
    """Werkzeugkoerper vom Zielkoerper abziehen und dabei verbrauchen."""
    combines = comp.features.combineFeatures
    inp = combines.createInput(ziel_body, sammle(werkzeug_bodies))
    inp.operation = adsk.fusion.FeatureOperations.CutFeatureOperation
    inp.isKeepToolBodies = False
    inp.isNewComponent = False
    return combines.add(inp)


def vereinen(comp, ziel_body, werkzeug_bodies):
    combines = comp.features.combineFeatures
    inp = combines.createInput(ziel_body, sammle(werkzeug_bodies))
    inp.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
    inp.isKeepToolBodies = False
    inp.isNewComponent = False
    return combines.add(inp)


# ---------------------------------------------------------------------------
# Dialoghelfer
# ---------------------------------------------------------------------------

def finde(inputs, ident):
    """Sucht eine Eingabe auch innerhalb von Gruppen und Reitern."""
    treffer = inputs.itemById(ident)
    if treffer:
        return treffer
    for i in range(inputs.count):
        item = inputs.item(i)
        gruppe = adsk.core.GroupCommandInput.cast(item)
        reiter = adsk.core.TabCommandInput.cast(item)
        kinder = gruppe.children if gruppe else (reiter.children if reiter else None)
        if kinder:
            treffer = finde(kinder, ident)
            if treffer:
                return treffer
    return None


def dokument_schluessel(design):
    try:
        return design.parentDocument.name
    except Exception:
        return '<aktiv>'


# ---------------------------------------------------------------------------
# Einstellungsspeicher
# ---------------------------------------------------------------------------

class Konfig(object):
    """Merkt die zuletzt benutzten Dialogwerte ueber Sitzungen hinweg.

    Liegt ausserhalb des Add-In-Ordners, damit ein Update oder Neukopieren
    des Add-Ins die Einstellungen nicht mitloescht. Fehler sind hier nie
    fatal - im Zweifel startet der Dialog eben mit den Vorgaben.
    """

    def __init__(self, app_name):
        self.app_name = app_name
        self.werte = {}

    def pfad(self):
        basis = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~')
        return os.path.join(basis, self.app_name, 'einstellungen.json')

    def laden(self):
        try:
            p = self.pfad()
            if not os.path.isfile(p):
                return
            with open(p, 'r', encoding='utf-8') as f:
                daten = json.load(f)
            if isinstance(daten, dict):
                self.werte.update(daten)
        except Exception:
            pass

    def speichern(self):
        try:
            p = self.pfad()
            ordner = os.path.dirname(p)
            if not os.path.isdir(ordner):
                os.makedirs(ordner)
            with open(p, 'w', encoding='utf-8') as f:
                json.dump(self.werte, f, indent=2, ensure_ascii=False, sort_keys=True)
        except Exception:
            pass

    def get(self, schluessel, vorgabe=None):
        return self.werte.get(schluessel, vorgabe)

    def update(self, daten):
        # Nur einfache, JSON-taugliche Werte uebernehmen.
        for k, v in daten.items():
            if isinstance(v, (str, int, float, bool)) or v is None:
                self.werte[k] = v

    def ganzzahl(self, schluessel, vorgabe, kleinster, groesster):
        """Gemerkten Wert holen und in gueltige Grenzen zwingen - eine
        kaputte Konfigdatei darf den Dialog nicht am Aufgehen hindern."""
        try:
            wert = int(self.werte.get(schluessel, vorgabe))
        except (TypeError, ValueError):
            return vorgabe
        return max(kleinster, min(groesster, wert))

    def zahl(self, schluessel, vorgabe, kleinster, groesster):
        try:
            wert = float(self.werte.get(schluessel, vorgabe))
        except (TypeError, ValueError):
            return vorgabe
        return max(kleinster, min(groesster, wert))


# ---------------------------------------------------------------------------
# Druckerkompensation
# ---------------------------------------------------------------------------

def schrumpf_faktor(profil):
    """Faktor, mit dem XY-Masse vorgehalten werden, damit sie nach dem
    Schrumpfen auf dem Nennmass landen. 0,24 % Schrumpf -> 1,0024."""
    prozent = profil.get('komp_schrumpf', 0.0)
    if abs(prozent) < 1e-9:
        return 1.0
    # Gedeckelt wie der Messwert-Pfad im Dialog. Ohne die Grenze gaebe ein
    # Profil mit komp_schrumpf=100 eine Division durch null, und ein
    # Tippfehler (2.0 statt 0.2) einen Stein, der nichts mehr klemmt. Die
    # gleiche Zahl kommt aus zwei Wegen - dann muessen auch beide dieselbe
    # Plausibilitaetsgrenze haben.
    return max(SCHRUMPF_MIN, min(SCHRUMPF_MAX, 1.0 / (1.0 - prozent / 100.0)))


def ist_kompensiert(profil):
    return (schrumpf_faktor(profil) != 1.0
            or bool(profil.get('komp_rund'))
            or bool(profil.get('komp_loch')))


# ---------------------------------------------------------------------------
# STL-Export
# ---------------------------------------------------------------------------

MESH = {
    'high': adsk.fusion.MeshRefinementSettings.MeshRefinementHigh,
    'medium': adsk.fusion.MeshRefinementSettings.MeshRefinementMedium,
    'low': adsk.fusion.MeshRefinementSettings.MeshRefinementLow,
}


def exportiere_stl(design, body, ordner, dateiname, mesh_key):
    """Exportiert einen Koerper als binaeres STL. Gibt den Pfad zurueck.
    Vorhandene Dateien werden nicht ueberschrieben, sondern durchnummeriert."""
    if not os.path.isdir(ordner):
        os.makedirs(ordner)

    pfad = os.path.join(ordner, dateiname + '.stl')
    zaehler = 2
    while os.path.exists(pfad):
        pfad = os.path.join(ordner, '{}_{}.stl'.format(dateiname, zaehler))
        zaehler += 1

    export_mgr = design.exportManager
    optionen = export_mgr.createSTLExportOptions(body, pfad)
    optionen.isBinaryFormat = True
    optionen.meshRefinement = MESH.get(mesh_key, MESH['high'])
    export_mgr.execute(optionen)

    return pfad


def saeubere_dateiname(text):
    return ''.join(c for c in text if c.isalnum() or c in ('_', '-'))
