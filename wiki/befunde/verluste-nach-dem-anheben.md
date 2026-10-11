---
type: Befund
title: Verluste nach dem Anheben je Form - L und U setzen knapp daneben ab, weil die Hand den seitlichen Sitz des Objekts nicht ausgleicht; unterwegs verlieren die Zinkenformen nicht mehr als Wuerfel
description: Zerlegung von 760 Episoden, in denen das kommandierte Objekt angehoben wurde (GUI-Lauf 2026-10-09, Langlauf-A/B 2 x 300, Kontrolle der Wertprobe lokaler Griff). Nach dem Anheben liefern L 60 %, U 51 %, T 75 %, X 80 %, Wuerfel 69-77 %, Balken 85 %. Der formabhaengige Posten ist das knappe Danebensetzen (abgesenkt, 20-45 mm vom Ziel) - L 32 %, U 35 % gegen Wuerfel 11 % (p < 1e-5), in allen Quellen gleich gerichtet. Unterwegs verloren oder weit weg abgesetzt wird bei den Zinkenformen nicht haeufiger, eher seltener (8 % gegen Wuerfel 17 %). obj_blue ist der Balken, nicht ein Wuerfel (berichtigt am selben Tag). Die Hand steht in Treffern und Fehlablagen gleich weit vom Ziel (Median ~20 mm); den Ausschlag gibt, wo das Objekt in der Hand sitzt. Den mittleren Versatz entlang der Klaue gleicht die Policy aus, den seitlichen von L und U (Streuung 12-15 mm) nicht, und auf den Versatz der einzelnen Episode reagiert sie kaum (|r| <= 0,3).
tags: [act23, ablage, tragen, form, diagnose, versatz]
status: stable
evidenz: gemessen
ebene: langlauf
generated: { by: claude/opus-5.5, at: 2026-10-11T00:00:00Z }
sources:
  - id: gui
    resource: "log/pc_act23_2026-10-09_14-13-40_32344.txt (667 Ep, Nutzer-GUI, Fehlgriff-Kopf an)"
    title: GUI-Lauf 2026-10-09
  - id: lang
    resource: "Langlauf-A/B 2026-10-10, je 300 Ep mit und ohne Fehlgriff-Kopf (Scratchpad lang_kopf.log, lang_ohne.log)"
    title: Langlauf-A/B
  - id: lok
    resource: "Kontrollarm der Wertprobe lokaler Griff 2026-10-10/11, 100 Ep nur L/U/T/X (Scratchpad lok_kontrolle.log)"
    title: Wertprobe-Kontrolle
---

# Frage

Nutzerauftrag 2026-10-11: "Zerlege die Verluste nach dem Anheben nach Form." Anlass war die offene
Frage aus der [Wertprobe lokaler Griff](/befunde/lokaler-griff-wertprobe.md): Die Zinkenformen werden
meist angehoben und gehen erst danach verloren. Wo genau?

# Berichtigung (2026-10-11, selber Tag)

Die erste Fassung dieser Seite zaehlte `obj_blue` zu den Wuerfeln. Es ist der lange **Balken**
(68 x 18 mm, zur Laufzeit gestreckt, `LONG_HALF`). Unten ist alles mit Wuerfel = rot + gruen
neu gerechnet. Die Kernaussage zu L und U bleibt; geaendert hat sich das Verlieren unterwegs: Das
ist bei Wuerfeln HAEUFIGER als bei den Zinkenformen, nicht gleich haeufig.

# Abgrenzung "angehoben"

Das Ende-Etikett taugt dafuer nicht. `trug True` heisst nur "Druck in der geschlossenen Klaue bei
erhobener Hand", und das kann auch ein **anderes** Objekt sein. 63 Wuerfel-Episoden (dazu 17 Balken) haben `trug True`,
ohne dass das kommandierte Objekt je 14 mm hoch kam (L/U/T/X zusammen 25). In einer Stichprobe passte
die gesehene Groesse nicht zum Wuerfel (7 statt 12 mm). Vermutlich wurde ein Nachbar gegriffen; das
ist hier nicht weiter verfolgt.

Eine erste Auswertung nach Ende-Etikett ergab deshalb fuer Wuerfel scheinbar viele "Ablagen
daneben", 100-200 mm vom Ziel. Tatsaechlich war das eine leere oder fremde Klaue, die ueber dem Ziel
oeffnete.

