---
type: Befund
title: Eine dauerhafte Adresse darf keine Farbe nennen - die Welt faerbt jede Episode um
description: Der entscheidende Versuch sollte trennen, ob die Formachse die gute ist oder obj_T der leichtere Koerper. Er hat beides widerlegt. Die Formachse zu erzwingen aendert nichts (0 von 18 gegen 0 von 22 brauchbaren Adressen), die Farbachse zu STREICHEN aendert alles (6 von 14, Median 141 mm auf 1,0 mm, null grobe Fehler). ACT23_FARB_MISCHUNG faerbt jede Episode um; eine eingefrorene Adresse trifft damit nicht den Koerper, sondern was gerade diese Farbe traegt.
tags: [act23, kommando, latent, selbstlernen, ab]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-16T00:00:00Z }
sources:
  - id: ab
    resource: "Drei frische kopflose Laeufe (ACT23_FRESH=1) je 140 Episoden, Seed 4242, NOVEL_WEITER=1 EIG_DIREKT=1 EIG_STETIG=1"
    title: wuerfel / formzuerst / ohnefarbe
  - id: vorher
    resource: /befunde/adresse-ohne-klasse-gemessen.md
    title: Der Lauf davor, dessen Ursachen-Lesart hier widerlegt wird
---

# Die Frage, mit der der Versuch startete

Der [Lauf davor](/befunde/adresse-ohne-klasse-gemessen.md) hatte zwei Direkt-Adressen mit
gegensaetzlichem Schicksal:

    obj_T   (None, ~gesehen, None)    16 von 22 = 72,7 %    5,0 mm,  0 grobe Fehler
    obj_X   (farbe-1, None, dick)      1 von 18 =  5,6 %   141,3 mm, 1 grober Fehler

Die eine nennt nur die Formachse, die andere nennt sie gar nicht - aber es ist auch ein anderer
Koerper. **Achse oder Koerper?** `ACT23_EIG_DIREKT_FORM` sollte es trennen: die Adresse beginnt
bei der Formachse allein und legt weitere nur nach, solange sie nicht eindeutig ist.

# Die Antwort war: weder noch

    Arm          Koerper  Adresse                  auf  rue   Median  grob   BRAUCHBAR
    wuerfel      obj_T    (None, ~gesehen, None)    16    6    5,0 mm    0   16/22 = 72,7 %
    wuerfel      obj_X    (farbe-1, None, dick)      1   17  141,3 mm    1    0/18 =  0,0 %
    formzuerst   obj_T    (None, ~gesehen, None)    13    7    5,4 mm    0   13/20 = 65,0 %
    formzuerst   obj_X    (farbe-1, cube, dick)      6   16   61,4 mm    6    0/22 =  0,0 %
    ohnefarbe    obj_T    (None, ~gesehen, None)    13    8    5,1 mm    0   13/21 = 61,9 %
    ohnefarbe    obj_X    (None,    cube, dick)      6    8    1,0 mm    0    6/14 = 42,9 %

    obj_X brauchbar:  0/18  gegen  0/22   p = 1,00       (Formachse erzwungen)
                      0/18  gegen  6/14   p = 3,3e-3     (Farbachse gestrichen)
                      0/22  gegen  6/14   p = 1,5e-3

**Die Formachse zu erzwingen aendert nichts.** Sie hebt die Aufloesung von 5,6 auf 27,3 % - und
**alle sechs Aufloesungen sind grobe Fehler**. Die Adresse findet oefter etwas und jedes Mal das
Falsche.

**Die Farbachse zu streichen aendert alles.** Median 141,3 mm -> **1,0 mm**, grobe Fehler 1 -> 0,
brauchbare Adressen 0 -> 6. `obj_T` liegt in allen drei Armen bei 62-73 % und dient als Kontrolle:
seine Adresse ist ueberall dieselbe, die Arme sind also vergleichbar.

# Warum

Jede Aufloesung von obj_X meldete **"1 Treffer"** - eindeutig - und zeigte trotzdem 60 bis 140 mm
daneben, immer auf dieselben Punkte. Und im Protokoll steht 140-mal:

    [Farbe] neu gemischt: obj_red=farbe-1

**`ACT23_FARB_MISCHUNG` ist Vorgabe 1 und faerbt jede Episode neu um.** Eine Adresse, die
`farbe-1` nennt, trifft deshalb nicht den Koerper, sondern *"was gerade farbe-1 ist"* - und das
ist von Episode zu Episode ein anderer.

**Der Docstring von `_farbe_wuerfeln` sagt es seit jeher**, nur fuer den anderen Pfad:

