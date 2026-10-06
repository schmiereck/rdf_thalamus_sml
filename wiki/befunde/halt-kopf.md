---
type: Befund
title: Haelt der Griff noch? - Tastsinn-Vorschlag, Veto aus eigenem Ergebnis, neu greifen
description: Kopf fuer den Aspekt "Griff verloren?" - der Tastsinn schlaegt vor (hat getragen, Klaue zu, Hand oben, 10 Schritte kein Druck), ein Erfolgsnetz aus dem Selbst-Urteil hat ein Veto, sonst Klaue auf und die Policy greift neu. Mechanik belegt (Rauchtest - Objekt verloren, neu gegriffen, 11 N, getragen). Sammellauf 100 Ep - 11 Vorschlaege, 8 echte Verluste (73 % Treffer allein aus dem Tastsinn); das Selbst-Urteil "geliefert" ist ein schwaches Etikett fuer "haelt noch" (1 von 3 Fehlalarmen geliefert, 2 von 8 Verlusten auch), das Veto-Netz waere erst nach Hunderten Episoden bereit.
tags: [act23, greifen, tragen, tastsinn, aspekte, selbst-urteil]
status: draft
evidenz: einzelmessung
ebene: act23-ab
generated: { by: claude/opus-5.5, at: 2026-10-06T00:00:00Z }
sources:
  - id: code
    resource: "0bb2c35 (HaltKopf, arm_modules/halt_kopf.py, ACT23_HALT_SELBST 1/2/3, pc_act16 run_combined._wahr_hub nur Messung)"
    title: Umbau
  - id: sammeln
    resource: "Kopflos, c2_state -> c3_state (geschrieben), GUI-Aufbau (ACT16_ABLAGE_FIX=1 ACT23_LOSLASS_KOPF=1 ACT23_LOSLASS_SELBST=1 ACT16_ENDE_HALTEN=30), Seed 9111, 100 Ep, ACT23_HALT_SELBST=2"
    title: Sammellauf 2026-10-06
---

# Frage

[Zufassen aus dem eigenen Ergebnis](/befunde/zufassen-selbst.md) fand: das Schliessen ist nicht der
Engpass, aber in 11 von 80 Episoden faellt das Objekt beim Tragen heraus, und der Arm faehrt mit
geschlossener Klaue leer weiter. Kann der Agent den Verlust aus dem Tastsinn bemerken und neu greifen?

# Gebaut

`HaltKopf` (`ACT23_HALT_SELBST`, Vorgabe 0), Muster vom [Loslassen](/befunde/loslassen.md):

* **Vorschlag (Tastsinn):** in diesem Griff schon getragen (Druck > 0,3 N, Klaue zu, Hand > 30 mm
  ueber Ruhe), jetzt Klaue zu, Hand oben, seit 10 Schritten Druck < 0,1 N. Einmal je Druckverlust.
* **Veto (gelernt):** p(Episode wird trotzdem geliefert | 8 Aspekte) aus dem Selbst-Urteil am
  Episodenende; nur Vorschlaege OHNE Eingriff werden Etikett (keine Selbstbestaetigung). Bereit ab
  20 Faellen, je Ausgang 5.
* **Eingriff:** Klaue auf, bis die Propriozeption "offen" meldet (> 0,45, hoechstens 100 Schritte),
  dann fuehrt wieder die Policy. Hoechstens 2 je Episode. Der beobachtbare Objektglaube friert beim
  Druckverlust ohnehin am Fallort ein (`run_combined._cobs`), die Policy faehrt dort neu an.
* Modi: `1` Vorschlag + Veto, `2` nur sammeln, `3` Vorschlag allein (Vergleichsarm - als
  Dauerloesung waere das eine feste Laufzeitregel, s. [Laufzeitregeln](/mechanismen/laufzeit-regeln.md)).
* Jeder Vorschlag protokolliert die **wahre** Objekthoehe (`[Messung: ...]`), nur zur Auswertung.

Rauchtest-Fehler: die erste Fassung hielt die Klaue fest 15 Schritte offen - sie kam von 0,07 nie
ueber 0,26, die Policy schloss wieder. Jetzt bis "offen" gefuehlt.

# Mechanik (Rauchtest, 3 Ep, Modus 3)

* Echter Verlust (Objekt 7 mm ueber Ruhe): Klaue auf (0,54), die Policy fuhr zurueck, griff neu
  (11,4 N), trug und liess am Ziel los - 33 mm daneben, Selbst-Urteil "geliefert", Welt nicht.
* Fehlalarm (Objekt noch 48 mm oben, Druck 0 trotz Halt): der Eingriff liess es fallen. Genau dafuer
  ist das Veto da.
* Der Klauenwinkel trennt die Faelle NICHT: 0,07 in beiden.

# Sammellauf (100 Ep, kein Eingriff)

| | Anzahl |
|---|---|
| Vorschlaege | 11 (in 11 Episoden) |
| davon wirklich verloren | **8** |
| davon haelt noch (Fehlalarm) | 3 |

* Episoden mit Vorschlag liefern 3/11, ohne 62/89.
* Das Selbst-Urteil als Etikett fuer "haelt noch": Fehlalarme 1 von 3 geliefert, echte Verluste
  2 von 8 geliefert. **Schwaches Etikett** - "geliefert" mischt "haelt noch" mit "falsch
  abgelegt" und "selbst wieder aufgenommen".
* Kein Einzelaspekt trennt Verlust von Fehlalarm (Klaue 0,50, Handhoehe 0,52, Druck vorher 0,33).
* Das Veto-Netz hat nach 100 Episoden 10 Faelle, davon 2 "geliefert" - **nicht bereit**. Bei dieser
  Rate braucht es grob 250 Episoden bis zur Bereitschaft.

# Lesart (vorlaeufig)

Der Tastsinn allein trifft 73 % - als Vorschlag brauchbar. Die Decke ist aber klein: ~8 echte
Verluste je 100 Episoden. Ob neu greifen sie rettet, sollte ein A/B (Modus 2 gegen 3, Seed 9112) messen - es wurde nach 13 Episoden je Arm wegen Speichermangels beendet (je 7/13 geliefert, ohne Aussage).
Offen bleibt ein besseres eigenes Etikett als "geliefert", z. B. ob die Kamera das Objekt beim
Loslassen unter der Hand sieht (`SelfEval`: "Objekt nicht am Loslass-Punkt gesehen").

# Verwandt

* [Zufassen aus dem eigenen Ergebnis](/befunde/zufassen-selbst.md)
* [Loslassen am Ziel](/befunde/loslassen.md)
* [Aspekt-Rueckmeldung](/fragen/aspekt-rueckmeldung.md)