Als **angehoben** gilt hier: Es gibt eine `[Ablage]`-Zeile. Sie entsteht nur, wenn die geschlossene
Klaue das kommandierte Objekt mehr als 14 mm ueber seine Ruhelage gebracht hat. Der Schnappschuss ist
der letzte solche Schritt, also der Moment, in dem das Objekt beim Absenken unter 14 mm faellt oder
aus der Hand geht. Es ist nicht der Moment des Oeffnens; danach bewegt sich die Hand im Median noch
12 mm (Vorbehalt wie in [Aufmerksamkeit](/fragen/aufmerksamkeit-objekt-ziel.md), Berichtigung
2026-09-28). Die Endlage und das Lieferurteil sind davon nicht betroffen.

1086 Episoden mit Ende-Zeile aus vier Quellen, davon 760 angehoben.

# Ergebnis: wohin die angehobenen Objekte gehen

| Form | angehoben | geliefert | nah daneben abgesetzt (<= 45 mm, < 20 mm hoch) | weit weg / aus der Hoehe |
|---|---|---|---|---|
| L | 120 | 60 % | **32 %** | 8 % |
| U | 108 | 51 % | **35 %** | 14 % |
| T | 116 | 75 % | 20 % | 5 % |
| X | 134 | 80 % | 13 % | 7 % |
| Wuerfel rot | 96 | 69 % | 14 % | 18 % |
| Wuerfel gruen | 91 | 77 % | 8 % | 15 % |
| Balken (obj_blue) | 95 | 85 % | 9 % | 5 % |

* **Nah daneben ist der formabhaengige Posten.** Gegen die Wuerfel (20 von 187): L p = 1e-5,
  U p = 7e-7, T p = 0,04, X p = 0,49 (Fisher; Bonferroni-Schranke fuer vier Formen 0,0125, L und U
  darunter). Je Quelle gleich gerichtet, L+U gegen Wuerfel: GUI 42 gegen 9 %, Langlauf mit Kopf 31
  gegen 12 %, ohne Kopf 27 gegen 15 % (einfachere Zaehlung, Anteile leicht anders als in der Tabelle);
  die Wertprobe-Kontrolle hatte keine Wuerfel. Der Balken setzt so selten daneben ab wie die Wuerfel
  (9 gegen 11 %).
* **Weit weg oder aus der Hoehe ist kein Zinken-Problem**: Zinken 40 von 478, Wuerfel 31 von 187
  (p = 0,003, die Wuerfel verlieren mehr). Fast alle diese Episoden enden im Stillstand, gut die
  Haelfte mit Fehlgriff-Eingriff; das Objekt liegt im Median 60-90 mm vom Ziel. Aus der Hoehe faellt
  kaum etwas: Nur 43 von 760 Schnappschuessen liegen hoeher als 20 mm, 27 davon nicht geliefert.
* Die Fehlablagen von L und U sind knapp: Beim Absenken liegt das Objekt 20-45 mm vom Ziel, am Ende
  29-32 mm (Liefergrenze 25 mm). Die Drift nach dem Absenken ist in Treffern und Fehlablagen gleich
  (12-13 mm).

# Warum: der Sitz in der Hand, nicht die Hand

Nah abgesetzte Episoden, Mediane in mm, Fehlablage / Treffer:

| Form | Objekt-Ziel | Hand-Ziel | Objekt-Hand | Hand <= 20 mm vom Ziel und trotzdem daneben |
|---|---|---|---|---|
| L | 27 / 20 | 18 / 20 (p = 0,88) | 16 / 9 (p = 0,006) | 20 von 38 |
| U | 30 / 18 | 19 / 19 (p = 0,73) | 17 / 18 | 19 von 38 |
| T | 26 / 20 | 24 / 22 | 20 / 14 | 10 von 23 |
| X | 34 / 18 | 22 / 21 | 16 / 17 | 8 von 18 |

**Die Hand steht in Treffern und Fehlablagen gleich weit vom Ziel.** Den Ausschlag gibt, ob sich
Hand-Ziel und Objekt-Hand aufheben oder addieren. Der Kosinus zwischen beiden Vektoren liegt bei
Treffern bei -0,4 bis -0,8 (sie heben sich teilweise auf), bei Fehlablagen von L, U und X bei 0 bis
+0,8 (sie addieren sich). Fuer L, U und X gilt das mit p <= 0,002, fuer T mit p = 0,03.

**Was die Policy ausgleicht und was nicht** (Regression Hand-Ziel auf Objekt-Hand im Klauenrahmen,
-1 = voller Ausgleich; dazu die Korrelation der einzelnen Episode):

