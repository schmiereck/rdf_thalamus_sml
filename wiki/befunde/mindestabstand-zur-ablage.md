---
type: Befund
title: Der Arm hat einen Mindestabstand von rund 37 mm - und die Ursache ist die Regel, die das Stapeln verbietet
description: Vier Arme je 100 Episoden mit Ablageabstand 30, 50, 70 und 90 mm. Bei 90 mm trifft der Arm den befohlenen Abstand auf 0,5 mm genau; bei 30 mm legt er 20 mm zu weit weg ab, in 93 Prozent der Faelle zu weit. Ueber alle 254 Ablagen landen nur 1,2 Prozent naeher als 20 mm an einem Koerper, das 5. Perzentil liegt bei 37,6 mm. Die Drift NACH dem Loslassen aendert sich dabei nicht (rho = 0,013) - das Objekt wird also nicht weggestossen, sondern gar nicht erst hingebracht. Die naechstliegende Ursache ist die Saeuberungsregel selbst: sie hat ueber tausend Episoden lang garantiert, dass NIE ein Ziel naeher als 50 mm an einem Koerper lag.
tags: [act23, ablage, stapeln, policy, ab]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-17T00:00:00Z }
sources:
  - id: ab
    resource: "Vier kopflose Laeufe je 100 Episoden aus identischen Kopien von act23_state.pkl (ad9d768c), Seed 4242, ACT23_ZIEL_ADRESSE=1, ACT16_ZIEL_SAEUBERN=0, ACT23_ZIEL_ABSTAND 0.03/0.05/0.07/0.09"
    title: Dosis-Wirkung des Ablageabstands
  - id: anlass
    resource: /mechanismen/stufe2-vorbereitet.md
    title: Punkt 4 der offenen Liste
---

# Die Frage

Stapeln verlangt **per Definition** ein Ziel, an dem ein Koerper steht - Abstand 0 mm.
[Die Zieladresse traegt](/befunde/ziel-als-adresse-gemessen.md) hatte gezeigt, dass ein Ziel
50 mm neben einem Koerper die Quote drueckt. **Haelt der Transport ein besetztes Ziel aus, und
wenn nicht, woran scheitert er?** Gemessen als Dosis-Wirkung ueber den Ablageabstand, nicht als
Ja/Nein - der interessante Punkt liegt bei 0 und ist nur ueber die Kurve erreichbar.

Dafuer musste die Saeuberungsregel weichen (`ACT16_ZIEL_SAEUBERN=0`, in allen vier Armen): sie
blaest jedes Ziel auf 50 mm Abstand zu jedem Koerper auf, eine Vorgabe von 30 mm waere still zu
50 mm geworden und die Kurve waere flach gewesen, ohne dass man es sieht.

# Zahlen

    Soll   Ep  gegriffen  abgelegt  geliefert  Quote | seitl. Med  p75   p90 | Adresse
    30mm  100      80        61        38     38,0 % |   25,0     31,0  55,0 | 86/99
    50mm  100      83        60        47     47,0 % |   25,0     27,0  43,4 | 90/97
    70mm  100      90        70        48     48,0 % |   25,0     33,0  50,0 | 93/99
    90mm  100      86        66        51     51,0 % |   25,0     32,8  39,0 | 92/99

    Quote: kein paarweiser Vergleich signifikant (bestes p = 0,087 fuer 30 gegen 90 mm,
           Bonferroni-Schranke 0,0083); Trend rho = +0,090, p = 0,073.

Die Quote sagt also **nichts Belastbares**. Die Ablage sagt sehr viel:

    UEBERSCHUSS -- wie weit die Endlage vom Bezugskoerper entfernt ist, MINUS dem befohlenen Abstand

      Soll 30mm   Median  +20,0 mm    zu weit in  93,3 %   n=60
      Soll 50mm   Median   +7,0 mm    zu weit in  71,2 %   n=59
      Soll 70mm   Median   +8,0 mm    zu weit in  62,3 %   n=69
      Soll 90mm   Median   -0,5 mm    zu weit in  48,5 %   n=66

      Trend ueber den Abstand: Spearman rho = -0,389, p = 1,3e-10
      30 gegen 90 mm:          Mann-Whitney   p = 3,2e-09

