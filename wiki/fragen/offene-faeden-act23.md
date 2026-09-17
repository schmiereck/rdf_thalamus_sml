---
type: Frage
title: Offene Faeden in act23
description: Was gemessen werden muesste, geordnet nach belegter Wichtigkeit - Klassenkonsolidierung, Griffmechanik, gelernte Schliess-Entscheidung, komplexer Wrist. Enthaelt auch die ausdruecklich geschlossenen Faeden.
tags: [act23, offen]
status: stable
evidenz: vermutung
ebene: code
generated: { by: claude/opus-5, at: 2026-09-07T00:00:00Z }
---

> **NEU (2026-09-16), und moeglicherweise ueber beide Engpaesse hinweg:**
> [Stetig adressieren statt Klassen vergeben](/fragen/stetige-adressierung.md). Alle drei
> Kommando-Achsen verwandeln stetige Groessen in Namen, und erst die Namen haben Geburt,
> Bestaetigung und Verhungern. Engpass 1 unten waere damit gegenstandslos statt geloest.

> **NEU (2026-09-17), eine AUFGABE statt einer Reparatur:**
> [Stapeln als neue Aufgabe](/fragen/stapeln-als-aufgabe.md). Das Ablageziel bekommt denselben Typ
> wie das Objekt - eine Adresse -, die Relation "auf" wird eine Phasendrehung im RoPE-Ziellatent.
> Die Verdrahtung steht groesstenteils; benannt und beziffert sind drei Huerden (eine Laufzeitregel,
> die Ziele von Koerpern wegschiebt; ein Erfolgsbegriff, der "liegt auf dem Tisch" heisst; und eine
> Ablagegenauigkeit, die doppelt so grob ist wie die geometrische Stapeltoleranz). Erste Messung:
> [ein gestapelter Koerper liest 16 mm daneben](/befunde/stapeln-bricht-die-tischebene.md).

> **Forschungsprogramm (2026-09-17):**
> [Dream-RSI: Forschungs- und Entwicklungsplan](/fragen/dream-rsi-forschungsplan.md) fuehrt
> die neuen Arbeitspakete und Entscheidungstore. Optionale Nutzerwuensche sind
> [direkte Servosteuerung](/fragen/dream-rsi-servosteuerung.md) und
> [weitere Fovea-Aufgaben mit schrittweisem Detailausbau](/fragen/dream-rsi-fovea.md).
> Dies sind ungepruefte Hypothesen. Die unten geschlossenen Faeden werden dadurch nicht
> wieder als erfolgversprechend behauptet: Motorik wird auf eigene Anpassung statt kleinen
> Zusatzgewinn ueber dem Teacher geprueft; Fovea-Ausbau braucht einen neuen Informationsbedarf.

# Die zwei belegten Engpaesse

Beide stammen aus [1109 Episoden ohne Lernfortschritt](/befunde/langlauf-ohne-fortschritt.md)
und sind nicht Vermutung, sondern Messung.

**1. Klassenkonsolidierung - die Engstelle ist jetzt benannt.** Im
[906-Episoden-Langlauf der entkoppelten Welt](/befunde/langlauf-entkoppelt.md) wurden 13 Klassen
geboren, und **alle 13** melden denselben Grund fuers Verhungern: *"kein Knopf zu vergeben - der
Probe-Koerper ist schon gebunden"*. Eine neu geborene Klasse ist damit strukturell nicht
kommandierbar, kann nie geuebt werden und stirbt. Das ist **kein Lernproblem, sondern eine
Vergabe-Engstelle** - der Weg von "geboren" zu "benutzbar" existiert nur fuer den einen
reservierten Probe-Koerper. Und die alte Ausrede greift nicht mehr: es gab 97 Farb/Form-
Kombinationen zu sehen, nicht 7.

> **PRAEZISIERT (2026-09-15).** Die Engstelle ist nicht der belegte Probe-Koerper, sondern
> dass die AUTO-SCHLEIFE `state.OBJECTS` ueberhaupt nie erweitert - auch das
> Eigenschafts-Kommando nicht, das sie umgehen sollte. Nur der GUI-Pfad und eine
> Startvariable koennen einen neuen Koerper einfuehren.
> Siehe [Die Vergabe-Engstelle, diagnostiziert](/befunde/vergabe-engstelle-diagnose.md).