| Form | entlang der Klaue | quer | Streuung Objekt-Hand quer | r quer (Episode) |
|---|---|---|---|---|
| Wuerfel (rot, gruen) | -0,66 / -0,77 | - | 5 mm | -0,05 / -0,18 |
| Balken | -1,27 | - | 3 mm | -0,38 |
| L | -0,62 | -0,28 | 11,6 mm | -0,30 |
| U | -0,52 | **-0,01** | **14,9 mm** | **-0,04** |
| T | -0,64 | -0,19 | 10,4 mm | -0,23 |

* Entlang der Klaue sitzt jedes Objekt rund 10 mm vor dem Reichpunkt. Diesen **mittleren** Versatz
  gleicht die Policy aus (beim Balken ganz, bei Wuerfeln zu zwei Dritteln).
* Quer dazu sitzen L und U je nach Episode bis 15 mm links oder rechts, weil an einer Zinke oder am
  Basisbalken gegriffen wird. Das gleicht die Policy nicht aus, bei U gar nicht (k = -0,01, r = -0,04).
* Auch entlang der Klaue folgt die Hand dem Versatz der einzelnen Episode kaum (|r| <= 0,3; einzige
  Ausnahme rot entlang, r = -0,51). Wuerfel-Fehlablagen sind die Episoden, in denen der Wuerfel
  ungewoehnlich tief in der Hand sitzt (Objekt-Hand entlang 18-26 statt 9-10 mm).

Lesart: Die Policy legt mit einem **festen**, gelernten Versatz ab, nicht mit dem Versatz der
laufenden Episode. Bei Wuerfeln und dem Balken reicht das, weil ihr Sitz kaum streut. Bei L und U streut der
seitliche Sitz mit dem Griffort um +-15 mm, und ein fester Versatz trifft dann ein Drittel der Faelle
knapp nicht.

# Einordnung

* Das bestaetigt und schaerft [Ablage im Netzbetrieb](/befunde/ablage-im-netzbetrieb.md) (380
  Episoden: "die Hand steht fast gleich gut; das Objekt sitzt quer in der Klaue"). Neu sind die Form
  als Trennlinie nach dem Anheben (L/U gegen Wuerfel), dass die Zinkenformen unterwegs nicht mehr verlieren und
  der Nachweis, dass die Hand nur den mittleren Versatz ausgleicht.
* Es widerspricht der [Wertprobe lokaler Griff](/befunde/lokaler-griff-wertprobe.md) nicht. Dort
  aenderte ein anderer Griffort die Querlage nicht (6 gegen 5 mm), also auch nicht diesen Posten.
* **Geschlossene Hebel in der Naehe:** Das Objekt in der Hand ansehen und die Hand um den gesehenen
  Versatz verschieben ist im FSM-Betrieb gemessen. Dort rueckte das Objekt naeher ans Ziel (21 -> 15
  mm), es gab aber keine Lieferungen mehr; die Blickkorrektur selbst zu lernen brachte ebenfalls
  nichts ([Aufmerksamkeit](/fragen/aufmerksamkeit-objekt-ziel.md)). Der Sitz in der Klaue als Ursache
  beim Zufassen ist geprueft und verworfen ([Ablage im Netzbetrieb](/befunde/ablage-im-netzbetrieb.md)).
  Gemessen wurde damals ueber alle Formen. Dass der Posten bei L und U sitzt und dort 12-15 mm streut,
  ist neu; ob das die alten Negative entkraeftet, ist nicht gemessen.
* **Offen und mit den vorhandenen Logs nicht pruefbar:** Der Agent waehlt seinen Griffpunkt selbst
  relativ zum gesehenen Blob. Er koennte also schon beim Zufassen wissen, wie weit die Objektmitte
  seitlich neben der Hand sitzen wird, ohne beim Tragen hinzusehen. Ob die Policy das als Eingang hat
  und ob dieser Wert den Versatz beim Absenken vorhersagt, steht nicht im Log.
  **Nachgemessen 2026-10-11, negativ:** der gesehene Versatz sagt die Ablage nicht vorher (sd 1-4
  mm, alle r n.s.), der wahre beim Zufassen schon (U quer r = 0,98) - siehe
  [Klauenlage und Griffversatz](/befunde/klauenlage-und-griffversatz.md).

# Verwandt

* [Ablage im Netzbetrieb](/befunde/ablage-im-netzbetrieb.md)
* [GUI-Lauf 2026-10-09](/befunde/gui-lauf-2026-10-09.md)
* [Wertprobe lokaler Griff](/befunde/lokaler-griff-wertprobe.md)
* [Aufmerksamkeit fuer Objekt und Ziel](/fragen/aufmerksamkeit-objekt-ziel.md)
* [U-Form-Engpass](/befunde/u-form-engpass.md)