> *"eine nach dem Umfaerben gewuerfelte Eigenschafts-Adresse muss die NEUE Farbklasse tragen,
> sonst adressiert das Kommando eine Farbe, die es nicht mehr gibt."*

`_auto_eig_umschreiben` wuerfelt JEDE Episode neu und ist deshalb nie betroffen. Eine
Direkt-Adresse steht den ganzen Lauf und ist es immer.

> **Die Regel, und sie ist allgemeiner als dieser Schalter:** eine dauerhafte Adresse darf nur
> Achsen nennen, die EIGENSCHAFTEN DES KOERPERS sind. In der gemischten Welt ist die Farbe
> ausdruecklich keine - sie wurde genau deshalb entkoppelt, *"damit der Farbpfad die Identitaet
> nicht mehr mittraegt"*.

Gebaut ist es entsprechend: solange `FARB_MISCHUNG` laeuft, nennt eine Direkt-Adresse keine Farbe.
Mit `ACT23_FARB_MISCHUNG=0` ist die Farbe wieder eine Eigenschaft und darf wieder genannt werden.
`ACT23_EIG_DIREKT_FORM` wird dadurch weitgehend gegenstandslos: ohne Farbachse ist die Form die
einzige verfolgbare Achse und wird ohnehin immer genannt.

# Drei Erklaerungen, die vorher geprueft und verworfen wurden

Sie stehen hier, damit niemand sie erneut aufmacht:

* **obj_X verliert seine Verformung** - nein. `[Neuheit-Kontrolle]` meldet in jeder Episode
  `(30, 4, 12)mm -> haelt`, weil nach obj_X kein Koerper mehr offen ist und er Probe-Koerper bleibt.
* **obj_X stand nicht in der Szene** - nein. In 10 von 10 Rueckfaellen stand er auf dem Tisch.
* **obj_X ist der schwerere Koerper** - nein, im Gegenteil. Eine getrennte Achsenmessung auf dem
  Zustand und den Szenen desselben Laufs (50 Szenen) sagt das Umgekehrte:

        Koerper    n   chroma ueber   form ueber   spanne ueber   alle drei
        obj_T     18      0,0 %        50,0 %        11,1 %        50,0 %
        obj_X     11      0,0 %        27,3 %         0,0 %        72,7 %

  **obj_X ist der LEICHTERE.** Genau dieser Widerspruch zwischen Pruefstand und Lauf war die Spur,
  die zur Farbmischung fuehrte.

# Lieferquote

    wuerfel     7/140 = 5,0 %
    formzuerst  6/140 = 4,3 %
    ohnefarbe  10/140 = 7,1 %

Nicht das Kriterium ([ziel.md](/ziel.md)), und bei diesen Zahlen nicht zu trennen. Die Richtung
passt immerhin zur Sache.

# Fallen

* **Ein Seed je Arm.** Die Aussage zur Farbachse ist mit p = 1,5e-3 bis 3,3e-3 belastbar, die
  Quoten sind es nicht.
* **Die Arme laufen nach der ersten abweichenden Entscheidung auseinander.** Bis dahin sind sie
  ausgerichtet - dafuer wuerfelt `_adresse_wuerfeln` auch dann, wenn ein Startpunkt gesetzt ist
  (sonst haetten die Arme allein durch drei verbrauchte Zufallszahlen divergiert, und obj_X waere
  auf ZWEI VERSCHIEDENEN Detektionen adressiert worden - 569 gegen 924 px. Das ist im ersten
  Anlauf passiert und hat ihn ungueltig gemacht).
* **obj_X faellt weiter in 8 von 14 Episoden zurueck.** Die verbleibende Schwaeche ist die
  Aufloesungsrate, nicht die Genauigkeit - trifft die Adresse, dann auf 1,0 mm.
* **Zwei Koerper.** Die Regel ist plausibel und mechanisch erklaert, aber an zwei Adressen
  gemessen.
* **Vorgabe bleibt 0** fuer `ACT23_EIG_DIREKT`.

# Verwandt

* [Die Adresse ohne Klasse](/mechanismen/adresse-ohne-klasse.md) - der Bau
* [Aus einer Sichtung kommandierbar](/befunde/adresse-ohne-klasse-gemessen.md) - der Lauf davor; seine Ursachen-Lesart ist hier widerlegt
* [Stetig adressieren statt Klassen vergeben](/fragen/stetige-adressierung.md) - die These
* [Adressfehler sind Verschmelzung](/befunde/adressfehler-sind-verschmelzung.md) - "eindeutig ist nicht richtig", hier zum wiederholten Mal
