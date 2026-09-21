---
type: Befund
title: Gemischt lernen, erster Lauf - der Puffer haelt die alte Aufgabe, die Hoehe ist noch keine Funktion
description: 100 Episoden, halb Stapeln halb Tischablage, Sockel wandernd mit 6/10/14 mm. Die Mischung haelt die Tisch-Erfahrung im Puffer (16000 statt 8000 Zeilen). Die Tischablage schwankt zwischen den Zwischenstaenden stark (3 bis 15 mm), faellt aber nicht stetig - kein Verlernen, sondern ein unruhiger Refit. Die Policy nutzt die Sockelhoehe als abgestufte Groesse, aber mit falscher Steigung und R2 unter 0,3 - sie hat keine Funktion gelernt. Der Grund ist messbar: nur 10 Sockel-Szenen in 100 Episoden, die Spalte korreliert noch mit dem Zielort (r = 0,54 und 0,65).
tags: [act23, stapeln, policy, puffer, curriculum]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-19T00:00:00Z }
sources:
  - id: lauf
    resource: "Ein kopfloser Lauf auf einer Kopie von act23_state.pkl (ad9d768c), 20 + 30 + 50 Episoden (Seeds 4242/4243/4244), ACT23_ZIEL_MISCH=0.5 ACT23_SOCKEL_WANDERT=1 ACT23_SOCKEL_HOEHEN=6,10,14 ACT23_SCENE_N=3, Teacher fahrend -- UNGEPRUEFT, s. Invarianten: nur mit ACT23_CHOREO=fsm zutreffend, sonst faehrt das Netz, klassenlose Adresse"
    title: Gemischter Lernlauf
  - id: vorher
    resource: /befunde/policy-lernt-hoehe-als-ort.md
    title: Der erste Lernlauf, dessen zwei Konstruktionsfehler hier behoben sind
---

# Was geaendert wurde

Der [erste Lernlauf](/befunde/policy-lernt-hoehe-als-ort.md) hatte zwei Konstruktionsfehler: 100 %
Stapel-Episoden verdraengten die Tisch-Erfahrung aus dem Puffer, und der feste Sockel verwechselte
Ablagehoehe und Zielort. Dagegen jetzt, nach Nutzervorgabe "auf jeden Fall gemischt":

| Schalter | Wert | wogegen |
|---|---|---|
| `ACT23_ZIEL_MISCH` | 0,5 | Verdraengung - je Episode halb Stapeln, halb Tischablage |
| `ACT23_SOCKEL_WANDERT` | 1 | Verwechslung mit dem Ort - neue Stelle je Szene |
| `ACT23_SOCKEL_HOEHEN` | 6,10,14 | "Hoehe als Schalter" - drei Werte, damit eine Steigung messbar wird |
| `ACT23_SCENE_N` | 3 | mit vier Objekten kann der Sockel nur +-12 mm wandern |

Gemessen wie zuvor offline am Netz, jetzt mit einer **Steigung**: dieselben Tisch-Absenkzustaende,
die 14. Spalte auf 0 / 6 / 10 / 14 mm Auflagenhoehe gesetzt. Als HOEHE gelernt heisst: die
Zielhoehe steigt mit Steigung ~1.

# Zahlen

    Stand | Tischzeilen | dZ bei h = 6 / 10 / 14 mm  Steigung   R2 | Stapel je Hoehe: Netz / Etikett
    ck000 |    24000    |    +0,0   +0,0   +0,0        0,00    -  |
    ck020 |    17330    |   +23,6  +39,6  +48,0        2,24  0,18 |  6: 27/24
    ck050 |    16555    |    +6,9  +20,3  +34,1        2,29  0,26 |  6: 27/24   14: 45/32
    ck100 |    16105    |   +13,4  +20,6  +22,1        0,96  0,04 | 10: 39/28   14: 34/32

    Tisch-Absenkung auf den AKTUELLEN Tischzeilen (echte Spalte):
      ck000  |Fehler| 4,7 mm    ck020 14,6 mm    ck050 3,0 mm    ck100 9,7 mm

    Stapel-Episoden: 20 Stapel, 6 daneben; Sockel nie gegriffen

# Was traegt

**Die Mischung haelt die alte Aufgabe im Puffer:** 16000-17000 Tischzeilen gegen 8095 im reinen
Stapellauf. Die Verdraengung ist behoben.

