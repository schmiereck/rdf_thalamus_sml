---
type: Befund
title: 906 Episoden in der entkoppelten Welt - die Quote haelt, die Aneignung stockt weiter
description: Erster Langlauf mit ACT23_FARB_MISCHUNG=1. Die Quote liegt bei 53,1 Prozent, also auf dem alten Niveau - der im A/B gemessene Einbruch tritt nicht ein. Die Adressierung haelt ueber 906 Episoden (1,4 mm, 98,9 Prozent eindeutig), und eine reine FORM-Adresse liefert so gut wie eine Farb-Adresse. 97 Farb/Form-Kombinationen statt 7 - aber keine einzige neue Formklasse setzt sich fest.
tags: [act23, langlauf, farbe, generalisierung, selbstlernen]
status: stable
evidenz: gemessen
ebene: langlauf
generated: { by: claude/opus-5, at: 2026-09-11T13:00:00Z }
sources:
  - id: lauf
    resource: log/pc_act23_2026-09-10_09-10-01_8996.txt
    title: GUI-Langlauf des Nutzers, 906 Episoden, 26,8 h, Commit 515393d, entkoppelte Welt
---

# Behauptung

Der erste Langlauf in der [entkoppelten Welt](/befunde/farb-mischung.md) beantwortet drei Fragen,
und zwei davon anders als das A/B vom Vortag:

1. **Die Quote haelt.** 53,1 % ueber 906 Episoden - das alte Niveau (~52 %). Der im A/B
   gemessene Einbruch auf 47,6 % **tritt im Langlauf nicht ein.**
2. **Die Adressierung traegt dauerhaft.** Median 1,4 mm, 98,9 % eindeutig, privilegierter
   Rueckfall 7,4 %.
3. **Eine reine FORM-Adresse liefert so gut wie eine Farb-Adresse** (49,8 gegen 53,0 %,
   p = 0,46). Das ist eine Aussage, die es vor der Entkopplung gar nicht geben konnte.

**Die Selbst-Aneignung stockt trotzdem unveraendert** - und das ist der eigentliche Befund.

# Zahlen

    906 Episoden, 26,8 h, Quote 53,1 %, Median-Abstand 23 mm

    Quote je 100 Episoden
      49,0 | 54,0 | 52,0 | 62,0 | 59,0 | 46,0 | 56,0 | 54,0 | 47,0   [%]
      erste Haelfte 55,6 %   zweite Haelfte 50,6 %   Fisher p = 0,143

    Adressierung   Median 1,4 mm | >20 mm in 45 von 876 | eindeutig 866/876 = 98,9 %
    Rueckfall      67/906 = 7,4 %

    Welche Achse adressiert, und wie gut liefert sie
      nur Farbe    364 Ep = 40,2 %   Quote 53,0 %
      nur Form     253 Ep = 27,9 %   Quote 49,8 %
      Farbe + Form 288 Ep = 31,8 %   Quote 56,2 %
      Fisher "nur Form" gegen "nur Farbe": p = 0,4613

    Kombinationen (Koerper, Farbklasse)
      gesamt 97 verschiedene Paare (vor der Entkopplung: 7)
      je Koerper 9 bis 17 verschiedene Farbklassen
      Verlauf: 4 -> 62 (Ep 150) -> 77 -> 87 -> 89 -> 92 -> 97

    Selbst-Aneignung
      Formklassen am Anfang: neu-9, neu-13, neu-34, neu-285
      Formklassen am Ende:   neu-9, neu-13, neu-34, neu-285      -- unveraendert
      13 Klassen geboren (neu-369 bis neu-381), alle mit
         "kein Knopf zu vergeben -- der Probe-Koerper ist schon gebunden"
      unzuordenbare Sichtungen  16 -> 227, LINEAR (~0,23 je Episode)
      Wiedererkennung, erste 200 gegen letzte 200 Episoden
         neu-9   40,0 -> 36,1 %    neu-13   1,8 ->  8,2 %
         neu-34  33,2 -> 36,1 %    neu-285 45,0 -> 32,8 %

    3 NEUE FARBKLASSEN geboren: farbe-61, farbe-62, farbe-63 (letzte an obj_U gebunden)

# Bewertung

