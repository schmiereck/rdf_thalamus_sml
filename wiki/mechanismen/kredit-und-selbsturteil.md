---
type: Mechanismus
title: Selbst-Urteil und Kredit-Routing
description: Der Agent beurteilt seinen eigenen Ausgang ohne Privileg (~90% Uebereinstimmung) und leitet die Schuld an den Lerner, dessen Entscheidung den Ausgang dominiert hat. Enthaelt die vier Routen, die graduelle Guete und die drei Regeln, die aus Vergiftungen gelernt wurden.
tags: [act23, selbstlernen, kredit]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-07T00:00:00Z }
verified: { by: human:thomas, at: 2026-07-25T00:00:00Z }
sources:
  - id: chronik
    resource: /chronik/act23.md
    title: act23-Chronik, Dreischritt-Plan und die Vergiftungs-Eintraege
---

# Behauptung

Der Agent beurteilt selbst, ob er geliefert hat, und verteilt daraufhin selbst die Gutschrift.
Beides laeuft ohne privilegierte Simulatordaten. Das ist der Kern des vom Nutzer beauftragten
Dreischritt-Plans (Selbst-Urteil -> Kredit-Routing -> Selbst-Imitation).

# Das Selbst-Urteil (`SelfEvalModule`)

Objekt ueber die **selbst benannte** Farbklasse gefunden (Form als Rueckfall), Position ueber die
Homographie, Abstand zum Wunsch als Latent-Differenz durch die gelernte Inverse `D`.
Erfolg = gefunden UND `self_d < TOL`; Valenz = `-self_d`.

    Uebereinstimmung mit dem privilegierten Urteil: 86% -> 95% nach Haertung
    Reale GUI-Validierung: 41/45 = 91%, spaeter 1102/1218 = 90,5%
    ALLE Abweichungen konservativ (falsch-negativ) - die sichere Richtung fuer ein Tor
    Korrelation self gegen wahr r = 0,98, Median-Bias +0 mm

**Haertung 1 - Identitaet ueber Kontinuitaet:** das gelieferte Objekt ist der Blob **naechst dem
Loslass-Punkt der Hand**, Chroma nicht erforderlich (ein duennes Objekt liest sich ausgewaschen);
die Klasse ist nur ein Stichentscheid unter nahen Blobs.

**Haertung 2 - Blob-Verschmelzung:** der Richter bekommt `exp_area` = die eigene
Detektionsflaeche vom Episodenanfang. Ist der Ablage-Blob > 1,35x der erwarteten Flaeche, gilt er
als verschmolzen, und geurteilt wird ueber den Schwerpunkt des Materials **innerhalb von 35 mm um
den Loslass-Punkt**. Einheitstest: verschmolzen bei 40 mm 10,2 -> 3,6 mm, bei 30 mm 7,0 -> 1,8 mm.

# Die vier Kredit-Routen

`run_combined` liefert drei selbst gemessene Kontrollpunkte: `_maxcz` (hat der Griff gehoben),
`_slipped` (verliess das Objekt die Klaue), `_attempted` (Klaue schloss tief AM Objekt).

| Situation | Route |
|---|---|
| nie angekommen | **Enthaltung** |
| tief geschlossen, kein Hub | Aktion bekommt **Fehlschlag** |
| gehoben + geliefert | **+1 Erfolg** |
| gehoben + verrutscht | Griff bekommt **Fehlschlag** |
| gehoben + gehalten + daneben | Policy-Zielfehler -> **Enthaltung** |

Das Etikett ist das Selbst-Urteil, nicht die Wahrheit. `ACT23_CREDIT=0` stellt das alte
FSM-Tor her, `ACT23_WORLD_LABEL=welt` das privilegierte Etikett.

**Graduelle Guete** (`ACT23_WORLD_GRADED`, Vorgabe AN): ein Erfolg wird mit
`quality(d) = exp(-(d/sigma)^2)` gewichtet statt flach 1,0; `sigma = 0,025`. Kurve: 0 mm -> 1,00,
10 -> 0,85, 15 -> 0,70, 20 -> 0,53, 25 -> 0,37, 40 -> 0,08.

