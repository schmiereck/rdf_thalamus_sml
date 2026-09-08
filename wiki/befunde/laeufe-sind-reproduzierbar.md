---
type: Befund
title: Zwei Laeufe mit gleicher Einstellung sind dieselbe Rechnung
description: Ein act23-Lauf ist bei gleichem Ausgangszustand, gleichem Seed und gleichen Schaltern bitgleich reproduzierbar - 200 Episoden lang auf den Millimeter. Innerhalb eines Laufs wiederholt sich dagegen nichts (94,5 Prozent verschiedene Szenen). Folge fuer die Messhygiene: die Replikate sind die Seeds, nicht die Wiederholungen.
tags: [act23, messhygiene, determinismus]
status: stable
evidenz: gemessen
ebene: langlauf
generated: { by: claude/opus-5, at: 2026-09-08T09:00:00Z }
sources:
  - id: armB
    resource: log/pc_act23_2026-09-07_18-12-30_22068.txt
    title: Arm B des Welt-Fit-A/B, 200 Episoden, FULL_EVERY=4
  - id: gui
    resource: log/pc_act23_2026-09-08_06-32-09_7140.txt
    title: GUI-Lauf des Nutzers vom 08.09., 286 Episoden, gleiche Vorgaben
  - id: armA
    resource: log/pc_act23_2026-09-07_18-12-30_9556.txt
    title: Arm A, 200 Episoden, FULL_EVERY=1
  - id: seeds
    resource: "Vier Laeufe je 6 Episoden aus einem eingefrorenen Zustandsschnappschuss (72e561bc), ACT23_SEED nicht gesetzt / 7 / 11 / 23"
    title: Seed-Vergleich aus einem Schnappschuss
---

# Anlass

Nutzerbeobachtung in `run_history`: *"Die letzten drei angezeigten Laeufe sind alle ca. 200
Episoden lang und sehen bei Lieferquote, Enthaltung und 'haelt beim Heben' extrem aehnlich aus.
Trainieren wir immer wieder die gleichen Episoden? Ich haette gedacht, dass die Schwankungen
zwischen den Laeufen groesser sind."*

# Behauptung

Sie sind nicht aehnlich - **zwei davon sind dieselbe Rechnung.** Ein act23-Lauf ist bei
gleichem Ausgangszustand, gleichem Seed und gleichen Schaltern vollstaendig deterministisch. Es
gibt zwischen zwei solchen Laeufen **keine** Streuung, die man durch Wiederholen mitteln
koennte.

Innerhalb eines Laufs wiederholt sich dagegen nichts nennenswert: 189 von 200 Szenen sind
verschieden. Die Antwort auf die Frage lautet also: **nein, innerhalb eines Laufs nicht - aber
ein neu gestarteter Lauf mit unveraenderten Eingaben rechnet den alten nach.**

# Zahlen

Episode fuer Episode verglichen, ueber die ersten 200 Episoden:

    Arm B (FULL_EVERY=4)  gegen  GUI-Lauf des Nutzers vom 08.09.
      gleiche Szene (alle 7 Koerperlagen)      200/200 = 100,0 %
      gleiches kommandiertes Objekt            200/200 = 100,0 %
      Ausgang identisch (geliefert UND mm)     200/200 = 100,0 %

    Arm A (FULL_EVERY=1)  gegen  Arm B
      gleiche Szene                             20/200 =  10,0 %
      erste Abweichung: Episode 19
      gleiches Objekt                           66/200 =  33,0 %

    Wiederholung INNERHALB eines Laufs
      Arm A   200 Episoden -> 189 verschiedene Szenen (94,5 %)
      Arm B   200 Episoden -> 187 verschiedene Szenen (93,5 %)
      GUI     286 Episoden -> 271 verschiedene Szenen (94,8 %)

Verschiedene Seeds trennen dagegen sofort. Vier Laeufe aus **einem eingefrorenen
Schnappschuss** (`72e561bc`), je 6 Episoden, Endabstaende:

    ACT23_SEED nicht gesetzt   10 | 14 | 22 | 121 | 15 | 26 mm
    ACT23_SEED=7               10 | 14 | 22 | 121 | 15 | 26 mm   <- bitgleich zu "nicht gesetzt"
    ACT23_SEED=11              26 | 19 | 11 |  22 | 11 | 26 mm
    ACT23_SEED=23              29 |  8 | 14 |  16 | 57 |  4 mm

Ab Episode 1 verschieden. **Der Seed ist der einzige Hebel fuer echte Variation.**

# Warum

MuJoCo ist hier deterministisch, die Lerner kommen aus derselben Pickle-Datei, und der
Zufallsstrom fuer Szenenaufbau und Auto-Zielwahl haengt an einem einzigen `default_rng`
(`pc_act23.py:2014`). Damit ist der ganze Lauf **eine** deterministische Kette: gleiche Eingaben,
gleicher Verlauf.

Sobald irgendetwas eine Entscheidung aendert, entkoppelt sich der Strom und **alles** danach ist
verschieden - genau das sieht man bei Arm A gegen Arm B ab Episode 19, wo der andere Fit-Plan
zum ersten Mal durchschlaegt.

