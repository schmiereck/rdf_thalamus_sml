---
type: Frage
title: Formabhaengige Griffwahl - heute greift der Agent die ganze Form, weil er nichts anderes darstellen kann
description: Konzept nach der Nutzerbeobachtung im GUI-Lauf 2026-10-09. Am Code belegt - Handgelenk, Greifpunkt und Kandidaten sind alle aus der GESAMTform abgeleitet (k=2-Achse des ganzen Flecks, Material naechst dem Schwerpunkt, Kandidaten hoechstens 0,3 Halbspannen davon, in 78 % der Episoden genau einer). Ein Griff "diese Zinke, quer zu ihr" ist nicht darstellbar. Vorschlag in drei Stufen - erst den Wert mit einer festen Probe-Regel auf Kopien messen (mit vorab festgelegtem Abbruchkriterium), dann den Griff-Kandidaten lokal beschreiben (Punkt, lokale Achse, lokale Breite, Abstand zum Schwerpunkt), dann aus eigenem Tasten waehlen lernen. Grenzt sich gegen die geschlossenen Faeden ab.
tags: [act23, greifen, form, wrist, greifpunkt, konzept, selbstlernen]
status: stable
evidenz: vermutung
ebene: code
generated: { by: claude/opus-5.5, at: 2026-10-10T00:00:00Z }
sources:
  - id: nutzer
    resource: "Nutzerbeobachtung zum GUI-Lauf 2026-10-09, woertlich in /befunde/gui-lauf-2026-10-09.md"
    title: Beobachtung
  - id: code
    resource: "shape_classifier.py perceive_all (_yaw_from, grasp, grasp_cands), pc_act16.py:567-583 (wrist_tgt), pc_act23.py:6976-7010 (Kandidatenschranke)"
    title: Ist-Zustand am Code, Commit b7ecbc0
  - id: lauf
    resource: "log/pc_act23_2026-10-09_14-13-40_32344.txt, 667 Episoden"
    title: GUI-Lauf 2026-10-09
---

# Anlass

Der Nutzer beobachtete im GUI-Lauf 2026-10-09 ([woertlich hier](/befunde/gui-lauf-2026-10-09.md)):
Der Agent zielt nicht auf eine gut greifbare Zinke. Er richtet sich nach der ganzen Laenge aus und
versucht, das Objekt im Ganzen "in die Zange zu nehmen". Oft klappt es nur, weil das Objekt
rutscht und eine schmale Zinke zwischen die Naegel geraet. Es fehlt, einen Griff passend zur Form
zu waehlen und ihn gezielt ueber Position und Handgelenkdrehung auszufuehren.

Die Formen mit Zinken liefern im selben Lauf deutlich schlechter. Der Verlust entsteht dabei nicht
beim Anheben, sondern danach:

    Objekt     n   geliefert  nie getragen   eigene Ablage trifft
    U         91     21 %        15 %             43 %
    L         89     33 %        11 %             58 %
    T         91     41 %         5 %             74 %
    X         98     53 %         7 %             76 %
    Wuerfel/Balken 298  40-54 %  19-25 %        85-93 %

Fehlablagen haengen an der Querlage in der Klaue: daneben gegen geliefert 9 gegen 1 mm im GUI-Lauf,
10 gegen 2 mm in beiden Langlaeufen (p <= 0,0001). Ein Objekt, das an einer zufaelligen Zinke ausserhalb der Mitte gegriffen
wird, haengt schief und kommt seitlich versetzt an.

# Ist-Zustand am Code: der Teilgriff ist nicht darstellbar

| Groesse | Woraus sie heute kommt | Folge fuer L/U/T/X |
|---|---|---|
| Objektachse (`yaw`) | Phase der k=2-Harmonischen des **ganzen** Flecks (`_yaw_from`) | Hauptachse der Gesamtform, keine Zinkenachse; beim X fast entartet |
| Handgelenk im Teacher | `wrist_tgt = Laengsachse + 90 Grad`, "greif die kurze Achse" (`pc_act16.py:567`) | Fuer Balken richtig. Bei L/U spannt die Klaue quer ueber die **ganze** Form - genau das Bild des Nutzers |
| Handgelenk im Weltmodell | 8er-Gitter um diese Gesamtachse (`WRIST_REL`), Kreuz-Merkmal `cos2(w - yaw)` | Lernt nur relativ zur Gesamtachse; eine Zinke im 90-Grad-Winkel dazu passt nur zufaellig |
| Greifpunkt | Material naechst dem Schwerpunkt | Beim U meist der innere Schlitzrand ([U-Form-Engpass](/befunde/u-form-engpass.md)) |
| Kandidaten | <= 6 dicke Maskenpunkte, Abstand >= 12 mm, dann Schranke `min(12 mm, 0,3 x Halbspanne)` | Im GUI-Lauf **474 von 608** Episoden mit genau einem Kandidaten, 125 mit zwei. Eine andere Zinke liegt immer ausserhalb der Schranke |

