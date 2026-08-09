# Text für den Facebook-Post

Fertig zum Kopieren, Links sind eingesetzt.

**Wichtig:** Facebook kann keine Markdown-Formatierung. Die Texte unten stehen
deshalb bewusst ohne `**Sternchen**` — die würden im Beitrag wörtlich
erscheinen. Alles zwischen den Trennlinien 1:1 übernehmen.

Die Links:

| Ziel | Adresse |
|---|---|
| Anleitung (empfohlen als Aufmacher) | https://wolfb63-del.github.io/Klemmbaustein-Generator/ |
| Direkter Download | https://github.com/wolfb63-del/Klemmbaustein-Generator/releases/latest |
| Projektseite | https://github.com/wolfb63-del/Klemmbaustein-Generator |

---

## Variante A — für den Post selbst

🧱 Klemmbaustein-Generator für Fusion — kostenlos

Ich habe ein Add-In für Autodesk Fusion gebaut, das klemmbaustein-kompatible
Teile auf Knopfdruck erzeugt. Kein Skizzieren, kein Modellieren: Typ wählen,
Größe eintippen, fertig.

✅ 11 Bauteiltypen: Stein, Halbstein, Platte, Fliese, Jumper-Platte,
Technic-Stein, Lochbalken, Schrägstein, Eckstein, Rundstein, Grundplatte
✅ 1×1 bis 32×32 Noppen, frei kombinierbar
✅ Echte Röhren an der Unterseite (bei 1×N Stege, wie beim Original)
✅ Live-Vorschau während der Eingabe
✅ Kanten brechen: Fase oder Radius, getrennt für Einführkante, Noppen und
Außenkanten — macht das Zusammenstecken spürbar leichter
✅ Druckerkalibrierung: du misst deinen Teststein, das Add-In rechnet
✅ Druckprofile für PETG, PLA, Resin — plus Regler für die Klemmkraft
✅ STL-Export direkt beim Erzeugen, mit sprechendem Dateinamen
✅ Serienmodus: legt die Steine automatisch nebeneinander ab

Das Ganze läuft mit der kostenlosen Fusion-Hobbylizenz, Python muss man nicht
installieren.

Das Beste ist der Klemmspiel-Regler. Halten eure Steine nicht? Wert um 0,05
hoch, neu drucken. Sitzen sie bockfest? Runter damit. Der Dialog rechnet live
mit und sagt euch, wie viel Luft am Klemmkontakt bleibt — bevor ihr druckt.

Dazu gibt es eine bebilderte Anleitung mit einer Kalibrier-Runde: einmal einen
4×2 drucken, nachmessen, zwei Zahlen eintragen — danach passt es dauerhaft für
euren Drucker. Die Zeichnungen darin sind direkt aus den Konstruktionsdaten
erzeugt, stimmen also immer mit dem überein, was rauskommt.

📖 Anleitung ansehen: https://wolfb63-del.github.io/Klemmbaustein-Generator/
📥 Direkt herunterladen: https://github.com/wolfb63-del/Klemmbaustein-Generator/releases/latest

Rückmeldungen und eure kalibrierten Druckerprofile nehme ich gern auf — je mehr
Profile zusammenkommen, desto besser für alle. 🙂

Unabhängiges, kostenloses Privatprojekt ohne jede Verbindung zur LEGO Gruppe.
LEGO® ist eine eingetragene Marke der LEGO Gruppe, die dieses Projekt weder
sponsert noch autorisiert. Alle Maße stammen aus frei verfügbaren Nennmaßen des
patentfreien Klemmbaustein-Rasters.

---

## Variante B — sehr kurz (Kommentar / Gruppen mit Zeichenlimit)

🧱 Kostenloses Fusion-Add-In: erzeugt Klemmbausteine in 11 Bauteiltypen von
1×1 bis 32×32 auf Knopfdruck — mit Live-Vorschau, Kantenbrechung,
Druckerkalibrierung, Klemmkraft-Regler und STL-Export. Läuft mit der
Gratis-Hobbylizenz.
📖 https://wolfb63-del.github.io/Klemmbaustein-Generator/

---

## Markenrechtliche Leitplanken für den Post

Halte dich an diese fünf Punkte, dann gibt es weder mit LEGO noch mit den
Gruppenmoderatoren Ärger:

1. **Titel und Überschrift markenfrei.** „Klemmbaustein-Generator", nie
   „LEGO-Generator". Das gilt auch für Dateinamen, Ordnernamen und den
   Download-Link.
2. **LEGO® höchstens einmal**, im Disclaimer am Ende, immer mit ® — nie als
   Aufmacher oder Verkaufsargument.
3. **Kein Logo, keine LEGO-Schrifttype, keine Minifiguren** in Bildern oder
   Grafiken. Auch keine Fotos, auf denen deine Teile in Original-Sets verbaut
   sind — zeig nur deine eigenen Drucke.
4. **Kein Geld, keine Spendenlinks, keine Werbung.** Markenrecht greift nur im
   geschäftlichen Verkehr. Sobald ein „Kauf mir einen Kaffee"-Link dranhängt,
   verlierst du dieses Argument.
5. **Gruppenregeln vorher lesen.** Viele Klemmbaustein-Gruppen verbieten
   „LEGO" im Beitragstitel von sich aus.

## Checkliste vor dem Hochladen

- [ ] ZIP enthält: `Klemmbaustein.py`, `Klemmbaustein.manifest`, `resources\`, `ANLEITUNG.md`
- [ ] ZIP enthält **nicht**: `__pycache__\`, `.env` (persönlicher Pfad, nutzlos für andere), `FACEBOOK-POST.md`
- [ ] Oberster Ordner im ZIP heißt exakt `Klemmbaustein` — sonst findet Fusion das Add-In nicht
- [ ] Download-Link testen (Facebook erlaubt keine ZIP-Uploads direkt — Google Drive, Dropbox, MakerWorld, Printables oder GitHub verwenden)
- [ ] Link auf "Jeder mit dem Link" freigeben, nicht nur für dich
- [ ] 2–3 Fotos gedruckter Steine anhängen — Posts mit Bild laufen deutlich besser
- [ ] Optional: kurzer Screencast des Dialogs (Live-Vorschau macht sich im Video gut)
- [ ] In Gruppenregeln prüfen, ob Eigenwerbung / Links erlaubt sind