Neu ist der Befund im Code nicht: `pc_act23.py:2010` haelt fuer die Parallel-Worker bereits fest,
*"without distinct seeds here they would replay bit-identical episodes"*, und ein Kommentar bei
`pc_act23.py:2437` formuliert die Konsequenz schon als Regel: **die Replikate sind die Seeds.**
Neu ist, dass es dem Nutzer in `run_history` sichtbar entgegentritt und dass es jetzt an einem
200-Episoden-Paar belegt ist statt an einer Nebenbemerkung.

# Nebenbefund: die Kopfzeile nennt den falschen Seed

Ohne gesetztes `ACT23_SEED` protokolliert der Lauf `[Lauf] Kern: SEED=11` - **gefahren wird aber
mit 7.** Oben belegt: "nicht gesetzt" ist bitgleich mit `ACT23_SEED=7` und deutlich verschieden
von `ACT23_SEED=11`.

Ursache am Code: `_source_defaults()` (`pc_act23.py:4710`) liest die Vorgaben per Regex aus dem
Quelltext und nimmt mit `out.setdefault(...)` den **ersten** Treffer. `ACT23_SEED` kommt dreimal
vor - `pc_act23.py:1672` und `:1732` mit Vorgabe `"11"` (zwei Diagnose-Pruefstaende, die im
Steuerungslauf gar nicht laufen) und `pc_act23.py:2014` mit Vorgabe `"7"` (der Szenen- und
Zielwahl-Strom, der den Lauf tatsaechlich treibt). Gemeldet wird die 11, gefahren die 7.

**Das ist eine Reproduktionsfalle:** wer ein Protokoll liest und zum Nachstellen `ACT23_SEED=11`
setzt, bekommt einen **anderen** Lauf. Betroffen ist jeder Lauf ohne gesetzten Seed - also alle
GUI-Laeufe des Nutzers.

Nicht behoben, weil jede Reparatur eine Wahl erzwingt: die beiden Diagnose-Vorgaben auf `7`
ziehen aendert die Pruefstands-Konstellationen, ein eigener Name (`ACT23_DIAG_SEED`) entkoppelt
die Pruefstaende von den Seed-Sweeps der A/B-Skripte (`act23_colour_split_ab.py` und die anderen
setzen `ACT23_SEED` je Seed und wuerden den Pruefstand dann einfrieren). Beides ist eine
Entscheidung, keine Aufraeumarbeit.

# Folgen fuer die Messhygiene

> **Ein Lauf ist EINE Stichprobe, nicht n unabhaengige.** Wiederholen desselben Laufs bringt
> null neue Information. Wer Streuung braucht, muss den **Seed** variieren.

Das praezisiert zwei bestehende Seiten:

* [Rechnerlast](/befunde/rechnerlast.md) beziffert die Schwankung eines 50-Episoden-Fensters mit
  26 Punkten. Das ist Schwankung **ueber die Zeit innerhalb** eines Laufs, **nicht**
  Wiederholungsstreuung - die gibt es nicht. Die Aussage bleibt als Nachweisgrenze gueltig, ihre
  Herkunft ist damit aber praeziser benannt.
* [Kopfloses A/B](/messungen/act23-headless-ab.md) warnt: *"Gleicher Seed erzwingt in act23 keine
  gleiche Objektfolge."* Das stimmt **fuer zwei verschiedene Konfigurationen** (Arm A gegen B:
  10 % gleiche Szenen) und ist leicht falsch zu lesen. Bei **gleicher** Konfiguration erzwingt
  derselbe Seed sehr wohl dieselbe Folge - vollstaendig.

# Fallen - eine eigene

Das [A/B zum Welt-Fit](/befunde/welt-fit-plan-ab.md) lief mit **demselben Seed in beiden Armen**.
Das ist nicht falsch, aber schwaecher als dort dargestellt: die ersten 19 Episoden sind identisch
und tragen null Unterscheidungskraft, und danach vergleicht man zwei **einzelne**
Trajektorien mit verschiedenen Szenenfolgen - daher auch der dort berichtete Objektmix-Unterschied
(obj_L 35 gegen 20 Episoden). Der bessere Aufbau ist ein **gepaarter Sweep ueber mehrere Seeds**,
je Seed beide Arme, wie ihn der Kommentar bei `pc_act23.py:2437` fuer die Bindungsmessung schon
beschreibt (6 Seeds, Vorzeichentest). Das Ergebnis des A/B bleibt bestehen; seine Reichweite ist
enger.

# Verwandt

* [Sparsamer Welt-Fit, A/B](/befunde/welt-fit-plan-ab.md) - betroffen von der Falle oben
* [Kopfloses A/B](/messungen/act23-headless-ab.md) - die Vorschrift, die das praeziser fassen muss
* [Rechnerlast](/befunde/rechnerlast.md) - die Nachweisgrenze, hier eingeordnet
* [Exekutionsvarianz](/messungen/exekutionsvarianz-exv.md) - misst absichtlich die andere Richtung