**Bei 90 mm trifft der Arm den befohlenen Abstand auf einen halben Millimeter genau**, und die
Abweichung ist sauber symmetrisch (48,5 % zu weit, also die Haelfte). Je naeher das Ziel an den
Koerper rueckt, desto systematischer legt er zu weit weg ab - bei 30 mm in **93 % der Faelle**.

    WIE NAH KOMMT DER ARM UEBERHAUPT?  (alle 254 Ablagen aus allen vier Armen)

      naeher als 20 mm am Bezugskoerper    1,2 %  (3)
      naeher als 25 mm                     1,6 %  (4)
      naeher als 30 mm                     2,4 %  (6)
      naeher als 35 mm                     4,3 %  (11)
      naeher als 40 mm                     8,7 %  (22)
      naeher als 50 mm                    21,3 %  (54)

      5. Perzentil 37,6 mm

> **Es ist kein Zielfehler, es ist ein MINDESTABSTAND.** Der Arm legt nicht ungenau ab - er legt
> genau ab, solange das Ziel weit genug weg ist, und weigert sich naeher als rund 37 mm an einen
> vorhandenen Koerper heranzugehen.

# Woran es NICHT liegt

**Nicht an einem Stoss nach dem Loslassen.** Die Drift nach dem Oeffnen der Klaue ist in allen
vier Armen dieselbe - Median 13,0 / 13,5 / 13,5 / 14,0 mm, Trend **rho = +0,013, p = 0,83**. Waere
der Nachbar ein mechanisches Hindernis, das das abgelegte Objekt wegstoesst, muesste die Drift bei
30 mm aufgehen. Sie tut es nicht.

> **Das Objekt wird nicht weggestossen, sondern gar nicht erst hingebracht.** Der Fehler steht
> schon beim Oeffnen der Klaue da.

**Nicht hauptsaechlich an der Wahrnehmung.** Der Glaubensfehler beim Loslassen (|Glaube - Wahrheit|
des getragenen Objekts) liegt in allen Armen bei Median 12,5-16 mm. Er traegt einen Nebeneffekt -
grobe Glaubensfehler >25 mm sind bei 30 mm Soll haeufiger (19,7 %) als bei 90 mm (7,6 %) -, aber
er erklaert keinen 20-mm-Versatz in 93 % der Ablagen.

**Nicht an der Adressierung.** 86 bis 93 von 99 Zieladressen loesen eindeutig auf, ohne Trend.

# Die naechstliegende Ursache: die Regel hat ihre eigenen Daten verhindert

`run_combined` saeubert seit jeher jedes uebergebene Ziel und schiebt es von JEDEM Koerper auf
0,05 m weg; das Zufallsziel wird ueber `clear(tgt, OBJS, 0.05)` gezogen. **Damit lag in der
gesamten Vorgeschichte - 1053 Episoden DAgger und jede Selbst-Imitation - kein einziges Ablageziel
naeher als 50 mm an einem Koerper.** Das ist keine Vermutung, sondern die Bauart des Codes.

Die Policy hat die Situation also **nie gesehen**. Der gemessene Boden von ~37 mm ist dann genau
das, was man erwartet: etwas Extrapolation ueber den Trainingsrand hinaus, und dann ist Schluss.

> **Die Regel, die das Stapeln verbietet, ist dieselbe, die die Daten verhindert hat, mit denen man
> es lernen koennte.** Das ist die guenstigste Form eines Engpasses: sie steht auf einem Schalter,
> und nach [Laufzeitregeln](/mechanismen/laufzeit-regeln.md) ist der zulaessige Weg genau dieser -
> die Regel im TRAINING fallen lassen, damit der Teacher nahe Ablagen vorfuehrt, und sie zur
> Testzeit nicht wieder einschalten.

