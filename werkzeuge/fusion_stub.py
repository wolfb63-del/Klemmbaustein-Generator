# -*- coding: utf-8 -*-
"""Minimaler Ersatz fuer die Fusion-API.

Klemmbaustein.py importiert adsk.core und adsk.fusion beim Laden. Wer die
Rechenlogik ausserhalb von Fusion benutzen will - fuer die Pruefungen oder
zum Bauen der Anleitung -, braucht diese Module also, ohne dass Fusion
laeuft. Mehr als der Import verlangt, muss der Ersatz nicht koennen.

Frueher stand dieselbe Funktion in test_logik.py und anleitung_bauen.py.
Braucht Klemmbaustein.py kuenftig ein weiteres adsk-Objekt, faellt das sonst
nur an einer der beiden Stellen auf - das andere Skript bricht dann bei
naechster Gelegenheit mit einem Fehler ab, der nach einem echten Defekt
aussieht.
"""

import sys
import types


def stub_adsk():
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

    adsk.core = core
    adsk.fusion = fusion
    sys.modules['adsk'] = adsk
    sys.modules['adsk.core'] = core
    sys.modules['adsk.fusion'] = fusion