**Zur Quote: mein A/B-Befund war der Ausreisser, nicht der Langlauf.** Im
[Farb-Mischungs-A/B](/befunde/farb-mischung.md) fiel die Quote gepoolt auf 47,6 %, getragen fast
allein von einem Arm (63,8 -> 45,5 %). Ueber 906 Episoden liegt sie bei 53,1 %. Die dort
formulierte Warnung - die Seeds widersprechen einander, der Vergleichsarm lag ueber dem
Ueblichen - hat sich als richtig erwiesen. **Die entkoppelte Welt kostet keine Quote.**

**Die Form-Achse traegt.** 253 Episoden wurden ueber eine reine Formklasse adressiert, ohne
Farbangabe, und lieferten 49,8 % - statistisch nicht von der Farb-Achse zu unterscheiden. Vor der
Entkopplung war "nur Form" inhaltlich dieselbe Information wie die Farbe; jetzt ist es eine
eigenstaendige Achse, und sie funktioniert.

**Die Kombinationsvielfalt ist da: 97 statt 7 Paare**, jeder Koerper in 9-17 Farbklassen gesehen.
Das Material fuer Generalisierung liegt also vor - zum ersten Mal.

**Und genau deshalb wiegt der Aneignungs-Befund schwerer als zuvor.** 13 neue Formklassen
geboren, **keine einzige** setzt sich fest; der Bestand am Ende ist identisch mit dem am Anfang;
die unzuordenbaren Sichtungen wachsen linear auf 227. Das ist zifferngenau dasselbe Muster wie in
[Selbst-Aneignung stockt](/befunde/selbstaneignung-stockt.md) - **nur jetzt kann es nicht mehr
daran liegen, dass es nichts Neues zu sehen gab.** Es gab 97 Kombinationen zu sehen.

Alle 13 Geburten tragen dieselbe Begruendung: *"kein Knopf zu vergeben - der Probe-Koerper ist
schon gebunden"*. `_register_open_class` steigt aus, sobald `NOVEL_BODY` gebunden ist, und
`_try_bind` prueft ausschliesslich Klassen, die auf **diesem einen** Koerper sitzen - die ganze
Vergabemaschinerie haengt an einem reservierten Probe-Koerper, und der ist seit Langem vergeben.

**Aber die Klassen sind nicht unbrauchbar, und das ist der Punkt:**

    Klasse    Alter  max wiedererkannt   Zaehler sagt   verhungert nach
    neu-369     25        75 %           kommandiert 0x      26 Ep
    neu-373     60        71 %           kommandiert 0x     229 Ep
    neu-376     40        67 %           kommandiert 0x      41 Ep
    neu-371     24        50 %           kommandiert 0x      25 Ep
    neu-374     24        50 %           kommandiert 0x      25 Ep
    neu-375     24        50 %           kommandiert 0x      25 Ep

Sechs der dreizehn erreichen 50-75 % Wiedererkennung - sie **funktionieren** und verhungern
trotzdem.

**Kein Lernfortschritt ueber den Lauf** (55,6 -> 50,6 %, p = 0,14, eher leicht fallend). Vierte
unabhaengige Bestaetigung von [1109 Episoden ohne
Fortschritt](/befunde/langlauf-ohne-fortschritt.md), diesmal in der neuen Welt.

# Der Zaehler hat einen blinden Fleck - und das entwertet eine alte Aussage

`neu-373` steht in **allen 363** Aneignungszeilen mit `kommandiert 0x`. Dasselbe Protokoll zeigt
aber fuenf Kommandos darauf:

    [Auto 409] neu-373 + mittel      [Auto 511] farbe-4 + neu-373
    [Auto 517] farbe-2 + neu-373     [Auto 610] farbe-5 + neu-373
    [Auto 614] neu-373 + mittel

Ursache am Code: der Zaehler liest `state.SHAPE_KEY.get(body)` (`pc_act23.py:4547`) - also **nur
den Knopf-Pfad**. Das [Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md) laeuft ueber
`state.EIGENSCHAFT` und wird nicht mitgezaehlt. Eine Klasse, die ausschliesslich ueber
Eigenschaften adressiert wird, gilt dem Zaehler als **nie kommandiert**.