**Die Policy nutzt die Hoehe als abgestufte Groesse**, nicht als Schalter: in jedem Zwischenstand
steigt die mittlere Zielhoehe monoton mit h (bei ck050 +6,9 / +20,3 / +34,1 mm).

# Was nicht traegt

**Eine Funktion ist es noch nicht.** Die Steigung liegt bei 2,2-2,3 und faellt dann auf 1,0 mit
einem Versatz von +13 mm schon bei 6 mm; R2 bleibt unter 0,3. Die Antwort auf die Hoehe haengt also
weit mehr an den uebrigen Zustandsgroessen als an der Hoehe selbst. In der eigenen Verteilung liegt
die Stapelhoehe 3-13 mm zu hoch - schlechter als mit festem Sockel (dort 2 mm), weil jede
Kombination aus Ort und Hoehe jetzt seltener vorkommt.

**Die Tischablage schwankt stark** - auf den aktuellen Tischzeilen 14,6 -> 3,0 -> 9,7 mm. Das ist
kein stetiges Verlernen (bei ck050 ist sie besser als am Anfang), sondern ein unruhiger Refit.
Dieselbe Unruhe zeigte der reine Stapellauf (16,8 -> 19,7 -> 7,9 mm auf den alten Zustaenden). Mit
drei Zwischenstaenden ist Rauschen von einem Trend nicht zu trennen.

> **Gegenueber dem ersten Lauf zurueckgenommen:** dort stand "die Tischablage liegt 12-15 mm zu
> hoch" als Folge der Verdraengung. Das war auf ALTEN Zustaenden gemessen, und die Schwankung hier
> zeigt, dass ein einzelner Zwischenstand dafuer nicht reicht. Die Verdraengung selbst ist belegt,
> ihre Folge fuer die Tischablage ist es nicht sicher.

# Der messbare Grund: zu wenige Szenen

    Sockel-Szenen in 100 Episoden:   10    (ACT23_SCENE_EVERY = 10, Vorgabe)
    Zielort der Stapelzeilen:         x +15 +- 64 mm,  y 180 +- 14 mm   (vorher +-6,5 / +-8,7)
    Korrelation Spalte 14 ~ Zielort:  x -0,54,  y +0,65

Der Sockel wandert jetzt wirklich (Streuung in x zehnmal groesser), aber eine Szene haelt zehn
Episoden lang. **Zehn Kombinationen aus Ort und Hoehe reichen nicht, um das eine vom anderen zu
trennen** - die Spalte ist noch zu mehr als der Haelfte mit dem Zielort korreliert.

# Was als naechstes zu messen ist

Mehr Szenen, nicht mehr Episoden allein: `ACT23_SCENE_EVERY=2` gibt bei 200 Episoden rund 100
Kombinationen. Und Zwischenstaende in kuerzeren Abstaenden, damit sich die Schwankung des Refits
von einem Trend unterscheiden laesst.

# Fallen

* **`ebene: pruefstand`.** Gemessen ist das Netz; ob es selbst fahrend stapelt, steht aus.
* **Ein Lauf.** Die Schwankung zwischen den Zwischenstaenden ist so gross wie die Effekte, die
  man sucht.
* **Die Stichproben je Hoehe sind klein**, und nicht jede Hoehe kommt in jedem Zwischenstand vor
  (bei ck020 nur 6 mm).
* **SCENE_N=3 ist eine andere Welt** als die Vorgabe mit vier Objekten. Die Tischzeilen dieses Laufs
  stammen aus anderen Szenen als das feste Probenset - deshalb steht oben die Tischablage auf den
  AKTUELLEN Zeilen.

# Verwandt

* [Die Policy lernt die Ablagehoehe - als Ort](/befunde/policy-lernt-hoehe-als-ort.md) - der erste Lauf
* [Der Teacher widersprach dem Stapel](/befunde/teacher-widerspricht-dem-stapel.md) - die Vorbedingung
* [Der Sockel braucht 80 mm Freiraum](/befunde/sockel-braucht-80mm-freiraum.md) - warum nur drei Objekte
* [Imitationspuffer](/befunde/imitationspuffer.md) - die Nullsummen-Diagnose des Puffers
