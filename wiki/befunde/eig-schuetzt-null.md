---
type: Befund
title: Der Eigenschafts-Schutz wirkt nicht - er ist zu fluechtig gebaut
description: Zwei Arme zu je 400 Episoden, ACT23_EIG_SCHUETZT 0 gegen 1, sind BITGLEICH. Der Schutz liest den Momentanzustand von state.EIGENSCHAFT, und ein Tripel wird je Koerper ueberschrieben - nach wenigen Episoden ist die Klasse wieder ungeschuetzt und stirbt 20 Episoden spaeter regulaer. Die Idee braucht ein Gedaechtnis, keinen Schnappschuss.
tags: [act23, selbstlernen, formklassen, negativ]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-11T22:00:00Z }
sources:
  - id: ab
    resource: "Zwei kopflose Steuerungslaeufe je 400 Episoden aus einer Kopie von act23_state.pkl (ad9d768c), ACT23_EIG_SCHUETZT 0/1, ACT23_NOVEL_EVERY=3, gleichzeitig gefahren"
    title: Schutz-A/B
---

# Behauptung

`ACT23_EIG_SCHUETZT` ist wirkungslos. Die beiden Arme sind nicht "statistisch gleich", sie sind
**bitgleich** - jede Ergebniszeile, jede Geburt, jede Verhungerung. Der Schalter hat kein
einziges Mal eine Entscheidung veraendert.

Die Ursache ist ein Konstruktionsfehler in meinem Entwurf, kein Messproblem.

# Zahlen

    Arm         Ep   Quote | geboren verhungert ueberlebt | Median Alter | Klassen Ende  unzuordenbar
    sch_aus    400  54,5 % |    5        4          1     |    25 Ep     |      4            80
    sch_an     400  54,5 % |    5        4          1     |    25 Ep     |      4            80

    Ergebniszeilen der beiden Arme: IDENTISCH (diff leer)
    Ueberlebensrate  1/5 gegen 1/5   Fisher p = 1,0000
    Lieferquote      218/400 gegen 218/400

Der Schalter war gesetzt - das Protokoll fuehrt ihn unter den Abweichungen
(`ACT23_EIG_SCHUETZT=1 (Vorgabe '0')`).

# Warum es nicht wirkt

`state.EIGENSCHAFT` ist ein Verzeichnis **Koerper -> Tripel**, und `add_eigenschaft` ueberschreibt
den Eintrag jedes Mal, wenn derselbe Koerper neu gewuerfelt wird. Bei sieben Koerpern passiert das
im Schnitt alle sieben Episoden. Der Schutz liest damit einen **Schnappschuss**, keine Historie.

Der Lebenslauf der einen kommandierten Klasse, die trotzdem starb:

    Ep  ~40   neu-384 geboren
    Ep   54   [Auto 54] farbe-3 + neu-384   <- jetzt in state.EIGENSCHAFT, geschuetzt
    Ep  ~61   derselbe Koerper neu gewuerfelt -> Tripel ueberschrieben, Schutz WEG
    Ep  ~66   verhungert nach 26 Ep (Alter erreicht STARVE_N = 25)

**Der Schutz haelt genau so lange, wie das Tripel aktuell ist - und in dieser Zeit ist die Klasse
ohnehin zu jung zum Sterben.** Wenn sie alt genug ist, ist sie langst wieder ungeschuetzt. Deshalb
konnte der Schalter nie eine Entscheidung aendern, und deshalb sind die Laeufe bitgleich.

Die Gegenprobe im selben Lauf: `neu-386` wurde **viermal** adressiert und ueberlebte - aber in
**beiden** Armen gleich. Sie ueberlebte, weil sie genug Exemplare sammelte
(`STARVE_MIN_EX = 6`), nicht wegen des Schutzes.

# Was das ueber meine Begruendung sagt

