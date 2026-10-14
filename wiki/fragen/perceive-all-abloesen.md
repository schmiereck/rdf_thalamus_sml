---
type: Frage
title: perceive_all abloesen - Bestandsaufnahme
description: Was perceive_all heute rechnet, wer welche Ausgabe verbraucht und welche Teile privilegiert, gerechnet oder schon gelernt sind. Ergebnis - acht gerechnete Stufen, zwei davon mit Privileg (Homographie aus bekannten Wuerfelorten, Arm beim Rendern ausgeblendet); jeder der 22 act23-Aufrufe braucht den Ort, 13 Farbe und Flaeche. Vorschlag fuer die Reihenfolge, mit dem Ort ueber die eigene Hand als erstem Schritt. Noch nichts gebaut, nichts gemessen.
tags: [act23, wahrnehmung, geruest, perceive_all, ziel]
status: draft
evidenz: vermutung
ebene: code
generated: { by: claude/opus-5, at: 2026-10-14T00:00:00Z }
sources:
  - id: code
    resource: src/pc_cvnn/arm_modules/shape_classifier.py:1019 (perceive_all), :339 (calibrate), :318 (_render_u8), :390 (_mask), :402 (_harmonics_at)
    title: perceive_all und Hilfsfunktionen, Stand 09d3e2f
  - id: fovea
    resource: src/pc_cvnn/pc_act18.py:782 (setup_following_fovea, zweite Homographie)
    title: Fovea-Kalibrierung
  - id: auftrag
    resource: "Nutzerauftrag 2026-10-14: 'Ja, mach die Bestandsaufnahme fuer perceive_all.'"
    title: Auftrag
---

# Frage

Nach [Ziel](/ziel.md) soll alles durch ein lernendes Netz laufen, und `perceive_all` gilt als
Uebergangsgeruest. Die Frage hier ist nur, **was abzuloesen ist und in welcher Reihenfolge**.
Ob es sich lohnt, ist keine Lieferfrage: die [Fovea-Linie](/mechanismen/fovea-und-blick.md) hat
gemessen, dass die Wahrnehmung nie der Lieferengpass war. **Erfolg heisst daher: gleiche
Lieferquote mit weniger Geruest**, nicht eine hoehere Quote.

Diese Seite ist eine Bestandsaufnahme am Code (Stand 09d3e2f). Gebaut und gemessen ist nichts.

# Was perceive_all rechnet

Ein Aufruf liefert eine Liste von Detektionen, eine je Objekt. Die Stufen der Reihe nach:

| # | Stufe | Verfahren | Art |
|---|---|---|---|
| 0 | Bild | Uebersichtskamera, **Arm ausgeblendet** (`geomgroup[1]=0`), Zielscheiben vorher **weggeparkt** (`mocap_pos`) | **privilegiert**: das kann eine echte Kamera nicht |
| 1 | Maske | Saettigung > `SAT_TH = 0,15`, farbunabhaengig | feste Schwelle |
| 2 | Einzelobjekte | Zusammenhangskomponenten; Erosions-Split (Vorgabe an) und Chroma-Split (aus, fuer Stapeln an) fuer verschmolzene Flecken | gerechnet |
| 3 | Ort `pos` | Pixelschwerpunkt ueber die Tisch-**Homographie** in Weltkoordinaten | gerechnet; **H wird kalibriert, indem der rote Wuerfel an 40 bekannten Weltorten aufgestellt wird** (privilegiert) |
| 4 | Form `desc` | komplexe Winkelharmonische auf Ringen, Betrag rotationsinvariant | fest gerechnetes Merkmal |
| 4a | Formklasse `shape`, `prob` | MLP-Kopf, offene Klassen ueber Prototypen, Neuheit, Geburt | **gelernt** |
| 5 | Lage `yaw`, `yaw4` | Phase der 2. und 4. Harmonischen | gerechnet |
| 6 | Groesse `dicke`, `span`, `area` | Distanztransformation (90-%-Perzentil), 95-%-Spanne, Pixelzahl | gerechnet |
| 7 | Farbe `chroma`, `cspread` | mittlere Chromatizitaet und Streuung im Fleck | gerechnet; die Farbklassen darauf (`ColourOpenSet`) sind **gelernt** |
| 8 | Greifpunkt `grasp_xy`, `grasp_dense`, `grasp_cands` | naechstes Material zum Schwerpunkt, dichtester Punkt, bis 6 dicke Punkte | Heuristik |

