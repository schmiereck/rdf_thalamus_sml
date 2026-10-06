---
type: Befund
title: Zufassen aus dem eigenen Ergebnis - die Schliess-Entscheidung ist nicht der Engpass
description: Jeder Greifversuch protokolliert mit sieben Einzelaspekten aus der letzten Pose mit offener Klaue, Etikett aus dem eigenen Tastsinn (traegt beim Anheben). 76 Versuche in 80 Episoden - 84 % halten, und die Aspekte trennen gehaltene von misslungenen nicht (zeitlich gehaltene Pruefung AUC 0,27-0,56, kein Einzelaspekt ueber 0,64). Bestaetigt den Glaubensfehler-Befund mit eigenem Etikett. Die groessere Luecke liegt danach - 11 Episoden verlieren das Objekt beim Tragen, die Klaue bleibt zu, der Arm faehrt leer weiter. Kein Veto gebaut.
tags: [act23, greifen, aspekte, tastsinn, selbst-urteil, negativ]
status: stable
evidenz: einzelmessung
ebene: act23-ab
generated: { by: claude/opus-5.5, at: 2026-10-06T00:00:00Z }
sources:
  - id: code
    resource: "5b5e14d + Folgecommit (ACT23_GRIFF_SELBST, arm_modules/griff_kopf.py, Versuchsverfolgung in _policy_mit_kopf)"
    title: Protokoll
  - id: lauf
    resource: "Kopflos, Zustand c2_state (7a3f7a2d + 36 Episoden Loslass-Sammeln), ACT23_NO_PERSIST=1, GUI-Aufbau (ACT16_ABLAGE_FIX=1 ACT23_LOSLASS_KOPF=1 ACT23_LOSLASS_SELBST=1 ACT16_ENDE_HALTEN=30), Seed 9101, 80 Episoden, ACT23_GRIFF_SELBST=1"
    title: Sammellauf 2026-10-06
---

# Frage

Nach dem [Loslassen](/befunde/loslassen.md) die Gegenseite der [Aspekt-Rueckmeldung](/fragen/aspekt-rueckmeldung.md):
kann der Agent aus dem eigenen Ergebnis lernen, **wann Zufassen gelingt** - und ein Veto gegen
aussichtslose Griffe einlegen?

# Gebaut (nur Stufe 1: protokollieren)

`ACT23_GRIFF_SELBST=1` verfolgt jeden Greifversuch im Netzbetrieb:

* **Beginn:** die Klaue schliesst tatsaechlich (war > 0,45, jetzt < 0,27), Hand < 30 mm seitlich
  vom Objektglauben.
* **Momentaufnahme:** die letzte Pose mit noch ganz offener Klaue. Zwei verworfene Fassungen im
  Rauchtest: (1) beim ersten "zu"-Befehl - der flackert im Anflug, Aufnahme 59-80 mm ueber dem
  Greifpunkt; (2) beim Unterschreiten von 0,27 - da war schon Druck da und der Objektglaube auf die
  Hand gesprungen (seitlich 0,0 mm): das Ergebnis leckte in die Aspekte.
* **Aspekte:** seitlich Hand-Glaube, Hand ueber Greifpunkt, Klaue, Fingerdruck, Kurzachse und Hoehe
  (beide geschaetzt), Versuchsnummer.
* **Etikett (eigener Tastsinn):** gehalten = Druck > 0,3 N bei geschlossener Klaue und Hand ueber
  40 mm; misslungen = die Klaue geht wieder auf oder die Episode endet vorher.

# Ergebnis

76 Versuche in 80 Episoden, **64 gehalten (84 %)**.

| Aspekt | gehalten (Median) | misslungen (Median) | AUC einzeln |
|---|---|---|---|
| seitlich | 12,7 mm | 11,7 mm | 0,50 |
| ueber Greifpunkt | 3,6 mm | 3,9 mm | 0,56 |
| Kurzachse | 8,6 mm | 7,1 mm | 0,47 |
| Hoehe | 12,0 mm | 12,1 mm | 0,35 |
| Fingerdruck | 0 | 0 | 0,64 |

Zeitlich geteilt (erste 45 Versuche Training, letzte 31 Pruefung, darin 4 misslungen): logistisch
AUC 0,27 / 0,48, act19-MLP 0,45 / 0,56 (ohne / mit Druck und Klaue). **Ein Veto bei p < 0,5 haette
keinen der 4 Fehlgriffe verhindert.**

Wohin die 32 nicht gelieferten Episoden gehen:

| | Episoden |
|---|---|
| gehalten, danach verloren / falsch abgelegt | **16** |
| nur Fehlgriffe | 8 |
| gar kein Greifversuch am Glauben | 7 |
| nicht gefunden | 1 |

# Lesart

**Ehrliches Negativ fuer das Veto, jetzt mit eigenem Etikett.** Das bestaetigt den alten Befund
[kein Glaubensfehler](/befunde/griff-glaube-und-tastsinn.md) (damals Etikett "geliefert", hier je
Versuch aus dem Tastsinn): aus der Pose vor dem Schliessen ist nicht ablesbar, ob der Griff haelt.
Und selbst eine perfekte Vorhersage koennte hoechstens 8 von 80 Episoden betreffen. Stufe 2 (Veto)
wird **nicht gebaut**.

Einzelmessung: ein Seed, 12 Fehlgriffe. Eine schwache Trennung unter AUC 0,65 ist damit nicht
ausgeschlossen, eine brauchbare (> 0,8) schon.

# Der Nebenfund: Verlieren beim Tragen

In 11 der 16 "gehalten, nicht geliefert"-Episoden endet die Episode mit Stillstand: das Objekt war
oben (Druck max 0,7-8 N), dann faellt der Druck auf 0 - **bei 58-80 mm Hoehe, also unterwegs** -,
die Klaue bleibt zu (max 0,11-0,26), und der Arm faehrt 260-600 Schritte leer weiter, bis die
Episode steht. Der Agent merkt den Verlust nicht, obwohl sein Tastsinn ihn meldet.

Ein Hinweis auf die Ursache: der mittlere Druck beim Anheben (`[Griffdruck] heben`) liegt in 10 von
17 Episoden mit langer druckloser Strecke oben unter 0,6 N, in den 41 sauber gelieferten nie (min
1,3 N). Vorbehalt: 12 gelieferte Episoden zeigen beim Tragen 0 N - "kein Druck" heisst nicht sicher
"verloren". Grob aus den Protokollzeilen gezaehlt, nicht sauber getrennt.

Das ist ein Kandidat fuer den naechsten Aspekt-Kopf ("haelt der Griff noch?" -> absetzen und neu
greifen), mit dem Muster vom Loslassen: ein Vorschlag aus dem Tastsinn, den ein Erfolgsnetz nur
bestaetigen oder verwerfen kann. **Nicht gebaut, nicht gemessen.**

# Verwandt

* [Kein Glaubensfehler, Tastsinn traegt das Schliessen nicht](/befunde/griff-glaube-und-tastsinn.md)
* [Loslassen am Ziel](/befunde/loslassen.md)
* [Aufgeben aus eigener Erfahrung](/befunde/aufgeben.md)
* [Aspekt-Rueckmeldung](/fragen/aspekt-rueckmeldung.md)