Ich hatte geschrieben: *"die Aufraeum-Mechanik entfernt genau die Klassen, die der Agent gerade
benutzt"* ([blinder Fleck](/befunde/aneignung-blinder-fleck.md)). Gemessen stimmt das so **nicht**
- jedenfalls nicht in diesem Lauf:

* Die Klassen, die adressiert werden, sammeln dabei Exemplare und ueberleben ohnehin (neu-386).
* Die Klassen, die sterben, werden fast nie adressiert - sie brauchen keinen Schutz vor dem
  Aufraeumer, sondern **einen Grund, benutzt zu werden**.

Der Einzelfall, der mich ueberzeugt hatte - `neu-373` im Langlauf, fuenfmal adressiert und
trotzdem nach 229 Episoden verhungert - bleibt unerklaert, ist aber n = 1 und koennte dieselbe
Fluechtigkeit sein.

# Was der Zaehler-Fix wert war

Ohne [Schritt 1](/befunde/aneignung-blinder-fleck.md) waere diese Analyse nicht moeglich gewesen:
`neu-384: 1x kommandiert` und `neu-386: 4x` stehen erst seit dem Fix im Protokoll. Vorher haetten
beide `0x` gemeldet, und der Unterschied zwischen "stirbt trotz Benutzung" und "stirbt mangels
Benutzung" waere unsichtbar geblieben. **Schritt 1 hat sich bezahlt gemacht, auch wenn Schritt 2
gescheitert ist.**

# Wie es richtig ginge - nicht gebaut

Die Idee braucht ein **Gedaechtnis** statt eines Schnappschusses: "wurde diese Klasse in den
letzten N Episoden kommandiert?" Der Zaehler `acq[c]["cmd"]` fuehrt genau das bereits - er muesste
nur in `protect` einfliessen, etwa als "cmd > 0 innerhalb der letzten 50 Episoden".

**Ob das etwas bringt, ist damit aber nicht gesagt.** Die Messung oben deutet eher darauf hin,
dass der Aufraeumer nicht das Problem ist: die sterbenden Klassen werden nicht benutzt, und ein
laengeres Leben allein macht sie nicht nuetzlicher. Wer den naechsten Anlauf nimmt, sollte zuerst
fragen, **warum eine geborene Klasse so selten adressiert wird** - in 400 Episoden waren es
5 Kommandos auf 5 junge Klassen, gegen 107 auf die vier etablierten.

# Fallen

* **`NOVEL_EVERY=3` statt 6** in beiden Armen, um die Geburtenrate zu heben. Die absoluten Zahlen
  sind deshalb nicht mit dem [906-Episoden-Langlauf](/befunde/langlauf-entkoppelt.md)
  vergleichbar; der Armvergleich ist davon unberuehrt.
* **Trotz verdoppelter Neuheitsrate nur 5 Geburten auf 400 Episoden** (1,25 %) - die Rate haengt
  also kaum an `NOVEL_EVERY`. Das war nicht erwartet und ist ungeklaert.
* **Bitgleichheit ist hier ein BEFUND, kein Fehler.** Nach
  [Zwei Laeufe sind dieselbe Rechnung](/befunde/laeufe-sind-reproduzierbar.md) sind zwei Laeufe mit
  gleicher Einstellung identisch - bitgleich trotz **verschiedener** Einstellung heisst: die
  Einstellung ist folgenlos.

# Folgen

`ACT23_EIG_SCHUETZT` bleibt auf `0`. Der Schalter bleibt im Code, weil der Kommentar dort die
gemessene Begruendung traegt und ein zweiter Anlauf (mit Gedaechtnis) daran ansetzen kann.

# Verwandt

* [Der blinde Fleck der Aneignung](/befunde/aneignung-blinder-fleck.md) - Schritt 1 und 2
* [906 Episoden in der entkoppelten Welt](/befunde/langlauf-entkoppelt.md) - wo der Verdacht herkam
* [Formklassen-Lebenszyklus](/mechanismen/formklassen-lebenszyklus.md)
* [Selbst-Aneignung stockt](/befunde/selbstaneignung-stockt.md)