**1b. Der urspruengliche Befund dazu:** 17 von 17 bzw. 14 von 14 selbst geborenen Klassen verhungern,
keine wird je kommandiert, die unzuordenbaren Sichtungen wachsen linear. Der Engpass sitzt bei
der **Geburt** (Klasse aus drei Sichtungen einer einzigen Lage), nicht am Anspruch danach - zwei
Fassungen einer Wache am Anspruch haben gemessen nichts geloest, siehe
[Formfaktorisierung](/befunde/formfaktorisierung.md) und
[Formklassen-Lebenszyklus](/mechanismen/formklassen-lebenszyklus.md). Naheliegender ungepruefter
Weg: [latente Augmentierung](/fragen/latente-augmentierung.md). Der groesste ungenutzte Lernstoff
daneben: rund 200 Fehlschlaege je 1000 Episoden werden vollstaendig verworfen. Siehe
[Selbst-Aneignung stockt](/befunde/selbstaneignung-stockt.md).

**2. Griffmechanik.** In 60-87 % aller Fehlschlaege hat die Klaue nie etwas getragen. Der Fehler
sitzt im Griff, nicht in der Ablage. Zugleich ist "Greifen ueber den Teacher hinaus lernen"
gemessen ein Sackgassenweg, siehe [Greif-Lerndeckel](/befunde/greif-lerndeckel.md) - der Weg
fuehrt also ueber **Mechanismus-Korrekturen**, nicht ueber RL. Beim U ist der Aktionsraum
fuenffach ausgeschoepft, siehe [U-Form-Engpass](/befunde/u-form-engpass.md).

# Weitere offene Punkte

**Gelernte Schliess-Entscheidung.** act23 hat die act21-Entwoehnung von `CLOSE_GUARD` und
`REFLEX` nie mitgemacht; die Policy hat die Entscheidung nach 1109 Episoden nicht gelernt. Der
naheliegende Ersatz ueber den Fingerdruck ist dreifach gemessen **negativ**. Offen bleibt der
Weg ueber ein wahrgenommenes Objekt-im-Greifer-Signal. Siehe
[Laufzeitregeln](/mechanismen/laufzeit-regeln.md).

**Komplexer Wrist-Kopf - GROESSTENTEILS ERLEDIGT, Eintrag korrigiert 2026-09-16.** Dieser Faden
stand hier als "nicht gemessen". **Das war falsch.** Das komplexe Produkt `z_w * conj(z_yaw)`
rechnet `world_model.cross_augment` seit dem 2026-07-17, Vorgabe an, mit Messung: der
Kapazitaetstest zeigt die bilineare Regel bei **n ~ 150 statt ~3000** sauberen Zeilen, der Lauf
67,5 % gegen 45 %. Dazu gebaut: `|cos2(w-yaw)|` als Schaerfe, dasselbe Produkt gegen die
Armrichtung, und die Neigung gegen die kinematisch erzwungene.

Was uebrig bleibt, ist schmaler als der alte Eintrag suggerierte: `WorldModel` laeuft auf einem
**reellen** MLP, nicht im CVNN - dort ist `[cos2w, sin2w]` bereits `e^{2iw}` als (Re, Im), und es
umzuschreiben aendert keine Zahl. Ein nativer Kopf hiesse, ihn in die komplexe PC-Engine zu
verlegen; eine Hypothese, was das besser machen soll, gibt es nicht.

**Der interessantere Rest:** der Wrist wird ueber ein Gitter gewaehlt (`wrist_grid=8`, 22,5-Grad-
Stufen) - die vierte diskretisierte Achse neben Farbe, Form und Groesse, und die einzige, an der
die Diskretisierung noch nie gemessen wurde. Siehe
[Modullandschaft](/mechanismen/act23-modullandschaft.md) und
[stetige Adressierung](/fragen/stetige-adressierung.md).

