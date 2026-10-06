---
type: Frage
title: Rueckmeldung je Aspekt statt Urteil ueber die ganze Situation
description: Nutzeridee 2026-10-05 - ein Teacher (oder ein Selbst-Urteil) bewertet nicht die ganze Situation, sondern einzelne Aspekte ("Finger A +27 %", "Arm zeigt zum Objekt +96 %"), wie der Drucksensor es fuer den Griff schon tut. Eigene Netze lernen diese Aspekte zu erkennen, auch aus dem Kamera-/Fovea-Bild; das Situationsverstaendnis setzt sich daraus zusammen. Erster Beleg - der Loslass-Kopf aus fuenf Einzelaspekten trennt, wo die ganzheitliche Policy scheitert, und machte dabei einen Teacher-Fehler sichtbar.
tags: [act23, idee, nutzeridee, kredit, selbst-urteil, architektur]
status: stable
evidenz: einzelmessung
ebene: pruefstand
generated: { by: claude/opus-5.5, at: 2026-10-05T00:00:00Z }
---

# Die Idee (Nutzer, 2026-10-05, sinngemaess)

Ein Teacher muss nicht eine ganze Situation belohnen oder bestrafen. Wie das Feedback des
Drucksensors koennte er nur **einzelne Aspekte** bewerten - "Finger A +27 %", "Finger B -10 %",
"Arm zeigt in Richtung Objekt +96 %". Das liesse sich mit einem **Selbst-Urteil aus dem Kamera-
bzw. Fovea-Bild** verknuepfen: eines oder mehrere Netze lernen, diese Aspekte zu erkennen, und
das **Situationsverstaendnis setzt sich aus solchen Einzelaspekten zusammen**.

# Was es dazu im Projekt schon gibt

* **Kredit-Routing** (`run_combined`, Checkpoints): das Ergebnis einer Episode geht an den Lerner,
  dessen Vorhersage brach - nie angekommen -> Policy, geschlossen ohne Hub -> Welt-Modell,
  gehalten aber daneben -> Ablage. Das ist Aspekt-Kredit auf Episodenebene.
* **Fingerdruck** (`[Griffdruck]` zufassen/heben/tragen/loesen) - ein Aspekt-Signal je Phase.
* **Selbst-Urteil** (`SelfEval`) - beurteilt nur "geliefert?", also die ganze Situation.
* Die `[Ablage]`-Zeile misst schon Aspekte (Hoehe beim Oeffnen, seitlich vom Ziel, Drift) -
  bisher nur fuer den Beobachter, nicht als Lernsignal.

# Erster Beleg: das Loslassen

Die gemeinsame Policy lernt Zielpunkt und Greiferwinkel in EINEM Netz und laesst am Ziel nicht
los ([Loslassen](/befunde/loslassen.md)). Ein eigener Kopf fuer den einen Aspekt "jetzt
loslassen?", zeitlich gehaltener Pruefsatz:

| Kopf | oeffnet am Ziel | oeffnet > 5 cm vom Ziel |
|---|---|---|
| ganzer Zustand (15 Werte) | 35 % | 22 % |
| **5 Einzelaspekte** (Hand-Ziel, Hoehe ueber Ablage, Druck, Klaue, Objekt-Ziel) | **99 %** | **0 %** |
| (gemeinsame Policy) | 3-14 % | 0 % |

Und die Aspekt-Sicht hat einen **Teacher-Fehler** sichtbar gemacht: in der Aspekt-Region "Hand am
Ziel, unten, haelt" standen 240 widerspruechliche Etiketten - der Teacher hielt ein aufgesetztes
Objekt fuer "nicht gegriffen" (`ACT16_ABLAGE_FIX`). Im ganzen Zustand war das unsichtbar.

# Offene Schritte

1. ~~Aspekt-Etiketten aus eigener Wahrnehmung~~ **gebaut fuer das Loslassen** (2026-10-06,
   [Loslassen](/befunde/loslassen.md)): Pose beim Loslassen -> Selbst-Urteil der Kamera; als Veto
   83 statt 72 % gelungenes Loslassen. Lehre: ein Erfolgsnetz allein raet in unbekannten Posen
   optimistisch -- es braucht einen Vorschlag (oder Unsicherheit), den es verwerfen kann.
   Fuer das Zufassen gemessen ([Zufassen selbst](/befunde/zufassen-selbst.md)): die Aspekte vor
   dem Schliessen trennen nicht, 84 % der Griffe halten ohnehin - kein Hebel. Der naechste
   Kandidat ist "haelt der Griff noch?" beim Tragen (11/80 Episoden verlieren unbemerkt) -
   gebaut: [Haelt der Griff noch?](/befunde/halt-kopf.md).
2. **Weitere Aspekt-Koepfe** fuer andere scharfe Entscheidungen (Schliessen; aufgeben). Aufgeben
   frei aus Ergebnissen ist gemessen schaedlich ([Aufgeben](/befunde/aufgeben.md)) - auch dort
   fehlte ein Vorschlag, den das Netz nur bestaetigen kann.
3. **Aspekt-Erkenner aus dem Fovea-Bild** ("Objekt zwischen den Backen", "Objekt kippt") als
   Eingaenge fuer diese Koepfe - die Bruecke zur Wahrnehmung.

# Verwandt

* [Loslassen](/befunde/loslassen.md)
* [Das Episodenende entscheidet der Agent selbst](/befunde/episodenende-selbst.md)
* [Kredit und Selbst-Urteil](/mechanismen/kredit-und-selbsturteil.md)