Damit ist "keine je kommandiert" aus [Selbst-Aneignung
stockt](/befunde/selbstaneignung-stockt.md) fuer jeden Lauf **mit** Eigenschafts-Kommando nicht
mehr belastbar. Die dortigen Pruefzeilen stammen aus der Zeit davor und bleiben gueltig - wer die
Aussage heute nachmisst, misst am blinden Fleck vorbei.

**Ein Hinweis, keine Messung:** `neu-373` ist die einzige Klasse mit mehreren Kommandos und die
einzige, die 229 statt ~25 Episoden lebte; die naechstlaengsten (41, 26, 26 Ep) hatten keine. Ob
Kommandieren am Leben haelt, ist damit **nicht** gezeigt - n = 1, und die Richtung koennte
umgekehrt sein (eine gut wiedererkannte Klasse wird eher adressiert). Pruefbar, sobald der
Zaehler beide Pfade sieht.

# Ein unerwarteter Nebenbefund

**Drei neue FARBklassen wurden geboren** (farbe-61/62/63), obwohl die Mischung nur vorhandene
Farben permutiert. Erwartet waren null. Die Erklaerung liegt nahe, ist aber **nicht gemessen**:
die gerenderte Chroma haengt nicht nur an der RGBA, sondern an Form, Lage und Schattenwurf -
dieselbe Farbe auf einer anderen Form ergibt eine leicht andere Chroma. Das ist dieselbe Lehre
wie bei der obj_Y-Aneignung ("die GERENDERTE Chroma zaehlt").

Bemerkenswert: **farbe-63 wurde an obj_U gebunden** - also hat die entkoppelte Welt tatsaechlich
eine Aneignung ausgeloest, die in der gekoppelten nicht stattgefunden haette. Bei den FARBEN
funktioniert, was bei den FORMEN stockt.

# Fallen

* **Der Lauf schrieb in die Live-Zustandsdatei** (`STATE_PATH=None`, normaler GUI-Betrieb). Der
  Zustand ist jetzt `ad9d768c`, vorher `98a293f2`. Wer aeltere Messungen dieser Reihe
  nachvollziehen will, braucht den alten Stand.
* **Der letzte Block umfasst nur 6 Episoden** (33,3 %) und traegt nichts.
* **Die Objektquoten sind keine Aussage ueber Formen mehr.** obj_X liegt mit 59,5 % vorn, obj_U
  mit 45,0 % hinten - aber jedes Objekt hatte in diesem Lauf 9-17 verschiedene Farben, die
  Zahlen mischen also Form und wechselnde Farbe.

# Was daraus folgt

Der schaerfste offene Punkt hat sich verschoben: nicht mehr "der Agent sieht zu wenig Neues",
sondern **"was er als neu erkennt, kann er nicht in Benutzung nehmen"**. Sechs der dreizehn
Geburten sterben bei 50-75 % Wiedererkennung - mitten im Funktionieren.

Zwei kleine Schritte folgen daraus, und beide sollten **vor** einem groesseren Umbau kommen:

1. **Den Zaehler beide Pfade sehen lassen** (`SHAPE_KEY` **und** `EIGENSCHAFT`). Solange er nur
   den Knopf sieht, misst jede kuenftige Aneignungsaussage am blinden Fleck vorbei - und die
   Frage "haelt Kommandieren eine Klasse am Leben" ist gar nicht erst stellbar.
2. **Die Vergabe vom Probe-Koerper loesen.** Eine Klasse, die auf *irgendeinem* Koerper
   wiederholt bestaetigt wird, koennte kommandierbar werden; ueber das Eigenschafts-Kommando
   braucht sie dafuer nicht einmal einen Knopf.

# Verwandt

* [Farbe und Form entkoppelt](/befunde/farb-mischung.md) - die Welt, in der das gemessen wurde;
  dessen Quoten-Befund ist hiermit relativiert
* [Selbst-Aneignung stockt](/befunde/selbstaneignung-stockt.md) - dasselbe Muster, jetzt ohne die
  Ausrede "nichts Neues da"
* [1109 Episoden ohne Lernfortschritt](/befunde/langlauf-ohne-fortschritt.md)
* [Formklassen-Lebenszyklus](/mechanismen/formklassen-lebenszyklus.md)
