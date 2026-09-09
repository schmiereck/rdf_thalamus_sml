---
type: Befund
title: Der Keim im Rueckfall schliesst die Luecke - bringt nichts und ist wieder aus
description: Der privilegierte Rueckfall-Keim schliesst die Luecke vollstaendig (Episoden ohne Keim 10 -> 0), bringt aber nichts Messbares (Fehlstart 2,9 -> 4,2 Prozent p = 0,47, Quote 52,9 -> 53,6 Prozent p = 0,93). Weil er das Privileg in den Blick-Regelkreis traegt und sich nicht bezahlt macht, steht die Vorgabe wieder auf 0. Der Grund fuer die Wirkungslosigkeit ist der Ertrag: die Rueckfall-Episoden sind Verschmelzungsfaelle.
tags: [act23, wahrnehmung, tracker, negativ]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-09T14:00:00Z }
sources:
  - id: rf
    resource: "Zwei kopflose Steuerungslaeufe je ~120 Episoden (Seed 7 und 23) mit ACT23_KEIM_RUECKFALL=1, aus dem Schnappschuss 98a293f2"
    title: Rueckfall-Arme
  - id: basis
    resource: "log/pc_act23_2026-09-09_06-37-31_3872.txt (Seed 7) und ..._2228.txt (Seed 23), ACT23_KEIM_FIX=1 ohne Rueckfall-Keim, derselbe Schnappschuss"
    title: Vergleichsarme aus dem Keim-Fix-A/B
---

# Anlass

Restluecke aus [Keim-Fix, A/B](/befunde/keim-fix-ab.md): trifft die Eigenschafts-Adressierung
nichts, gibt `perceive()` die **privilegierte wahre Lage** als Greifziel zurueck und
veroeffentlichte dabei **keinen Keim** - der Tracker startete in diesen 3-5 % der Episoden wieder
blind. Nutzerauftrag: *"Der Rueckfall soll auch einen Keim setzen."*

# Behauptung

Die Luecke ist geschlossen: **Episoden ohne Keim 10 -> 0.** Ein Nutzen ist **nicht nachweisbar**,
weder bei den Fehlstarts (2,9 -> 4,2 %, p = 0,47) noch bei der Quote (52,9 -> 53,6 %, p = 0,93).

Der Grund dafuer ist der eigentliche Ertrag dieser Messung: **die Rueckfall-Episoden sind
Verschmelzungsfaelle.** Gegen einen Blob, der zwei Koerper zu einem verschmilzt, hilft kein
Ortsanker - der Keim zeigt korrekt auf das gemeinte Objekt, aber es gibt keine Detektion, die
nur dieses Objekt waere.

# Zahlen

    Arm          Ep  ohne Keim  priv. Keim | mehrdeutig Fehlst. | 1 Kand. Fehlst. | Quote  | fremd>5%
    s7  RF aus  120          6           0 |  14   1 =  7 %     | 106  1 = 1 %    | 55,8 % |  9,2 %
    s7  RF an   119          0           4 |  23   3 = 13 %     |  96  3 = 3 %    | 55,5 % |  7,6 %
    s23 RF aus  120          4           0 |  16   1 =  6 %     | 104  4 = 4 %    | 50,0 % |  8,3 %
    s23 RF an   120          0           3 |  19   1 =  5 %     | 101  3 = 3 %    | 51,7 % |  5,8 %

    gepoolt   RF aus   Fehlstart  7/240 = 2,9 %   Quote 127/240 = 52,9 %
              RF an    Fehlstart 10/239 = 4,2 %   Quote 128/239 = 53,6 %
              Fisher p (Fehlstart) = 0,472   Fisher p (Quote) = 0,927

Die sieben privilegierten Keime einzeln - **Start auf**, in Klammern der Abstand des gewaehlten
Blobs zu diesem Koerper, danach der Abstand zum gemeinten:

    obj_U      2 Kand. -> obj_T     (21 mm)   eigenes 23 mm    FALSCH
    obj_L      2 Kand. -> obj_U     (19 mm)   eigenes 23 mm    FALSCH
    obj_green  1 Kand. -> obj_red   ( 9 mm)                    FALSCH
    obj_green  2 Kand. -> obj_red   (12 mm)                    FALSCH
    obj_L      1 Kand. -> obj_L     (11 mm)                    RICHTIG
    obj_U      1 Kand. -> obj_U     ( 5 mm)                    RICHTIG
    obj_green  2 Kand. -> obj_green ( 2 mm)                    RICHTIG

# Bewertung

* **Der Auftrag ist erfuellt**, und das ist der einzige belegte Effekt: keine Episode startet
  mehr ohne Keim.
