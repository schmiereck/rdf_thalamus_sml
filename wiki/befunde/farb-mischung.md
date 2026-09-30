---
type: Befund
title: Farbe und Form entkoppelt - die Adressierung haelt, die Quote faellt uneinheitlich
description: Die sieben Koerperfarben werden je Episode permutiert, colour_of_body kommt aus der Wahrnehmung statt aus der Tabelle. Die Adressierung bleibt intakt (Median 1,2-1,4 mm, Eindeutigkeit unveraendert). Die Lieferquote faellt gepoolt von 57,5 auf 47,6 Prozent - aber die Seeds widersprechen einander (-1,3 gegen -18,3 Punkte), und ein Rateneinbruch ist bei einer schwereren Welt ohnehin kein Defekt.
tags: [act23, wahrnehmung, farbe, generalisierung, ab]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-10T20:00:00Z }
sources:
  - id: sweep
    resource: "Gepaarter Seed-Sweep: 4 kopflose Steuerungslaeufe je ~112 Episoden (Seed 7 und 23, ACT23_FARB_MISCHUNG 0/1), Schnappschuss 98a293f2, gleichzeitig gefahren"
    title: Farb-Mischungs-A/B
  - id: rueckhalt
    resource: /befunde/farbe-form-rueckhalt.md
    title: Der Rueckhalte-Test, der die Entkopplung begruendet
---

# Was gebaut wurde

Nutzerauftrag nach dem [Rueckhalte-Test](/befunde/farbe-form-rueckhalt.md): *"jede Form in
mehreren Farben, Zuordnung zwischen den Episoden gewuerfelt, innerhalb fest. Vorher waere zu
klaeren, was `colour_of_body` dann liefert - ich wuerde es je Episode neu aus der Wahrnehmung
setzen statt aus einer Tabelle."*

`ACT23_FARB_MISCHUNG` tut genau das - **Vorgabe 1 seit dem 2026-09-10** (Nutzerentscheid nach
der Messung; die entkoppelte Welt ist ab jetzt die Standardwelt):

* **Permutation statt neuer Farben.** Die sieben **vorhandenen** Koerperfarben werden unter den
  Koerpern getauscht. Eine neue Farbe wuerde eine neue Farbklasse gebaeren - das waere ein
  anderes Experiment und wuerde die Messung verunreinigen. Kontrolle: **0 neue Farbklassen** in
  beiden Armen.
* **`colour_of_body` je Episode aus der Wahrnehmung.** `perceive_all` -> Chroma klassifizieren ->
  Detektion dem naechsten Koerper zuordnen (40-mm-Schranke). Derselbe Zuordnungsschritt wie bei
  der bestehenden Erstbindung (`pc_act23.py:2826`) - **keine neue Privilegklasse**, aber ehrlich
  gesagt: der Schritt *ist* buchhalterisch privilegiert, und er laeuft jetzt je Episode statt
  einmal.
* **Drei Wachen** aus der Erstbindung uebernommen: verschmolzene Blobs binden nicht (Mischchroma
  gebiert Phantomklassen), zwei Koerper teilen nie eine Farbklasse, und ohne gute Zuordnung
  bleibt ein Koerper **ungebunden statt geraten**.
* **Eine Fassung fuer beide Auto-Schleifen**, VOR `curious_pick` und `_auto_eig_umschreiben` -
  beide nehmen wahr, und eine nach dem Umfaerben gewuerfelte Adresse muesste sonst eine Farbe
  nennen, die es nicht mehr gibt.

# Zahlen

    Arm         Ep |  Quote  Median mm | eindeutig  Rueckfall | Fehlstart  fremd>5% | unzuordenbar
    m7_aus     112 | 50,9 %      24    | 104/110    5,4 %     |  3,6 %     11,6 %   |  0 -> 29
    m7_an      113 | 49,6 %      25    | 109/110    6,2 %     |  3,5 %      5,3 %   |  0 -> 26
    m23_aus    116 | 63,8 %      19    | 111/114    4,3 %     |  6,0 %      7,8 %   |  0 -> 26
    m23_an     112 | 45,5 %      26    | 103/109    6,2 %     |  5,4 %      9,8 %   |  0 -> 45

    ADRESSIERUNG (Kommando gegen wahre Lage des gemeinten Koerpers)
      m7_aus  Median 1,4 mm   m7_an  1,2 mm
      m23_aus Median 1,0 mm   m23_an 1,4 mm

    Lieferquote
      Seed  7   50,9 -> 49,6 %   Fisher p = 0,894
      Seed 23   63,8 -> 45,5 %   Fisher p = 0,0076
      gepoolt   57,5 -> 47,6 %   Fisher p = 0,0386

