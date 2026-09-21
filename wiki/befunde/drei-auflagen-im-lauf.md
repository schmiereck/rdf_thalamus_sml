---
type: Befund
title: Drei Auflagenformen im Lauf - die Schaetzung verschlechtert sich genau wie vorhergesagt, und die Aufgabe merkt es nicht
description: Die act23-Gegenprobe zur dritten Auflage. Die Sonde hatte recht, quantitativ - der Schaetzfehler steigt von 0,8 auf 2,2 mm, nur 45 Prozent der Schaetzungen treffen noch die richtige Stufe. Gestapelt wird trotzdem 17 von 20 gegen 15 von 17 mit dem Privileg (85 gegen 88 Prozent, p = 1,00), die neue 60-mm-Platte sogar 7 von 7. Der Grund ist messbar - die Fehlschlaege sind seitlich, nicht senkrecht - Versatz 65 mm gegen 15 mm -, und der Schaetzfehler ist bei gelungenen und misslungenen Stapeln gleich gross. Eine neue Spielart der Pruefstandsfalle: die Sonde war nicht falsch, sie hat ein strengeres Kriterium gemessen, als die Aufgabe braucht.
tags: [act23, stapeln, hoehe, wahrnehmung, pruefstandsfalle]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-21T00:00:00Z }
sources:
  - id: ab
    resource: "Drei kopflose Laeufe nacheinander auf Kopien von act23_state.pkl (ad9d768c), Seed 7001, **vom NETZ gefahren** (`ACT23_CHOREO` nicht gesetzt = Vorgabe `netz`; das zuvor hier stehende 'Teacher fahrend' war falsch, s. Invarianten): warm 60 Episoden (49 Zieladressen, 12 Lernbeispiele verworfen -> 37 Zeilen ueber drei Platten), dann A und B je 40 aus DEMSELBEN warmen Zustand. Rezept identisch zur Zwei-Grundriss-Reihe, einziger Unterschied ACT23_SOCKEL_N=3 statt ACT23_SOCKEL2=1; Unterschied zwischen den Armen allein ACT23_HOEHE_SEHEN=0 gegen =1"
    title: Das Drei-Grundriss-A/B
  - id: sonde
    resource: /befunde/dritte-auflage-bricht-die-nachbarschaft.md
    title: Die Sonde, deren Vorhersage hier geprueft wird
---

# Die Vorhersage

Die Sonde sagte: mit drei Auflagenformen faellt der Schaetzer von 92 auf 62 %, auf der neuen
60-mm-Platte auf 48 %
([gemessen](/befunde/dritte-auflage-bricht-die-nachbarschaft.md)). Dort steht auch, dass ich den
act23-Lauf zunaechst nicht fahren wollte, weil die Stapelquote ihn nicht aufloesen koenne.

**Diese Begruendung war zu pauschal**, und der Nutzer hat den Lauf angefordert. Sie gilt fuer die
Quote; sie gilt nicht fuer den **Schaetzfehler**, der in jeder Episode steht, stetig ist und rund
30 Messwerte je Arm hat.

# Die Sonde hatte recht - beim Schaetzfehler

                           |Schaetzfehler|   davon richtige Stufe   > eine Stufe daneben
    zwei Auflagen (Vortag)     0,80 mm                -                    -
    drei Auflagen, Arm A       0,90 mm              66 %                 12 %
    drei Auflagen, Arm B       2,20 mm              45 %                 24 %

45 % richtige Stufe gegen die 48 % der Sonde. **Die Vorhersage trifft, und sie trifft der Groesse
nach.** Der Schaetzer ist mit drei Formen messbar schlechter geworden, im Lauf wie auf dem
Pruefstand.

> Der Schaetzer rechnet in beiden Armen mit, benutzt wird er nur in B. Dass A dabei besser liegt
> (0,90 gegen 2,20 mm), ist kein Widerspruch: in B **steuert** die Schaetzung die Ablagehoehe, die
> Szene entwickelt sich dadurch anders, und der Schaetzer sieht spaeter andere Bilder. Die Arme
> laufen auseinander, sobald der Schalter wirkt.

# Und die Aufgabe merkt es nicht

                      Stapel
    A  Privileg     15/17 = 88 %
    B  gesehen      17/20 = 85 %        p = 1,00

    je Grundriss in B:   50 mm 4/6   |   60 mm 7/7   |   70 mm 6/7

**Die neue Platte wird 7 von 7 gestapelt** - ausgerechnet die, auf der die Sonde 48 % vorhersagte.

# Warum: die Fehlschlaege sind seitlich, nicht senkrecht

                         |Schaetzfehler|        Versatz
    B  gelungen (17)          2,20 mm            15 mm
    B  misslungen (3)         2,30 mm            65 mm

    A  gelungen (15)          1,90 mm            18 mm
    A  misslungen (2)         1,55 mm            72 mm

**Der Schaetzfehler ist bei gelungenen und misslungenen Stapeln gleich gross** - in A haben die
Fehlschlaege sogar den kleineren. Was sie unterscheidet, ist der seitliche Versatz: 15 gegen
65 mm, also Vorbeigriffe, keine Hoehenfehler.

