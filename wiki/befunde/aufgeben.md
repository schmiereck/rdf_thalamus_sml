---
type: Befund
title: Aufgeben aus eigener Erfahrung - in dieser Form schaedlich
description: Ein Aufgeben-Kopf schaetzt alle 50 Schritte aus acht Einzelaspekten, ob die Episode noch gelingt, gelernt aus dem Kamera-Selbst-Urteil am Episodenende (aufgegebene Episoden lernen nicht mit). Gepaartes A/B im GUI-Aufbau (selbst loslassen), 3 Seeds x 75 - ohne 52,3 %, mit 45,9 % (Differenz -6,3 [-15,6, +3,0], Seeds 0:3), nur 3,9 % Schritte gespart. Mal zu vorsichtig (3-4 Abbrueche je Seed, treffsicher), mal zu forsch (26 Abbrueche, 7 davon im Vergleichsarm geliefert). Vorgabe aus.
tags: [act23, episodenende, aufgeben, aspekte, negativ, ab]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5.5, at: 2026-10-06T00:00:00Z }
sources:
  - id: code
    resource: "e915d15 (AufgebenKopf, ACT23_AUFGEBEN, run_combined._aufgeben)"
    title: Umbau
  - id: lauf
    resource: "Kopflos, Zustand c2_state (7a3f7a2d + 36 Episoden Loslass-Sammeln), ACT23_NO_PERSIST=1, beide Arme im GUI-Aufbau (ACT16_ABLAGE_FIX=1 ACT23_LOSLASS_KOPF=1 ACT23_LOSLASS_SELBST=1 ACT16_ENDE_HALTEN=30), Seeds 9091-9093 je 75 Ep (9094 wegen Speichermangels abgebrochen), Arm A1 ACT23_AUFGEBEN=1"
    title: A/B 2026-10-06
---

# Frage

Nach [Loslassen](/befunde/loslassen.md) enden erfolgreiche Episoden durch ein eigenes Ereignis.
Gescheiterte liefen bis zum Zeitbudget - gut ein Drittel aller Episoden, je ~900 Schritte. Kann
der Agent aus eigener Erfahrung lernen, wann Weitermachen nichts mehr bringt?
([Aspekt-Rueckmeldung](/fragen/aspekt-rueckmeldung.md), naechster Aspekt nach dem Loslassen.)

# Gebaut

`AufgebenKopf`: alle 50 Schritte eine Momentaufnahme aus acht Aspekten (Schritte, haelt etwas,
Hand-Ziel, Hand-Objekt, Objekt-Ziel, Handhoehe, Fingerdruck, Klaue); nach der Episode bekommen
alle das Selbst-Urteil der Kamera. Aufgeben ab 300 Schritten, wenn zweimal in Folge unter 5 %
Erfolg erwartet wird. **Keine Selbstbestaetigung:** aufgegebene Episoden lernen nicht mit.

# Ergebnis

| Seed | ohne | mit | aufgegeben (davon im Vergleichsarm geliefert) |
|---|---|---|---|
| 9091 | 43/75 | 37/75 | 4 (0) |
| 9092 | 38/72 | 33/72 | 3 (0) |
| 9093 | 35/75 | 32/75 | 26 (7) |
| **gesamt** | **52,3 %** | **45,9 %** | **33 (7)** |

* Differenz -6,3 Punkte, 95 %-Intervall [-15,6, +3,0] - ein Schaden ueber 10 Punkte ist NICHT
  ausgeschlossen; Seeds 0:3.
* Schritte gesamt 171 150 gegen 164 530 (-3,9 %); Budget-Enden 107 gegen 82.
* Die Arme sind bis zum ersten Aufgeben bitgleich (9091: Ep 13, 9092: Ep 41); danach laufen sie
  durch unterschiedliches Weiterlernen auseinander.

# Lesart

**Ehrliches Negativ.** Der Kopf ist in zwei Seeds zu vorsichtig, um Zeit zu sparen (3-4
Abbrueche, aber treffsicher), im dritten zu forsch (26 Abbrueche, mehr als jeder vierte haette
noch geliefert). Dieselbe Lehre wie beim ersten Erfolgsnetz fuers Loslassen: ein Netz, das allein
aus Ergebnissen eine Schwelle zieht, ist ausserhalb dessen, was es gesehen hat, nicht kalibriert
- es braucht einen Vorschlag oder ein Unsicherheitsmass, an dem es sich festhalten kann.
Zusaetzlich verschiebt jeder Abbruch das Weiterlernen, und das kostete hier in allen drei Seeds.

`ACT23_AUFGEBEN` bleibt aus. Das Zeitbudget bleibt das Ende gescheiterter Episoden.

# Was ein naechster Versuch braeuchte (nicht gebaut)

* Ein Vorschlag, den das Netz nur bestaetigen kann (z. B. "seit N Schritten kein Fortschritt"),
  statt freier Schwelle - wie beim Loslassen das Veto.
* Ein Unsicherheitsmass (Ensemble), damit unbekannte Lagen nicht als aussichtslos gelten.

# Verwandt

* [Loslassen am Ziel](/befunde/loslassen.md)
* [Das Episodenende entscheidet der Agent selbst](/befunde/episodenende-selbst.md)
* [Aspekt-Rueckmeldung](/fragen/aspekt-rueckmeldung.md)
