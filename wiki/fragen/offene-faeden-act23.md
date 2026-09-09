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

# Die zwei belegten Engpaesse

Beide stammen aus [1109 Episoden ohne Lernfortschritt](/befunde/langlauf-ohne-fortschritt.md)
und sind nicht Vermutung, sondern Messung.

**1. Klassenkonsolidierung.** 17 von 17 bzw. 14 von 14 selbst geborenen Klassen verhungern,
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

**Komplexer Wrist-Kopf.** Der Wrist-Winkel wird heute von Hand als `[cos2w, sin2w]` kodiert -
eine handgebaute Phasenkodierung in einem komplexwertigen Netz. `z = e^{2iw}` waere nativ, die
pi-Periodizitaet der Greifersymmetrie das Quadrieren der Phase, und `cos2(w-yaw)` schlicht
`z_w * conj(z_yaw)`. Nicht gemessen. Siehe
[Modullandschaft](/mechanismen/act23-modullandschaft.md).

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

**Verschmelzung: die HAEUFIGKEIT im Lauf.** Die eine Haelfte der Frage ist beantwortet - der
Split traegt ab 35 mm vollstaendig, bei 25 mm nur zu 72 %, und die Formklasse ueberlebt viel
schlechter als die Position ([Abstandskurve](/befunde/verschmelzung-abstandskurve.md)). Offen ist
die andere Haelfte: **wie oft stehen die Koerper im Lauf ueberhaupt so nah?** Das haengt an
`randomize_objects` und ist mit dem Nachbar-Merkmal im Puffer billig auszaehlbar (dort steht
`d_nah`, Median 80 mm - aber nur auf 6 % der Zeilen, s.
[Merkmale kommen zu spaet](/befunde/merkmale-kommen-zu-spaet.md)).
Zweiter offener Punkt: die Formklasse ueber den Split zu retten ist der schwaechere Pfad -
ob sich das verbessern laesst, ist ungemessen.

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
* **Rechnerlast als Einfluss auf die Lieferquote** - zwei natuerliche Lastfenster widersprechen
  einander, die Physik ist unter Volllast bitgleich, im Steuerpfad steht keine Wanduhr. Siehe
  [Rechnerlast](/befunde/rechnerlast.md).
