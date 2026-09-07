---
type: Befund
title: Die Ausfuehrung ist nicht der Deckel des Weltmodells
description: 40 Szenen x 4 Wiederholungen - ICC 0,61, ehrliche Obergrenze 81,9 % gegen Grundrate 54,4 %. Zwischen beiden liegen ~27 Punkte lernbares Signal; der Deckel sitzt in der Situationsrepraesentation.
tags: [act23, weltmodell, varianz]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-08-11T12:29:00Z }
verified: { by: human:thomas, at: 2026-08-11T12:29:00Z }
sources:
  - id: exv-lauf
    resource: /raw/index.md
    title: log/pc_act23_2026-08-11_10-52-00.txt - 160 Episoden, 6732 Weltzeilen, Lernen eingefroren
  - id: wm-lauf
    resource: /raw/index.md
    title: log/pc_act23_2026-08-11_20-17-49.txt - Lauf mit geloggter Weltvorhersage
---

# Behauptung

Die Streuung der Ausfuehrung erklaert **nicht**, warum das Weltmodell bei R^2 0,19 haengt.
Zwischen Grundrate (54,4 %) und ehrlicher Obergrenze (81,9 %) liegen rund 27 Prozentpunkte
lernbares Signal. Der Deckel sitzt in der **Situationsrepraesentation**, nicht in der Bahn.

Das widerruft ausdruecklich eine eigene frueheres Vermutung aus einem Rauchtest mit n = 3.

# Zahlen

40 Szenen x 4 Wiederholungen = 160 Episoden, Lernen eingefroren.[^exv-lauf]

* **ICC 0,61** (Erfolg) / **0,77** (Abstand); auf den 32 Szenen mit wirklich fixer Wahl 0,63 / 0,61
* **65 % der Szenen perfekt reproduzierbar** (12x 4/4 geliefert, 14x 0/4), 35 % kippen
* **Obergrenze fuer einen Vorhersager, der nur die Situation sieht: 81,9 %**
  (Leave-one-out *innerhalb* der Szene)
* Grundrate 54,4 %, Nullwelt 50,6 % (95 %: 38,7-62,5), p < 0,0003
* Je Objekt: L und U kippen am haeufigsten (je 50 %), gruener Wuerfel am seltensten (14 %)
* Der Greifpunkt-Abstand trennt kippende von stabilen Szenen **nicht** (Median 14,5 vs 6,0 mm, p = 0,41)

**Was das Weltmodell davon einsammelt: nichts.**[^wm-lauf] Auf den Episoden, die es selbst
faehrt, AUC 0,489 gegen den Ausgang; auf Szenenebene Spearman +0,035 (p = 0,83); selbst auf den
26 eindeutigen Szenen AUC 0,518 (p = 0,90). mu ist dabei nicht konstant (0,40-1,19).

**sigma ist nicht kalibriert** (Halteteil mit Luecke 1500, n = 500):

    Spearman(sigma, |Fehler|)   = +0,030  (p = 0,5)     -- sagt NICHT, wo das Modell falsch liegt
    Spearman(sigma, Neuheit)    = +0,173  (p = 0,0001)  -- misst Unbekanntheit, schwach
    Spearman(|Fehler|, Neuheit) = +0,042  (p = 0,35)    -- Unbekanntheit heisst NICHT falsch

Nur 30 % des Fehlers sind irreduzibel (|Fehler| bei perfekter Szenenkenntnis 0,147 gegen 0,496
beim blossen Raten), 70 % waeren vorhersagbar gewesen. **93 % von sigma stammen aus der
Initialisierung**, nur 7 % aus der Datenabdeckung: sigma ohne jedes Resampling betraegt 0,1400
gegen 0,1502.

Alle vier geplanten Rezepte sind null (Werkzeug `src/pc_cvnn/act23_wm_regime.py`):

    Gewichtung des Arbeitsbereichs x3/x10/x30 : 0,813 / 0,812 / 0,810  (Ausgangslage 0,816)
    Vergessen (letzte 3000/1500/800)          : 0,752 / 0,726 / 0,754
    Label binarisiert statt abgestuft         : 0,814
    Merkmalsbloecke                           : NICHT PRUEFBAR (Gueltig-Flag zu 0 %)

# Aufbau

[Wiederholungsmessung EXV](/messungen/exekutionsvarianz-exv.md).