Das ist geometrisch auch zu erwarten. Ob ein Wuerfel auf einer Platte liegen bleibt, entscheidet,
ob sein Schwerpunkt ueber der Auflage steht - eine **seitliche** Bedingung. Die Ablagehoehe muss
nur gut genug sein, um weder in die Platte zu fahren noch aus grosser Hoehe zu werfen; **zwei
Millimeter sind dafuer belanglos.**

# Die Lehre, und sie ist eine neue Spielart einer alten Falle

> **Die Sonde war nicht falsch. Sie hat ein strengeres Kriterium gemessen, als die Aufgabe
> braucht.**

"Richtige Stufe von dreien" verlangt den Fehler unter 2 mm. Die Aufgabe verlangt ihn unter -
gemessen an diesen Daten - deutlich mehr. Ein Pruefstandsmass, das feiner aufloest als die
Aufgabe, meldet einen Zusammenbruch, wo keiner ist.

Das unterscheidet diesen Fall von den drei in
[Pruefstandsfalle](/mechanismen/pruefstandsfalle.md) gesammelten: dort sagte der Pruefstand eine
Wirkung vorher, die nicht kam. **Hier kam die vorhergesagte Verschlechterung genau, und sie war
folgenlos.** Die Falle liegt nicht in der Messung, sondern in der Wahl der Messgroesse.

## Was das rueckwirkend ueber die ganze Hoehen-Linie sagt

Die Hoehe wird gebraucht - ohne sie faehrt die Klaue in die Auflage, das ist der Grund fuer
`ACT16_GOAL_Z`. Aber sie wird nur **grob** gebraucht. Der Ertrag der Stufe-3-Linie ist damit
sauber benennbar und er ist nicht die Genauigkeit:

* **Ertrag:** eine Groesse, die der Agent gesagt bekam, kommt aus seinem eigenen Bild
  ([das Privileg ist gefallen](/befunde/oberkante-ohne-privileg.md)) - und das haelt auch, wenn die
  Welt drei Auflagenformen hat.
* **Kein Ertrag:** Genauigkeit. Zwischen 0,8 und 2,2 mm Schaetzfehler liegt fuer die Aufgabe
  nichts.

# BERICHTIGUNG 2026-09-21: es war das NETZ, nicht der Teacher

In der Quellenzeile stand "Teacher fahrend". **Das war falsch.** `ACT23_POLICY=teacher` waehlt nur
den Greifer; wer die Teilziele faehrt, entscheidet `ACT23_CHOREO`, und dessen Vorgabe ist `netz`.
Diese Laeufe hat also die **gelernte Policy** gefahren.

Am A/B aendert das nichts - beide Arme hatten dieselbe Einstellung. Es aendert die **Lesart**, und
zwar zugunsten des Befundes: die Quoten stammen nicht von der gescripteten Choreographie, sondern
von der Policy.

# Fallen

* **`p = 1,00` bei 17 gegen 20 Urteilen.** Erst ein Einbruch auf 11 von 20 (55 %) waere trennbar
  gewesen. Die Aussage "die Aufgabe merkt es nicht" stuetzt sich deshalb **nicht** auf die Quote,
  sondern auf den Vergleich Schaetzfehler-gelungen gegen -misslungen und auf den Versatz. Die
  Quote ist die schwaechste Zahl auf dieser Seite.
* **n = 3 Fehlschlaege in B.** Der Satz "die Fehlschlaege sind seitlich" steht auf drei Faellen in
  B und zwei in A. Die Richtung ist in beiden Armen dieselbe und der Abstand gross (15 gegen
  65 mm), aber es sind fuenf Episoden.
* **Nur "keine Wirkung, die dieser Lauf zeigen koennte".** Ein feineres Hoehenraster, eine
  schmalere Auflage oder ein Objekt mit kleinerer Standflaeche koennten die Hoehe sehr wohl
  bindend machen. Der Befund gilt fuer diese Welt.
* **Nicht mit fruehereren Zahlen vergleichen.** Die XML hat seit `sockel3` wieder einen Koerper
  mehr ([Invarianten](/mechanismen/invarianten.md)). Die 88 % hier und die 94 % der
  Zwei-Grundriss-Reihe sind nicht zeichengenau vergleichbar; innerhalb dieses Laufs ist der
  Vergleich sauber.
* **Der Schaetzer bleibt unveraendert.** Die vier auf dem Pruefstand gemessenen Abhilfen sind
  weiterhin nicht uebernommen - dieser Lauf gibt keinen Anlass dazu, im Gegenteil.

# Verwandt

* [Die dritte Auflage bricht die Nachbarschaft](/befunde/dritte-auflage-bricht-die-nachbarschaft.md) - die Sonde, deren Vorhersage hier eintrifft und folgenlos bleibt
* [Der lokale Hoehenschaetzer haelt im Lauf](/befunde/lokaler-schaetzer-im-lauf.md) - dieselbe Messung mit zwei Auflagenformen
* [Die Oberkante ohne Privileg](/befunde/oberkante-ohne-privileg.md) - worum es in der Linie eigentlich geht
* [Pruefstandsfalle](/mechanismen/pruefstandsfalle.md) - die drei aelteren Faelle, und wie sich dieser unterscheidet
* [Stapeln als Aufgabe](/fragen/stapeln-als-aufgabe.md) - Stufe 3