Der Agent kann also nicht schlecht waehlen, er hat schlicht keine Wahl. Alle drei Groessen
beschreiben das Objekt als Ganzes. Die Schranke war 2026-08 begruendet: verschobene Griffe hielten
schlechter, 64 % bis 0,3 Halbspannen gegen 24 % darueber. Gemessen wurde das aber an Verschiebungen,
die das Weltmodell **gegen die Gesamtachse** gewaehlt hatte. Das Handgelenk passte also nicht zum
neuen Punkt.

# Abgrenzung gegen geschlossene Faeden

Die folgenden Faeden beruehrt das Konzept. Was davon gilt und wo es abweicht:

* **"Greifen ueber den Teacher hinaus lernen"** ([Greif-Lerndeckel](/befunde/greif-lerndeckel.md)).
  Dort wurde RL, Suche oder Argmax ueber denselben Aktionsraum gefahren, die Darstellung blieb
  unveraendert. Das gemeinsame Argmax ueber Punkt und Handgelenk hat durch Modellausbeutung
  geschadet. Hier soll sich die **Darstellung** aendern, nicht die Suche. Das ist derselbe Hebel
  wie beim Kreuz-Merkmal, dem einzigen gemessenen Selbstlern-Erfolg am Griff (D gegen E,
  p ~ 0,03, 20-mal dateneffizienter; [Wrist-Ausrichtung](/befunde/wrist-ausrichtung.md)).
  Die Kandidaten bleiben diskret und auf Material, die Wahl bleibt LCB.
* **Erzwungener Greifpunkt auf der Zinke** (`ACT23_FORCE_GRASP=prong`, 2026-07). Das ist der
  wichtigste Gegenbefund: L 8/20, U 5/20 gegen je 9/20; mit privilegiertem Handgelenk L und U je
  11/20. Das privilegierte Handgelenk lag aber an der **Gesamt**-Laengsachse (`obj_yaw`), nicht
  quer zur gegriffenen Zinke. Punkt, lokale Achse und Lage zum Schwerpunkt zusammen wurden nie
  gemessen. Bei n = 20 schliessen die Zahlen einen Gewinn von 10-15 Punkten nicht aus, stuetzen
  ihn aber auch nicht. **Deshalb kommt die Wertprobe zuerst.**
* **U-Greifpunkt im Schlitz** (folgenlos, p = 0,81) und **Nagelneigung** (folgenlos) bleiben
  unberuehrt.
* **Das Wrist-Gitter**: die Lage des Gitters wiegt 2,3-mal mehr als seine Dichte
  ([Wrist-Gitter](/befunde/wrist-gitter-kostet-nichts.md)). Das ist ein Argument **fuer** das
  Konzept: der Anker gehoert dorthin, wo gegriffen wird.

# Vorschlag in drei Stufen

## Stufe 0 - Wertprobe (fest, nur auf Kopien, nie Vorgabe)

Ein Probe-Schalter nach dem Muster von `ACT23_FORCE_WRIST`, etwa `ACT23_FORCE_GRASP=lokal`:

* Kandidaten ueber das **ganze** Material, nicht nur am Schwerpunkt;
* je Kandidat die lokale Materialachse (Strukturtensor der Maske in einer Umgebung von rund 10 mm)
  und die lokale Breite (zweimal die Distanztransformation);
* gewaehlt wird der Kandidat, dessen lokale Breite in die Klaue passt und der dem Schwerpunkt am
  naechsten liegt (Balance, gegen das Haengen beim Tragen);
* das Handgelenk steht quer zur lokalen Achse.

Gemessen wird als act23-A/B mit `ACT23_SZENE_JE_EPISODE`, gepaart nach Aufgabe, nur L/U/T/X,
2 x 100 Episoden auf einer Kopie des Hauptzustands:
- gehoben, geliefert;
- Querlage in der Klaue;
- Treffer der eigenen Ablage.

