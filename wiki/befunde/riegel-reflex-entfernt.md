---
type: Befund
title: Riegel und Reflex koennen zur Laufzeit weg - die Policy schliesst allein
description: Gepaartes act23-A/B, 8 Seeds x 50 - Schliess-Riegel und Greif-Reflex an 196/400, aus 196/400, 95 %-Intervall der Differenz [-7, +7] Punkte, Seeds 4:3:1. Das vorab festgelegte Kriterium (Schaden ueber 10 Punkte ausgeschlossen) ist erfuellt. Widerlegt die Riegel-Messung vom 25.08. (beide aus -8,3 Punkte) fuer den heutigen Zustand. Seit 2026-10-04 sind beide im Netzbetrieb aus, im Teacher-Betrieb bleiben sie Geruest (act21-Prinzip).
tags: [act23, schliessen, riegel, reflex, laufzeit-regeln, ab]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5.5, at: 2026-10-04T00:00:00Z }
sources:
  - id: lauf
    resource: "Kopflos, Kopie des Zustands 7a3f7a2d, ACT23_NO_PERSIST=1, Seeds 9991-9998 je 50 Ep, ACT23_SZENE_JE_EPISODE=1 ACT23_AUTO_CURIOUS=0 ACT23_EIG_DIREKT=1 ACT23_EIG_STETIG=1 ACT16_GOAL_Z=1 ACT16_GRIFF_Z=1 ACT16_RULEDIAG=1, Choreo netz, Marker-Ablage; Arm R Vorgaben, Arm O ACT16_CLOSE_GUARD=0 ACT16_REFLEX=0; je Seed parallel"
    title: A/B-Lauf 2026-10-03
  - id: code
    resource: "pc_act23.py REGELN_NETZ / _regeln_basis (Vorgabe: im Netzbetrieb aus)"
    title: Umsetzung
---

# Frage

Schritt 3 der [Laufzeitregeln](/mechanismen/laufzeit-regeln.md). Die Riegel-Messung vom
25.08. (4 Arme x 120 Episoden) hatte ergeben: beide aus -8,3 Punkte (n. s.), nur der Riegel aus
-18,3 (p = 0,006), nur der Reflex aus -14,2 - "ein gekoppeltes Paar, nicht abschalten". Die
[Offline-Analyse](/befunde/schliessen-offline.md) zeigte seither, dass die Policy den
Schliesszeitpunkt im Wesentlichen gelernt hat. Kostet das Abschalten heute noch etwas?

# Aufbau

Vorab festgelegt: Arm R (beide an) gegen Arm O (beide aus), 8 Seeds x 50, gepaart, Seed als
Einheit plus Gesamtquote; Kriterium zum Entfernen wie am 25.08.: das 95 %-Intervall schliesst
einen Schaden ueber 10 Punkte aus. Getestet wurde nur das Paar (der Einzelausbau war damals der
schaedliche Fall und ist nicht die Frage).

Paarung: alle Aufgaben gleich. Je Arm 5 Episoden "nicht gefunden" (dieselben Aufgaben, seit
`ACT23_RUECKFALL=aufgeben`) - als nicht geliefert gezaehlt.

# Ergebnis

| Seed | an | aus |
|---|---|---|
| 9991 | 25 | 29 |
| 9992 | 27 | 24 |
| 9993 | 27 | 29 |
| 9994 | 17 | 22 |
| 9995 | 24 | 25 |
| 9996 | 28 | 22 |
| 9997 | 24 | 24 |
| 9998 | 24 | 21 |
| **gesamt** | **196/400 = 49,0 %** | **196/400 = 49,0 %** |

* Differenz 0,0 Punkte, 95 %-Intervall **[-7, +7]**; McNemar 57:57 (p = 1,0); Seeds 4:3:1.
* Endabstand median 25 gegen 25 mm. Je Objekt nichts trennbar (L 21 gegen 30, roter Wuerfel 34
  gegen 28).
* Fehlerarten (Kredit-Zeile): "Griff hielt nicht" 68 gegen 68, "Griff am Objekt fehlgeschlagen"
  30 gegen 18, "verrutscht" 2 gegen 6.
* Wie oft die Regeln eingriffen (Arm R) bzw. eingegriffen haetten (Arm O), je Episode: Reflex
  54 / 60 Schritte, Riegel 273 / 253 Schritte. Der Riegel-Zaehler misst ueberwiegend Rauschen
  (j5 = 0,53 statt 0,54, s. Offline-Befund); der Reflex greift oft, aber folgenlos.
* Nebenbefund wie am 25.08.: ohne Regeln urteilt das Selbst-Urteil optimistischer ("sicher
  geliefert" 212 gegen 197 bei gleicher Quote).

# Lesart

**Die Policy schliesst allein so gut wie mit Riegel und Reflex.** Das 95 %-Intervall schliesst
einen Schaden ueber 7 Punkte aus. Der Befund vom 25.08. galt fuer den damaligen Zustand; seitdem
hat die Policy weitergelernt (12000 Selbst-Imitationszeilen), die Normierung ist repariert
([Konstante Spalte](/befunde/konstante-spalte-sprengt-policy.md)) und die Wahrnehmung besser.

Umgesetzt nach dem act21-Prinzip (`ACT21_RULES_TRAIN_ONLY`): **im Netzbetrieb sind Riegel und
Reflex aus, im Teacher-Betrieb (Choreo FSM) bleiben sie Geruest** fuer die Trainingsdaten.
`ACT23_REGELN_NETZ=1` stellt das alte Verhalten her.

# Was offen bleibt

* Das 4-mm-Band zu fruehen Schliessens (12-16 mm) und der im Policy-Zustand unsichtbare
  Stillstand bestehen weiter - sie kosten gemessen nichts Erkennbares, waeren aber die naechste
  Schaerfung (Fortschrittsmerkmal im Zustand, Teacher-Etikett "bei Stillstand schliessen").
* Die Teacher-Etiketten (`reactive_subgoal`) entscheiden weiter nach Hoehenschwelle mit
  privilegiertem `obj_h` - als Trainingsgeruest zulaessig.
* Weiter zur Laufzeit an: `SOFT_RELEASE`, `WRIST_ALIGN`, `PHASE_STALL`, `MAX_REACQ`.

# Verwandt

* [Die Schliess-Entscheidung offline](/befunde/schliessen-offline.md)
* [Laufzeitregeln](/mechanismen/laufzeit-regeln.md)
* [Griffglaube und Tastsinn](/befunde/griff-glaube-und-tastsinn.md)