Gelernt ist also nur, was **auf** den Detektionen sitzt: Formklassen, Farbklassen und
nachgelagert Groessen- und Hoehenschaetzer. Wo ein Objekt ist, was zu ihm gehoert und wie es
liegt, ist gerechnet.

**Es gibt zwei Homographien.** Die Fovea kalibriert in `setup_following_fovea` (pc_act18.py:782)
eine eigene, auf dieselbe Weise und ebenfalls mit ausgeblendetem Arm. `shape_clf.H` wird im
Zustand mitgespeichert, die Fovea-Homographie wird bei jedem Start neu gefittet.

# Wer was verbraucht

22 Aufrufe in pc_act23.py, 2 in shape_classifier.py, 15 in Pruef- und Sondenskripten. Dazu
kommen die Geschwister `perceive_colour` (14 act23-Stellen) und `colour_parts_all` mit derselben
Maske und derselben Homographie. Die act23-Aufrufe nach Aufgabe:

| Aufgabe | Aufrufer (pc_act23.py) | gebrauchte Felder |
|---|---|---|
| **Greifen: Ort und Anfahrt** | `perceive` :6509, `make_shape_track` :6608 (je Bild in der Anfahrt), `situation_feats` :4469 | pos, grasp_xy, px, prob, shape, chroma, yaw/yaw4, desc, grasp_cands, wpx |
| **Adressieren und Aneignen** (Eigenschafts-Kommando, Farbbindung, namenlose Koerper) | `finde_nach_eigenschaften` :1685, `_auto_eig_umschreiben` :3539, `_ziel_adresse_wuerfeln` :3940, `_farbbindung_neu` :4051, `_farbe_wuerfeln` :4209/:4301/:4364, `_namenlose_kandidaten` :5671, `_eig_nachfuehren` :5720, `_streuung` :5774, `open_set_glance` :6009, `_objekt_merken`/`_objekt_sehen` :6924/:6944 | pos, chroma, area, desc, shape, dicke, span, cspread |
| **Groesse und Hoehe** | `_groesse` :2951, `_groesse_sammeln` :3013, `_stapel_paar` :6267 | pos, area, span |
| **Selbst-Urteil** (haelt, geliefert, Ablage) | `_halt_flecken` :7810, `_ph` :8154, `run_one` :8433 | pos, area, chroma, px, wpx |

**Jeder der 22 Aufrufe braucht `pos`**, 13 brauchen `chroma` und `area`, 7 `desc`. Der Ort ist
damit die Stelle, an der jeder Ersatz zuerst passen muss.

# Bekannte Bruchstellen

* Die Homographie gilt nur fuer die **Tischebene**. Gehobene oder gestapelte Koerper liegen
  daneben ([16 mm am Stapel](/befunde/stapeln-bricht-die-tischebene.md)), der Fovea-Servo hat
  deshalb ein Greifer-offen-Tor.
* Die Homographie haengt an der Bildbreite (`needs_recal`, Falle vom 2026-08-02).
* Verschmelzung naher Koerper unter ~75 mm, drei Reparaturen
  ([Wahrnehmungs-Splits](/mechanismen/wahrnehmungs-splits.md)); die Formklasse ueberlebt die Rettung
  schlechter als der Ort.
* Wer `perceive_all` ruft, muss die Zielscheiben zuruecksetzen ([Invarianten](/mechanismen/invarianten.md)).
* Das Ausblenden des Arms verschont die Maske vor einem Problem, das eine echte Kamera haette:
  ein gegriffener Koerper wuerde mit der Klaue zu einem Fleck verschmelzen. Wie gross das wird,
  ist ungemessen.

# Was schon an Lernendem da ist

* **HexFovea** (komplexes PC-Netz): findet, haelt und verfolgt ein Objekt ueber die
  Farbidentitaet, Drift 8,5 px; liest die Lage auf ihren Zellen (`fovea_cell_yaw`) so gut wie die
  PCA. Ihre Weltkoordinaten kommen aber aus der eigenen Homographie.