**Vorab festgelegtes Kriterium:** geliefert auf den Zinkenformen +10 Punkte oder mehr bei
McNemar p < 0,05, dann weiter mit Stufe 1. Sonst wird der Faden mit Befundseite geschlossen.
Bleibt die Lieferung gleich, sinkt aber die Querlage, ist das ein Mechanismus ohne Wirkung und
ebenfalls ein Abbruch.

Kosten: ein Schalter, rund 6-7 h Lauf.

## Stufe 1 - den Griff-Kandidaten lokal beschreiben

Der feste Teil aus Stufe 0 wird zur **Wahrnehmung**, die Wahl selbst bleibt beim Modell:

* `perceive_all` liefert je Kandidat Punkt, lokale Achse, lokale Breite und Abstand zum
  Schwerpunkt in Halbspannen. Die Kandidaten liegen entlang der Mittellinie des Materials, nicht
  nur auf den dicksten Punkten.
* Das Weltmodell bekommt die Merkmale **relativ zum Kandidaten**: `cos2(w - lokale Achse)`,
  `sin2(...)`, lokale Breite im Verhaeltnis zur Klauenoeffnung, Schwerpunktabstand. Das
  Handgelenk-Gitter wird um die lokale Achse des Kandidaten aufgespannt statt um die Gesamtachse.
* Die Schranke wird an den Schwerpunktabstand gekoppelt statt an die Verschiebung vom
  Heuristik-Punkt. Ein Punkt auf einer anderen Zinke ist dann waehlbar, eine Zinkenspitze weit
  aussen bleibt teuer.
* Der Teacher (nur im Training) richtet die Klaue quer zur lokalen Achse seines Punkts aus. So
  lernt die Policy lokale Griffe, statt die Gesamtform nachzuahmen. Zur Laufzeit waehlt das
  Weltmodell.

Fuer Wuerfel und Balken aendert sich nichts: lokale Achse und Gesamtachse fallen dort zusammen.
Das ist zugleich die Gegenprobe, die anschlagen muss: Wuerfel duerfen sich im A/B nicht bewegen.

## Stufe 2 - die Wahl aus eigener Erfahrung

Etiketten fuer die Kandidatenwahl:
- der Tastsinn beim Anheben (`ACT23_GRIPLABEL`, labelt rund 62 % der Fehlgriffe kausal am Griff);
- der Ablageerfolg.

Beides ist eigene Erfahrung und kein Teacher-Etikett ([weniger Teacher](/befunde/tastetikett-gegen-privileg.md)).
Gemessen wird wie beim Kreuz-Merkmal: Wird die Wahl formabhaengig? Faellt bei L, U, T und X ein
anderer Kandidat als bei Wuerfeln, und liefern die gewaehlten Griffe besser als die nicht gewaehlten?

Spaeter, nicht Teil dieses Konzepts: die Masken-Geometrie (Strukturtensor, Distanztransformation)
ist Geruest wie `perceive_all` selbst (Architekturregel 1). Der naechste Schritt waere eine auf der
Fovea gelernte Greifbarkeitskarte, deren Etikett ebenfalls aus dem Tasten kommt.

# Risiken

* **Modellausbeutung**: Mehr Kandidaten bedeuten mehr Stellen, an denen das LCB in duenn belegte
  Bereiche laeuft. Abhilfe: neue Kandidaten nur dort anbieten, wo die Fehlerroute sie labeln kann.
  Das ist dieselbe Kopplung wie 2026-08 ("Falsifizierbarkeit").
* **Etikettenhunger**: Gerade die Zinkenformen liefern selten und bekommen deshalb wenig Etiketten.
  Rund 38 % der Fehlgriffe enthalten sich weiterhin.
* **Pruefstandsfalle**: Stufe 0 ist bereits ein act23-A/B. Eine isolierte Greifprobe ersetzt sie
  nicht.
* **Die Nutzerbeobachtung ist eine Beobachtung.** Dass die Klaue quer ueber die Gesamtform steht,
  ist am Code belegt. Dass das die Lieferung kostet, ist es noch nicht. Das klaert Stufe 0.

# Verwandt

* [GUI-Lauf 2026-10-09](/befunde/gui-lauf-2026-10-09.md) - Anlass und Zahlen
* [Wrist-Ausrichtung](/befunde/wrist-ausrichtung.md), [U-Form-Engpass](/befunde/u-form-engpass.md),
  [Greif-Lerndeckel](/befunde/greif-lerndeckel.md), [Wrist-Gitter](/befunde/wrist-gitter-kostet-nichts.md)
* [Laufzeit-Regeln](/mechanismen/laufzeit-regeln.md) - warum Stufe 0 nie Vorgabe wird