# Bewertung

Drei Folgerungen, jede mit eigener Reichweite:

1. **Fuer das Weltmodell:** mehr Merkmale koennten helfen, mehr Wiederholungen nicht. Der
   Engpass ist, was das Modell von der Situation *sieht*.
2. **Fuer `mu - lam*sigma`:** die Formel zieht eine Groesse ab, die nichts ueber das Risiko
   sagt. Das erklaert den frueher gemessenen **flachen lam-Sweep** (AUC 0,747-0,753 ueber alle
   lam) - lam ist egal, weil sigma gegenueber dem Fehler Rauschen ist.
3. **Fuer die Neugier:** sigma war ueber die Situationen praktisch konstant, die Neugier waehlte
   faktisch zufaellig.

# Folgen

**Gebaut** (Commit `5ba0772`): `WorldModelModule.novelty(feats, actions=None, k=3)` - Abstand
zur k-naechsten *eigenstaendigen* Erfahrung in Einheiten der Spaltenstreuung, je
Erfahrungsgruppe minimiert. Wiederholung zaehlt nicht: 4x dieselbe Szene 12,82 -> 12,68, vier
eigenstaendige 12,82 -> 0,00. `curious_pick` nutzt es statt `sd.max()`;
`ACT23_NOVELTY_DIRECT=0` stellt sigma wieder her.

Beleg (200 echte Situationen): Spannweite 90 %/10 % - sigma 1,3x, Neuheit 6,1x; entlegene
Situation 9x des Medians; Neuheit vs sigma Spearman -0,051 (p = 0,47). Nebeneffekt: das
Rauschende-Fernseher-Problem entfaellt hier von selbst. `mu - lam*sigma` blieb unangetastet
(Risiko-Job, keine Belege dafuer).

Ebenfalls gebaut und **wirkungslos**: Block-Bootstrap nach Erfahrungsgruppe
(`ACT23_WM_BLOCK=0` schaltet ab). Korrekt und altbestandsfest, aber sigma 0,1502 -> 0,1494,
also ~1 %.

# Fallen

* **Die naive Formel `max(k,n-k)/n` gibt 88,1 %** und ist bei nur 4 Wiederholungen verzerrt -
  eine Welt aus reinen Muenzwuerfen misst damit schon 68,8 %.
* **Die 0,86 waren ein Bewertungsleck**, nicht "das Modell erkennt schlechte Aktionen". Die
  eigene erste Erklaerung war falsch. Der echte Grund ist der benachbarte Halteteil - siehe
  [Pruefstandsfalle](/mechanismen/pruefstandsfalle.md). Echte Verallgemeinerung ~0,66.
* **Widerlegt (eigene Hypothese):** der Puffer sei durch alte Zeilen vergiftet. Vergessen macht
  es schlechter, nicht besser. Die alten Zeilen helfen.
* **MuJoCo ist hier deterministisch.** Bleibt das Objekt liegen und kehrt der Arm in dieselbe
  Ruhelage zurueck, wiederholt sich eine Episode bis auf den Millimeter (63 +/- 0 und 169 +/- 0 mm
  ueber je drei Laeufe). Streuen Ergebnisse, ist die Ursache **kein Rauschen**, sondern eine
  beobachtbare versteckte Zustandsvariable - hier die Armstellung beim Start, weil
  `run_combined` mit `arm_reset=False` faehrt.
* **Die Wahl ist nicht bitgleich wiederholbar.** Mit `ACT23_WRIST_REL=1` ist das Wrist-Gitter
  armrelativ (`grid = w0 + linspace`); eine andere Armstellung verschiebt `w0` (gemessen
  ~0,1 Grad - harmlos, aber ein binaeres "identisch ja/nein" haette es als Aktionswechsel
  gewertet).

# Offen

In 8 von 40 Szenen driftete die Aktion trotz abgeschalteter Neugier und zurueckgespultem RNG
(bis 61,6 Grad Wrist, 11,6 mm Offset) - die Situationsmerkmale sind also nicht bitgleich,
vermutlich sieht die Kamera je nach Armstellung etwas anderes. Aufs Ergebnis wirkt es nicht.

# Verwandt

* [Selbst-Aneignung stockt](/befunde/selbstaneignung-stockt.md)
* [Greif-Lerndeckel](/befunde/greif-lerndeckel.md)