# Nachtrag 2026-09-11: der Quotenbefund ist entkraeftet

Ein GUI-Langlauf ueber **906 Episoden** in der entkoppelten Welt liefert **53,1 %** - das alte
Niveau. Der hier gemessene Einbruch auf 47,6 % war der Ausreisser-Arm, nicht die Welt. Die
Vorbehalte unten ("die Seeds widersprechen einander", "m23_aus lag mit 63,8 % weit ueber dem
Ueblichen") haben sich als richtig erwiesen. **Die Entkopplung kostet keine Quote.** Siehe
[906 Episoden in der entkoppelten Welt](/befunde/langlauf-entkoppelt.md).

# Bewertung

**Die Adressierung haelt - das war die eigentliche Frage.** Median 1,0-1,4 mm in allen vier
Armen, die Eindeutigkeit bleibt (103-111 von ~110), der privilegierte Rueckfall steigt nur von
4-5 auf 6 %. Die neu aus der Wahrnehmung gesetzte Bindung traegt also; das Eigenschafts-Kommando
funktioniert in einer Welt, in der die Farbe nicht mehr die Form verraet.

**Die Quote faellt, aber der Befund traegt nicht, was er auf den ersten Blick verspricht.**
Gepoolt -9,9 Punkte bei p = 0,039 - die beiden Seeds sagen aber voellig Verschiedenes: -1,3
Punkte (p = 0,89) gegen -18,3 Punkte (p = 0,0076). Dazu kommt, dass ausgerechnet der
Vergleichsarm `m23_aus` mit 63,8 % **deutlich ueber** dem sonst ueblichen Niveau (~52 %) liegt;
ein Teil des "Einbruchs" ist wahrscheinlich dessen Ausreisser. Der Vorzeichentest ueber die
Objekte ist entsprechend schwach: 4/7 bzw. 5/7 schlechter.

**Und selbst ein echter Rateneinbruch waere hier kein Defekt.** Die gemischte Welt ist
schwerer - der Farbpfad traegt die Identitaet nicht mehr automatisch mit. Das war die vorab
notierte Erwartung, und nach [dem Projektziel](/ziel.md) ist die Lieferquote hier ohnehin nicht
das Kriterium: eine Welt, in der Farbe und Form unabhaengig sind, ist die Welt, in der
Generalisierung **ueberhaupt erst messbar** wird.

**Ein Nebenwert ist auffaellig:** in `m23_an` wachsen die unzuordenbaren Sichtungen auf 45 statt
26. Passend zur Erwartung - vertraute Formen in ungewohnten Farben sind fuer den Open-Set-Blick
neu. Ob daraus Aneignung wird oder nur Muell, ist mit einem Arm nicht zu sagen.

# Fallen und Vorbehalte

* **Das ist ein WELT-Wechsel, kein Eingriff.** Ein A/B vergleicht hier zwei verschiedene
  Aufgaben, nicht zwei Loesungen derselben Aufgabe. "Besser/schlechter" ist die falsche Frage;
  "haelt die Maschinerie" ist die richtige, und die Antwort ist ja.
* **Die Seeds widersprechen einander deutlich.** Nach
  [Zwei Laeufe sind dieselbe Rechnung](/befunde/laeufe-sind-reproduzierbar.md) ist ein Lauf eine
  Stichprobe; zwei Seeds sind zwei. Fuer eine belastbare Aussage ueber die Quote braeuchte es
  mehr Seeds - und die Quote ist hier nicht das Ziel.
* **Nur der Auto-Pfad faerbt um.** Ein von Hand kommandiertes Objekt wuerde die Farbe unter dem
  Kommando wechseln; deshalb sitzt der Aufruf in den beiden Auto-Schleifen, nicht in `run_one`.
* **`colour_of_body` wird weiterhin persistiert.** Mit Mischung ist der gespeicherte Stand nur
  die Bindung der letzten Episode - beim naechsten Lauf ueberschreibt ihn die erste Episode
  ohnehin. Harmlos, aber nicht als dauerhafte Wahrheit lesen.

# Was jetzt messbar ist, das es vorher nicht war

Vorher trugen "Farbe" und "Form" dieselbe Information. Jetzt sind es zwei. Konkret sichtbar
wurde das schon im Rauchtest: Auto wuerfelte `neu-285 + mittel` - eine **reine Form-Adresse**,
die vorher inhaltlich dasselbe gesagt haette wie die Farbe.

Damit werden zwei Fragen aus [den offenen Faeden](/fragen/offene-faeden-act23.md) erstmals
stellbar: ob die instabile Formklasse von obj_X (4 von 8 Lagen, s.
[Rueckhalte-Test](/befunde/farbe-form-rueckhalt.md)) im Lauf tatsaechlich kostet, und ob die
Selbst-Aneignung neue **Kombinationen** aufgreift statt nur neuer Koerper.

# Folgen: die entkoppelte Welt ist die Standardwelt

Der Nutzer hat die Vorgabe am 2026-09-10 auf `1` gestellt. Das ist eine Entscheidung ueber das
**Szenario**, nicht ueber eine Verbesserung - und sie folgt [dem Projektziel](/ziel.md): erst in
einer Welt, in der Farbe und Form unabhaengig sind, ist Generalisierung ueberhaupt messbar.

Geprueft ohne jede Umgebungsvariable auf einer Zustandskopie: die `[Farbe]`-Zeile erscheint je
Episode, `ACT23_FARB_MISCHUNG` taucht nicht mehr unter den Abweichungen auf, **0 neue
Farbklassen**, und die vier Episoden liefern 3 von 4.

> **Warnung fuer spaeter:** wer diese Vorgabe zurueckdreht, weil "die Quote gefallen ist", misst
> das Szenario, nicht einen Fehler. Alle Quotenzahlen ab hier sind mit denen davor **nicht**
> vergleichbar - es ist eine andere Aufgabe. Der Kommentar am Schalter sagt das ebenfalls.

**Rueckfall in einer Zeile:** `ACT23_FARB_MISCHUNG=0`.

# Verwandt

* [Farb-Rueckhalte-Test](/befunde/farbe-form-rueckhalt.md) - die Begruendung
* [Projektziel](/ziel.md) - warum Kombinationen zaehlen
* [Zwei Laeufe sind dieselbe Rechnung](/befunde/laeufe-sind-reproduzierbar.md)

# Beobachtung im GUI-Lauf 2026-09-30: die Knopf-Namen luegen

Der Nutzer sah "[Auto 83] Gruenes Wuerfel", obwohl kein gruener Wuerfel in der Szene lag, und
vermutete einen Auswahlfehler. Am Log (`log/pc_act23_2026-09-30_08-21-56_16080.txt`) geprueft:
kein Auswahlfehler - obj_green lag auf dem Tisch (nicht geparkt), wurde in Ep 82 und 83 wirklich
gegriffen und getragen (Griffdruck 6 N). Die Ursache ist die Benennung: `OBJECTS` traegt feste
Namen mit FARBWORT ("Rotes Wuerfel", "Gruenes Wuerfel"), waehrend `FARB_MISCHUNG` (Vorgabe 1) die
Farben je Szene unter den Koerpern permutiert. "Gruenes Wuerfel" heisst nur noch "der Koerper
obj_green", und der kann gerade rot, blau oder gelb sein. Nebenbefund derselben Episode:
"Selbst-Urteil: noch keine eigene Klasse fuer obj_green" - die Farbbindung je Episode hatte den
Koerper nicht gebunden; das passt zur suchenden Fovea (vermutet, nicht geprueft).
Abhilfe (nicht gebaut): Anzeige-Name aus der aktuell gesehenen Farbe bilden oder farbneutral
("Wuerfel A/B").