Diese Lesart ist **nicht bewiesen**. Der Gegenkandidat ist die Mechanik: die Klaue ist breit, und
neben einem 24-mm-Koerper auf Greifhoehe abzusenken heisst, mit einem Finger in ihn hineinzufahren.
Beide Erklaerungen sagen denselben Boden vorher. Sie trennen sich an einer billigen Messung:
**bewegt sich der Bezugskoerper?** Wird er beim Anfahren verschoben, ist es die Mechanik; bleibt er
stehen, waehrend der Arm vorher abbricht, ist es die Trainingsverteilung. Das ist nicht
protokolliert und die naechste Messung dieser Linie.

# Was das fuer das Stapeln heisst

**Bei 0 mm ist heute nichts zu holen** - der Arm kommt gemessen nicht unter ~37 mm. Die Kurve
extrapoliert, sie misst diesen Punkt nicht; ein 0-mm-Arm braucht `ACT16_GOAL_Z`, sonst faehrt die
Klaue auf Greifhoehe in den Bezugskoerper.

**Der Sockel loest das nicht von allein.** Er ist 70 mm breit, sein Rand liegt 35 mm von der Mitte.
Ein Objekt, das nicht naeher als 37 mm an die SOCKELMITTE kommt, landet auf dem Rand oder daneben.
Die breite Auflage kauft Toleranz gegen Streuung, nicht gegen einen systematischen Mindestabstand.

# Eine Nicht-Reproduktion, die festgehalten gehoert

[Die Zieladresse traegt](/befunde/ziel-als-adresse-gemessen.md) mass bei 50 mm einen Schwanz von
**p90 = 86,0 mm** im seitlichen Ablagefehler. Hier sind es bei 50 mm **43,4 mm**. Drei Dinge
unterscheiden die Laeufe: die Saeuberungsregel (dort AN, hier AUS), die XML (hier mit dem Sockel,
und nach den [Invarianten](/mechanismen/invarianten.md) sind Laeufe ueber eine XML-Aenderung
hinweg nicht vergleichbar) und 140 gegen 100 Episoden.

**Der 86-mm-Schwanz reproduziert sich nicht.** Die Aussage jener Seite, die HIER bestaetigt wird,
ist die andere: das Objekt wird falsch hingetragen und nicht weggestossen - die Drift ist in allen
Armen gleich. Ein Kandidat fuer den Unterschied: bei eingeschalteter Saeuberung liegt Soll 50 mm
genau auf der Schwelle, die Regel feuert also staendig und versetzt das Ziel sprunghaft - moeglich,
dass der Schwanz zum Teil die Regel selbst war. Ungemessen.

# Fallen

* **Ein Seed je Arm.** Die Quotenzahlen tragen nichts (bestes p = 0,087). Die Abstandsaussage
  traegt (p = 1,3e-10 ueber 254 Ablagen), weil sie je Ablage zaehlt, nicht je Lauf.
* **0 mm ist nicht gemessen**, sondern extrapoliert.
* **Der Bezugskoerper ist immer ein normaler Koerper** (~24 mm), nie der Sockel. Abstaende sind
  Mittelpunkt zu Mittelpunkt.
* **Die Saeuberung war in allen vier Armen aus** - der Vergleich zu einem Arm MIT Regel fehlt.
* **`ACT16_ZIEL_SAEUBERN` bleibt Vorgabe 1**, bis der Nutzen der Abschaltung gemessen ist.

# Verwandt

* [Stufe 2 vorbereitet](/mechanismen/stufe2-vorbereitet.md) - die Liste, deren Punkt 4 das hier ist
* [Die Zieladresse traegt](/befunde/ziel-als-adresse-gemessen.md) - der Vorgaenger, dessen Schwanz sich nicht reproduziert
* [Laufzeitregeln](/mechanismen/laufzeit-regeln.md) - warum eine Regel im Training erlaubt ist und zur Testzeit nicht
* [Merkmale kommen zu spaet](/befunde/merkmale-kommen-zu-spaet.md) - dasselbe Muster: der Puffer enthaelt nicht, was man braucht
* [Ablage und Platzieren](/befunde/ablage-und-platzieren.md) - woher die 25 mm seitlicher Fehler stammen