* **21 gegen 23 mm, 19 gegen 23 mm** - in den beiden ersten Faellen sitzt der gewaehlte Blob
  fast genau **zwischen** zwei Koerpern. Das ist die Signatur eines verschmolzenen Blobs, nicht
  die eines Muenzwurfs. Der Keim hat richtig gezeigt; die Wahrnehmung hatte nichts Richtiges
  anzubieten.
* **Daraus eine Hypothese, die zum Mechanismus passt:** der privilegierte Rueckfall ist faktisch
  ein **Verschmelzungs-Melder**. `finde_nach_eigenschaften` findet genau dann nichts Passendes,
  wenn der Blob mit einem Nachbarn verschmolzen ist und Form- oder Farbklasse dadurch kippen -
  derselbe Mechanismus, den [Wahrnehmungs-Splits](/mechanismen/wahrnehmungs-splits.md)
  beschreibt. **Nicht gemessen**, aber die Abstaende in allen vier Fehlstarts stuetzen es.
* **Ein unerwarteter Nebeneffekt, guenstig:** mit gesetztem `mem["xy"]` greift die 5-cm-Sprung-
  schranke des Trackers schon im ERSTEN Bild. Liegt der beste gleichklassige Blob weiter als
  5 cm neben der wahren Lage, wird er gar nicht erst uebernommen - der Tracker rastet dann auf
  nichts ein statt auf dem falschen Koerper. Vorher gab es diese Schranke im Erstbild nicht.

# Der Ehrlichkeitsvorbehalt

Dieser Keim ist **privilegiert**: er kommt aus `sim.obj_pos(body)`. Das Greifziel war es in
diesem Zweig ohnehin schon; neu ist, dass das Privileg auch den **Blick-Regelkreis** anfaehrt.
Das laeuft dem [Projektziel](/ziel.md) zuwider ("keine Positionen, die von mathematischen
Algorithmen erkannt und eingespeist werden") und ist deshalb im Protokoll kenntlich gemacht:
`perception.seed_priv` faerbt die Diagnosezeile zu `Keim JA (PRIVILEGIERT)`. Ohne diese
Markierung haette die Keim-Diagnose ab jetzt Privileg als saubere Wahrnehmung ausgewiesen.

`px` bleibt bewusst `None` - fuer die Bildkoordinate gaebe es keine ehrliche Quelle, sie
muesste durch die Homographie zurueckprojiziert werden und truege das Privileg noch tiefer in
den Blickpfad. Bis zum ersten Treffer steht die Fovea still.

# Was das fuer die Grenzen der Fallzahl heisst

Der Rueckfall betrifft 3-5 % der Episoden, also 7 Faelle in 239 Episoden. Fuer die direkte
Zielgroesse *"Fehlstart unter Rueckfall-Episoden"* ist das **keine auswertbare Stichprobe** -
das war vor der Messung angesagt und hat sich bestaetigt. Die Gesamtzahlen (Fehlstart, Quote)
vergleichen ausserdem zwei auseinandergelaufene Trajektorien, siehe
[Zwei Laeufe sind dieselbe Rechnung](/befunde/laeufe-sind-reproduzierbar.md).

**Belegt ist damit genau eines: die Luecke ist zu. Ein Nutzen ist es nicht.**

# Folgen: gebaut, gemessen, wieder abgeschaltet

**`ACT23_KEIM_RUECKFALL` steht auf `0`** (Nutzerentscheid 2026-09-09, nach der Messung). Die
Abwaegung ist damit vollstaendig protokolliert: kein Schaden gemessen, **kein Nutzen gemessen**,
aber ein Privileg mehr im Blick-Regelkreis. Wo nichts zu gewinnen ist, wiegt der Verstoss gegen
[das Projektziel](/ziel.md) schwerer.

Der Schalter bleibt im Code stehen, damit die Messung reproduzierbar bleibt - eingeschaltet
markiert `perception.seed_priv` den Keim, und die Diagnosezeile druckt
`Keim JA (PRIVILEGIERT)`.

**Das ist ein Muster, kein Einzelfall:** eine Aenderung, die eine Luecke sauber schliesst, ist
damit noch nicht begruendet. Die Luecke war real und ist es weiterhin - sie kostet nur nichts.

Der lohnendere Weg fuehrt ueber die Ursache: waeren die Blobs getrennt, fiele der Rueckfall gar
nicht erst an. Siehe [Wahrnehmungs-Splits](/mechanismen/wahrnehmungs-splits.md) und die noch
ungemessene Frage, ab welchem Nachbarabstand der Split versagt
([offene Faeden](/fragen/offene-faeden-act23.md)).

# Verwandt

* [Keim-Fix, A/B](/befunde/keim-fix-ab.md) - die Restluecke stammt von dort
* [Wahrnehmungs-Splits](/mechanismen/wahrnehmungs-splits.md) - die vermutete eigentliche Ursache
* [Projektziel](/ziel.md) - warum ein privilegierter Keim ein Vorbehalt ist