> **Entwurfsregel:** das Kredit-**Routing** entscheidet, OB gelabelt wird; der **Abstand**
> entscheidet, WIEVIEL. Fehlschlaege bleiben hart 0,0 - ein weicheres Negativ wuerde genau das
> falsifizierende Signal fuer schlechte Griffgeometrie stumpf machen.

Dieselbe Graduierung in der Selbst-Imitation (`ACT23_IMIT_GRADED`): das Aufnahmetor wandert von
15 auf 25 mm, das Gewicht traegt die Guete. **Entkoppelt** davon bleibt, welche Episoden die
Teacher-Korrekturen verdraengen - das haengt weiter am strengen 15-mm-Kriterium, sonst wuerde
das weitere Tor still die DAgger-Korrekturen ausduennen.

# Drei Regeln, jede aus einer gemessenen Vergiftung

1. **Ergebnis-Etiketten fliessen nur zu dem Lerner, dessen EIGENE Entscheidung den Ausgang
   dominiert hat.** Im Netz-Modus wurden Choreographie-Fehler der Aktion angelastet - sigma blieb
   bei 0,4-0,9, LCB wurde zufaellig, die Neugier frass Rauschen.
2. **Ein Kontrollpunkt isoliert die Aktion nur, wenn die ausfuehrende Choreographie
   VERTRAUENSWUERDIG ist.** Die `_attempted`-Fehlschlagroute ist unter FSM sauber, unter der
   gelernten Choreographie mehrdeutig (die Policy streift das Objekt und schliesst zum falschen
   Zeitpunkt -> der Wrist bekommt die Schuld). ~38 Fehletiketten in 120 Episoden, sigma
   0,5-0,9 -> 0,9-1,6, Bilanz 18/30 -> 10/30.
3. **Aktions-Kandidaten nur dort anbieten, wo ihre Fehlschlaege beobachtbar sind.** Nachdem die
   Netz-Fehlschlagroute abgeschaltet war, bekam ein Greifpunkt-Offset, der den Hub verhindert,
   **nie** ein Etikett - und das aufgeblaehte sigma schob LCB genau in diese unbeschrifteten
   Extrapolationen (Modellausbeutung). Fix: Maskenkandidaten werden nur angeboten, wo die
   Fehlschlagroute sie beschriften kann. A/B: Kopplung allein 17/30 = volle Erholung.

# Fallen

* **Ein Falsch-Positiv ist die EINE vergiftende Richtung.** Gemessen: eine imitierte
  "23-mm-Lieferung" war ein 53-mm-Fehlschlag (der Richter liest den Schwerpunkt eines
  laenglichen Objekts bis ~30 mm daneben). Deshalb ist das Imitationstor strenger als das
  Lieferkriterium.
* **`lifted` heisst "> 20 mm gestiegen", nicht "die Klaue hat gegriffen".** Ein flach getragenes
  U reisst die Hebeschwelle nie und wird als "nicht gegriffen (Policy)" verbucht. Die fruehere
  Deutung "47 % greift ins Leere" war dadurch **falsch**; die physische no-grasp-Rate ist
  niedriger und unbekannt. `ACT23_CREDIT_FLAT` (Vorgabe AN) zaehlt eine sichere Lieferung auch
  ohne Hub.
* **Eine Selbst-Kalibrierung der Ablage-Referenz ist gemessen gescheitert** (`ACT23_SELFREF`,
  Vorgabe AUS): die Fehllesungen sind episodenabhaengig, nicht klassenkonstant, und der Zug zum
  Loslass-Punkt fabrizierte ein selbstsicheres Falsch-Positiv.
* **Ein blankes `except: pass` verbarg einen Totalausfall** - der Latent-Dynamik-Block warf jede
  Episode einen `NameError` und trainierte nie. Fehler duerfen nicht still verschwinden.

# Verwandt

* [Der Weltmodell-Deckel](/befunde/exekutionsvarianz.md)
* [Imitationspuffer](/befunde/imitationspuffer.md)
* [Wrist-Ausrichtung](/befunde/wrist-ausrichtung.md) - dort der Befund, dass dem Weltmodell
  genau die Gegenbeispiele fehlen