* **Formkopf und offene Klassen** auf dem Deskriptor, **Farb-Open-Set** auf der Chromatizitaet.
* **GroessenSchaetzer** und **HoehenSchaetzer**: lernen aus Flaeche, Dicke und Ort, der
  Hoehenschaetzer seine Etiketten aus der Beruehrung.
* **BodyModel** und gelernte IK: die Hand ist ohne Kamera bekannt. Das ist eine Etikettenquelle
  fuer den Ort, die kein Privileg braucht.
* **S1 visuelles Koerpermodell** (Codex-Linie): ein erster Verbraucher der Gelenkphasen; auf
  neuen Posen noch 28 % schlechter als das Mittelbild ([Befund](/befunde/s1-visuelles-koerpermodell.md)).
* Vorhandener Plan fuer die Fovea: [F0-F3](/fragen/dream-rsi-fovea.md), Auslesekoepfe auf
  eingeschwungenen Netzzustaenden.

# Vorschlag: Reihenfolge

Nach Hebel fuer das Ziel und nach Risiko. Jeder Schritt ist ein Schalter, der eine Stufe ersetzt,
und endet in einem act23-A/B; ein Pruefstandsergebnis allein zaehlt nicht
([Pruefstandsfalle](/mechanismen/pruefstandsfalle.md)).

1. **Ort ueber die eigene Hand lernen statt ueber kalibrierte Wuerfelorte.** Die Etiketten kommen
   aus dem Koerpermodell: wo die Hand im Bild erscheint, ist sie laut eigener Kinematik. Ersetzt
   Stufe 3 (`_px_to_world` ist eine Funktion, 13 act23-Stellen) und beseitigt das
   Kalibrierprivileg. Kann ueber die Hoehe der Hand auch die Tischebenen-Grenze angehen. Messbar
   in Millimetern gegen die heutige Homographie, nach Szene geteilt. **Voraussetzung:** die Hand
   muss dafuer im Bild sichtbar sein, waehrend das Wahrnehmungsbild sie heute ausblendet.
2. **Maske aus dem Vorhersagefehler.** Objekt ist, was ein gelerntes Modell des leeren Tisches
   nicht vorhersagt - die PC-eigene Lesart statt `SAT_TH`. Erster Schritt dahin, den Arm im Bild
   zu lassen; das lernende Modell muss ihn dann selbst erklaeren (ueber die eigene Bewegung).
3. **Lage aus den Fovea-Zellen** statt aus der Harmonischen-Phase. Klein, Werkzeug existiert,
   gemessen gleich gut. Erst nach Schritt 1 sinnvoll, weil die Zellen ueber die Homographie in
   Welt umgerechnet werden.
4. **Einzelobjekte (Segmentierung) ueber die Fovea**: ein Objekt ist, worauf der Blick einrastet
   und was sich zusammen bewegt. Der laengste Weg; er beruehrt alle Aneignungs-Aufrufer.
5. **Greifpunkt-Heuristiken** zuletzt. Die [Wertprobe](/befunde/lokaler-griff-wertprobe.md) zeigt,
   dass die Wahl des Punktes kein Hebel ist; der Ersatz waere rein architektonisch.

Groesse (Stufe 6) und Farbe (Stufe 7) bleiben vorerst: es sind Messungen auf der Maske, die mit
ihr mitwandern, und darauf sitzen schon gelernte Schaetzer.

# Offen vor dem ersten Bau

* Wie genau ist die heutige Homographie gegen die Wahrheit, getrennt nach Tischmitte, Rand und
  gehobenen Koerpern? Das ist die Messlatte fuer Schritt 1.
* Sieht die Uebersichtskamera die Hand in genug Arbeitsposen? Codex hat 238 Ansichten mit
  sichtbarer Klaue aus vier Episoden gezaehlt ([Arbeitsposen](/befunde/act23-arbeitsposen-kamera.md)).
* Soll die Fovea-Homographie mit ersetzt werden oder zuerst nur `shape_clf.H`?

# Verwandt

* [Ziel](/ziel.md), [Laufzeitregeln](/mechanismen/laufzeit-regeln.md) - perceive_all als Geruest
* [Fovea und Blick](/mechanismen/fovea-und-blick.md)
* [Wahrnehmungs-Splits](/mechanismen/wahrnehmungs-splits.md)
* [Offene Faeden](/fragen/offene-faeden-act23.md)