**Situationsrepraesentation des Weltmodells.** Zwischen Grundrate 54 % und Obergrenze 82 %
liegen ~27 Punkte lernbares Signal, die das Modell nicht einsammelt (AUC 0,489 im Lauf). Vier
naheliegende Rezepte sind bereits null. Was fehlt, ist ein **Merkmal**, nicht ein Verfahren.
Siehe [Exekutionsvarianz](/befunde/exekutionsvarianz.md). **Praezisierung 2026-09-08:** das
naechstliegende Merkmal ist laengst gebaut - der Nachbar-Block - steht aber nur auf 6 % der
Pufferzeilen und konnte deshalb nie wirken. Vor jedem neuen Merkmal steht damit die Frage, wie
ein Merkmal ueberhaupt in einen gewachsenen Lifelong-Puffer kommt. Siehe
[Merkmale kommen zu spaet](/befunde/merkmale-kommen-zu-spaet.md).

**Das Kredit-Design fuer Fehlgriffe.** Der konkreteste Strang daneben: dem Weltmodell fehlen
genau die schaedlichen Faelle als Etikett - 36 % der Episoden sind komplett unsichtbar. Zwei
denkbare Zwischenwege sind benannt und **nicht gebaut**: nur bei sauberem Anfahrkriterium labeln,
oder das Fehlgriff-Etikett nur auf die Ausrichtungsdimension wirken lassen. Siehe
[Wrist-Ausrichtung](/befunde/wrist-ausrichtung.md) und
[Kredit und Selbst-Urteil](/mechanismen/kredit-und-selbsturteil.md).

**Der Latent-Attraktor braucht zwei Voraussetzungen**, bevor er ueberhaupt wieder gemessen
werden kann: eine vortrainierte, persistente Dynamik mit Uebergaengen **pro Schritt** statt einem
je Episode, und ein Tor, das ihn erst unterhalb einer MSE-Schwelle einschaltet. Siehe
[Latent-Etappen](/befunde/latent-etappen.md).

**Den FORM-Split verbessern - teilweise erledigt.** Der Tracker-seitige Weg (Kontinuitaet statt
Neuklassifikation) ist gebaut und gemessen: sauber, aber klein (1-2 % der Anfahrschritte, kein
Lauf war je ganz blind), siehe
[Kontinuitaet statt Neuklassifikation](/befunde/kontinuitaet-statt-neuklassifikation.md). Offen
bleiben die beiden anderen Wege aus [der Diagnose](/befunde/formsplit-warum.md): eine
kontextabhaengige Schwelle fuer Split-Detektionen (der Deskriptor liegt bei 0,94-1,55 x novel_th,
also knapp daneben) und die Rettung des Fussabdrucks selbst (der Splitteil behaelt nur 31-58 %
der Pixel). Der zweite waere die Ursache, ist aber der tiefste Eingriff in Uebergangsgeruest.

**Der urspruengliche Faden, unveraendert:** Die Verschmelzungsfrage ist in beiden Haelften beantwortet
([Abstandskurve](/befunde/verschmelzung-abstandskurve.md),
[Nachbarnaehe im Lauf](/befunde/nachbarnaehe-im-lauf.md)) und hat einen scharfen Rest
hinterlassen: der Split rettet die **Position** ab 35 mm vollstaendig, die **Formklasse** erst ab
65 mm - und die Lieferquote folgt der Formklasse, nicht der Position (Schwelle im Ausgang bei
55 mm, -13,9 Punkte in 15,6 % der Episoden). Ob sich die Formklassen-Rettung verbessern laesst,
ist **ungemessen** und ist damit der konkreteste Rest dieser Linie. Obergrenze des Ertrags:
~2,2 Punkte, und darin stecken auch Rammen und Greifpunktwahl, nicht nur Verschmelzung.

**Warum die Bindung mit mehr Uebung LAENGER dauert** (namenlose Fenster 3,2 -> 7,3 Episoden
statt kuerzer, entgegen der Erwartung). Ungemessen. Und: die Wiedererkennung streut ueber Seeds
massiv (17-100 %) - fuer belastbare Aussagen braucht es mehrere Laeufe **je** Seed, nicht mehr
Seeds.

**Warum rastet der Tracker auf dem Nachbarn ein?** Das WO ist geklaert: nicht Latent-Ziel und
nicht Choreographie, sondern der Objekt-Belief der Anfahrt, der auf ~4 mm genau am **falschen**
Koerper steht (31,2 gegen 4,2 %, p = 0,0086, s.
[Der Tracker rastet auf dem Nachbarn ein](/befunde/ablenker-bindung-gemessen.md)). Offen ist das
WARUM, und es sind zwei unterscheidbare Kandidaten: Blobverschmelzung zweier naher Koerper oder
eine Fehlzuordnung beim **Aufsetzen** des Trackers. Die naechste Messung steht in der Seite und
ist billig.

