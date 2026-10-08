---
type: Befund
title: Fehlgriff-Kopf - ein eigener Klassifikator loest das Schweben, aber der zweite Griff zielt auf einen noch falscheren Glauben
description: Eigener Kopf "Klaue wieder aufmachen?" nach dem Muster des Loslass-Kopfs (ACT23_FEHLGRIFF_KOPF). Offline trifft er 645/653 Fehlgriff-Zustaende bei 1 Fehlalarm in 329 und keinem in gehaltenen Zustaenden. Im act23-A/B (gepaart, 100 Aufgaben) feuert er in 22 Episoden, die Hand oeffnet und greift neu - das Schweben ist weg. Die Quote bewegt sich nicht (gehoben 69 gegen 68, p = 1,00; geliefert 55 gegen 52, p = 0,66). Ursache: die Neugriffe landen 38 mm neben dem Objekt (erster Griff 14 mm), weil der erste Griff das Objekt verschoben hat und niemand nachsieht.
tags: [act23, greifen, fehlgriff, kopf, klassifikator, objektglaube]
status: stable
evidenz: einzelmessung
ebene: act23-ab
generated: { by: claude/opus-5.5, at: 2026-10-08T00:00:00Z }
sources:
  - id: code
    resource: "14ce487 (ACT23_FEHLGRIFF_KOPF, src/pc_cvnn/arm_modules/fehlgriff_kopf.py)"
    title: Fehlgriff-Kopf
  - id: lauf
    resource: "c4_state, NO_PERSIST, GUI-Aufbau (ACT16_ABLAGE_FIX=1 ACT23_LOSLASS_KOPF=1 ACT23_LOSLASS_SELBST=1 ACT16_ENDE_HALTEN=30), ACT23_GREIF_SPUR=1, Seed 9115, 100 Ep; Kontrolle = Diagnoselauf aus zwischen-zufassen-und-anheben"
    title: A/B 2026-10-08
---

# Frage

[Zwischen Zufassen und Anheben](/befunde/zwischen-zufassen-und-anheben.md) fand: nach einem
herausgerutschten Griff schwebt die Hand mit leerer, geschlossener Klaue an einer Teacher-Schwelle,
weil die MSE-Policy an der Sprungstelle "anheben / aufmachen" mittelt. Die Schwelle zu verschieben
verschob nur den Haengepunkt. Traegt ein eigener Kopf fuer diese eine Entscheidung?

# Bau

`FehlgriffKopf` (eigenes Modul, nicht persistiert, beim Laden aus dem DAgger-Puffer gelernt und mit
dem Loslass-Kopf nachtrainiert):

* zustaendig, wenn die Klaue geschlossen ist (`j5 < 0,27`) und die Hand mehr als 30 mm vom Ziel
  steht - am Ziel entscheidet der Loslass-Kopf;
* fuenf Aspekte aus dem Policy-Zustand: Fingerdruck, Klauenwinkel, Hand ueber dem Greifpunkt,
  Objektglaube ueber Ruhehoehe, Hand gegen Objektglauben seitlich;
* Etikett: der Teacher mit vorgezogener Schwelle (`NACHGRIFF_FIX` nur fuer diese Etiketten, die
  Policy-Daten bleiben unberuehrt); `j5 >= 0,45` heisst aufmachen;
* zur Laufzeit: dreimal in Folge `p > 0,5` -> Klaue auf, bis sie gefuehlt offen ist; hoechstens
  drei Mal je Episode; die Efferenzkopie `_nachgreifen` verhindert, dass das Oeffnen als "Ablage"
  die Episode beendet.

**Architektur:** dasselbe kleine MLP wie der Loslass-Kopf. Nach dem Nutzerprinzip, andere
Architekturen nur bei begruendetem Zweifel zu nehmen, erwogen und beibehalten: der Zweifel betraf
die gemeinsame Regressions-Policy an Sprungstellen, nicht kleine Entscheidungskoepfe. Der Befund
unten bestaetigt das - der Kopf entscheidet richtig; was fehlt, liegt nicht in seiner Architektur.

# Offline

Zeitlich geteilt (die letzten 20 % des Puffers als Halteteil, ohne Luecke): 645 von 653 Fehlgriff-Zustaenden
erkannt, 1 Fehlalarm in 329 "weiter anheben"-Zustaenden, 0 Ausloesungen in gehaltenen Zustaenden
(Druck > 0,3).

# act23-A/B

Gleicher Zustand, gleicher Seed, alle 100 Aufgaben gepaart (Szenen-Abdruck):

| | Kontrolle | Fehlgriff-Kopf |
|---|---|---|
| gehoben | 68 | 69 (12 gegen 11 Paare, p = 1,00) |
| geliefert | 52 | 55 (12 gegen 9, p = 0,66) |
| herausgerutscht, nicht gehoben | 14 | 18 |
| nur in der Luft geschlossen | 2 | 0 |
| Episoden mit Kopf-Eingriff | - | 22 (52 Eingriffe) |

**Der Kopf tut, wofuer er gebaut ist.** Er feuert 26-33 mm ueber dem Greifpunkt bei Druck 0, die
Klaue oeffnet, die Hand greift neu - das Schweben aus der Kontrolle tritt nicht mehr auf. Ein
einziger Eingriff traf einen getragenen Gegenstand (86 mm Hub, 1,1 N - ein schwacher Griff).

**Aber die Neugriffe treffen nicht:**

    erster Schluss unten (n = 22)     Hand - wahres Objekt 14 mm, Glaube - wahr 13 mm
    weitere Schluesse unten (n = 41)  Hand - wahres Objekt 38 mm, Glaube - wahr 36 mm

13 der 22 Episoden schoepfen alle drei Eingriffe aus, ohne zu heben. Der erste, randstaendige
Griff schiebt das Objekt beim Rutschen weg; der Objektglaube bleibt dort, wo der Druck verloren
ging. Der Neugriff zielt mit der richtigen Entscheidung auf eine noch falschere Stelle. 6 der 22
Episoden werden gerettet (gehoben), 5 in der Kontrolle gehobene gehen verloren - Nettowirkung null.

# Lehre

Die Entscheidung "aufmachen" war ein Teilproblem und ist mit einem eigenen Kopf geloest. Der
Engpass dahinter ist dieselbe Verortung wie beim ersten Griff: ohne neuen Blick nach dem Oeffnen
kann ein zweiter Versuch nicht besser sein als der erste. Das Muster kennt das Projekt schon aus
[Noch an der Hand?](/befunde/halt-sehen.md): dort fand das **Nachsehen** (Kamera sucht den eigenen
Farbfleck nach dem Oeffnen) das gefallene Objekt auf 4 mm. Dieses Nachsehen haengt im Code am
Tragen-Zweig (`HALT_SELBST=4`) und lief hier nicht.

Naheliegender naechster Schritt (nicht gebaut): das Nachsehen auch nach einem Fehlgriff-Eingriff
ausloesen, sodass der Neugriff auf die gesehene Lage zielt. `ACT23_FEHLGRIFF_KOPF` bleibt Vorgabe 0.

# Verwandt

* [Zwischen Zufassen und Anheben](/befunde/zwischen-zufassen-und-anheben.md) - die Diagnose
* [Loslassen](/befunde/loslassen.md) - das Muster eines eigenen Entscheidungskopfs
* [Noch an der Hand?](/befunde/halt-sehen.md) - Nachsehen nach dem Oeffnen
* [Aufmerksamkeit fuer Objekt und Ziel](/fragen/aufmerksamkeit-objekt-ziel.md) - Objektglaube 12-16 mm
