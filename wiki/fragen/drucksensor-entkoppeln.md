---
type: Frage
title: Drucksensor wieder loswerden - wo er heute fest verdrahtet ist
description: Bestandsaufnahme 2026-11-13 aus dem Lesen des Codes (Review von Google agy, Fundstellen von Claude nachgeschlagen) - der Fingerdruck war ein Test und hat sich etabliert; der Nutzer moechte ihn wieder loswerden und nicht nach NetResearch uebernehmen. Die Seite listet, wo er Pflicht ist, und Ersatzvorschlaege. Nichts davon ist gemessen, nichts wurde geaendert.
tags: [tastsinn, drucksensor, policy-zustand, aspekt-koepfe, sim-to-real, netresearch]
status: draft
evidenz: vermutung
ebene: code
generated: { by: claude/fable-5.2, at: 2026-11-13T17:00:00Z }
sources:
  - id: auftrag
    resource: "Nutzer 2026-11-13: Der Sensor kann erst einmal drin bleiben. Das war ein Test, der sich dann etabliert hat. Ich wuerde ihn allerdings gerne wieder loswerden. Ich will nur vermeiden, dass wir ihn in NetResearch uebernehmen."
  - id: review
    resource: "NetResearch/REVIEW-2026-11-13.md, Abschnitt 2 (Google agy): Drucksensor als Pflicht-Input statt als optionales Feature"
---

# Drucksensor wieder loswerden - wo er heute fest verdrahtet ist

**Stand:** Der Sensor bleibt vorerst. Diese Seite haelt nur fest, wo er heute Pflicht ist, damit ein
spaeteres Entkoppeln nicht bei null anfaengt. **Fuer NetResearch gilt: kein Druck-Eingang**, weder im
Export noch in neuen Ports.

Wer was gefunden hat: Die Liste stammt aus dem Review von agy. Claude hat jede Fundstelle im Code
nachgeschlagen; alle unten genannten stimmen. Die Folgerungen ("ohne Sensor passiert X") sind aus dem
Code gelesen, **nicht gemessen** - nach der Projektregel sagt das nichts ueber einen act23-Lauf.

## Wo der Druck heute Pflicht ist

| Stelle | Was dort steht | Folge ohne Sensor (gelesen, nicht gemessen) |
|---|---|---|
| `pc_act16.py`, Policy-Zustand | `[druck_gueltig, druck_N]` haengt an jedem Zustand (Plaetze 11, 12) | In der Simulation ist `druck_gueltig` immer 1; ein Ausfall kommt im Training nicht vor |
| `pc_act16.py`, `ACT16_OBS_STATE` (Standard an) | `_holding = press > 0.3 and Klaue zu` entscheidet, ob der Objektglaube mit der Hand mitwandert | Ohne Druck bleibt der Objektglaube beim Tragen auf dem Tisch stehen; betroffen sind die Plaetze 3-5, nicht nur 11-12 |
| `arm_modules/loslass_kopf.py` | `haelt()` und der Trainingsfilter verlangen `s[12] > 0.3` | Kopf wird nie zustaendig und nie trainiert |
| `arm_modules/fehlgriff_kopf.py` | Fingerdruck ist der erste von fuenf Aspekten | Der Kopf haengt laut [Fehlgriff-Kopf](/befunde/fehlgriff-kopf.md) im Wesentlichen an "Druck 0"; ohne Sensor droht Dauer-Fehlgriff |
| `arm_modules/aufgeben_kopf.py` | `haelt` aus `s[12] > 0.3`, Druck zusaetzlich als Merkmal | Halte-Zustand immer 0 |
| `arm_modules/halt_kopf.py`, `griff_kopf.py` | Druck, Schritte ohne Druck, hoechster Druck als Merkmale | Merkmale konstant |
| `pc_act16.py` `ENDE_SELBST`, `pc_act23.py` `ACT23_GRIPLABEL` (Standard an) | Episoden-Ende und Griff-Etikett aus dem Druck | Etiketten fehlen oder sind falsch |

Dazu passt der eigene Befund [Griff-Glaube und Tastsinn](/befunde/griff-glaube-und-tastsinn.md): Der Sensor
liefert bei manchen Griffen 0 N trotz stabilem Halt. Und die Leitlinie in
[Hoehe ertasten](/mechanismen/hoehe-ertasten.md), Kamera statt Tasten.

## Ersatzvorschlaege aus dem Review (ungeprueft)

1. **Halten ohne Druck erkennen:** aus der Kamera (bewegt sich das Objekt mit der Hand mit?) oder aus dem
   Greifer selbst (Klaue bleibt trotz Schliessbefehl offen stehen = etwas klemmt dazwischen).
2. **Ausfall ueben:** in einem Teil der Trainingszeilen `[druck_gueltig, druck_N] = [0, 0]` setzen, damit die
   Policy den Druck nur als Zusatzhinweis nutzt.
3. **Ein Halte-Signal statt vieler Schwellen:** die harten `s[12] > 0.3`-Weichen durch ein gemeinsames,
   gelerntes Signal ersetzen, das ohne Druck auskommt.

## Offen

- Reihenfolge: Die `_holding`-Weiche in `OBS_STATE` wirkt am weitesten (sie veraendert den Objektglauben)
  und waere der erste Kandidat.
- Jeder Schritt braucht einen act23-Vergleich; aus dieser Seite folgt keine Wirkungsaussage.