**Der Welt-Fit je Episode.** Am Pruefstand geklaert: der Fit ist schon warm, die MSE steht nach
einer Epoche, mu und sigma bleiben bei 5-200 Epochen innerhalb der Eigenstreuung des 600er-Fits.
Offen bleibt genau eines - **wie viel Aufnahmekraft man aufgibt** (der 600er-Fit folgt
widersprechender Erfahrung dreimal staerker) und ob ein Plan "voll alle n Episoden" das
auffaengt. Das ist eine `act23-ab`-Frage, kein Pruefstand mehr. Siehe
[Welt-Fit: Warmstart](/befunde/welt-fit-warmstart.md) und
[Episodendauer](/befunde/episodendauer.md).

**Der rote Wuerfel.** Schlechtestes Objekt im Langlauf (33,6 %), ausgerechnet die einfachste
Form; in einer eingefrorenen 80-Episoden-Messung lag er noch bei 57 %. Unerklaert.

**Tote Flaeche.** `motor.py`, `planner_chain.py`, `obstacle.py`, `obstacle_vision.py`,
`wrist.py`, `object_orientation.py` sind vorhanden, im act23-Lauf aber nicht verdrahtet.

**`perceive_all` ist Uebergangsgeruest.** CC-Segmentierung, Homographie und PCA sind genau die
Kruecke, die nach [Projektziel](/ziel.md) abgebaut werden soll. Zwei bekannte Bruchstellen:
`perceive_all` parkt die Marker, und die Homographie haengt an `RES=240`.

# Ausdruecklich geschlossen - nicht wieder aufmachen

* **"Laenger laufen lassen"** - 43 Stunden gemessen wirkungslos.
* **Greifen ueber den Teacher hinaus lernen** (RL, Suche, Imagination) - jeder Weg gemessen
  gleichauf oder schlechter; das gemeinsame Argmax schadet deutlich.
* **Ausfuehrungsvarianz als Erklaerung fuer den Weltmodell-Deckel** - mit n = 40 widerlegt.
* **Fingerdruck als Traeger der Schliess-Entscheidung** - dreifach gemessen negativ.
* **Der Glaubensfehler beim ersten Griffversuch** - es gibt keinen; Erfolg und Misserfolg sind
  identisch getimt (12,8 gegen 13,0 mm).
* **Der U-Greifpunkt im offenen Schlitz** - zu 70 % wahr, aber folgenlos (p = 0,81).
* **Die Nagelneigung** - abflachen 57,3 Grad -> 20 Grad wirkt auf act23-Ebene nicht
  (-2,0 Punkte, p = 0,76).
* **Aequivariante Augmentierung ueber die Lage** - gebaut, gemessen, wirkungslos: eine
  vorgestellte Zeile ist von einer exakten Kopie nicht zu unterscheiden (+0,0006 AUC).
  Siehe [Die Augmentierung wirkt wie eine Zeilenwiederholung](/befunde/augmentierung-wirkt-wie-wiederholung.md).
* **Die Wirkung des Chroma-Schnitts ueber die Lieferquote nachweisen** - Verschmelzung ist
  im Lauf ein 2-%-Phaenomen, das ist unterhalb der Nachweisgrenze. Die Wahrnehmung ist
  direkt gemessen besser (20 von 1024 verfehlten Koerpern auf 0). Siehe
  [Frisch bei null](/befunde/chroma-split-frisch.md).
* **Den Eig-Split ueber eine bessere Farbquelle retten** - drei Anlaeufe, drei Negative:
  Tripel-Farbe (verschlimmert), gebundene Farbe mit und ohne Indiz (beide schlechter), und
  die vollstaendige Bindung ueber den Pixelschnitt aendert nichts. Siehe
  [Die pixelweise Farbbindung](/befunde/farbbindung-pixelweise.md).
* **Rechnerlast als Einfluss auf die Lieferquote** - zwei natuerliche Lastfenster widersprechen
  einander, die Physik ist unter Volllast bitgleich, im Steuerpfad steht keine Wanduhr. Siehe
  [Rechnerlast](/befunde/rechnerlast.md).
