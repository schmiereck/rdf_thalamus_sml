---
type: Befund
title: Findet die Bilddifferenz der eigenen Bewegung die Hand?
description: Grob ja, fuer eine Kalibrierung nein. Der Schwerpunkt der Bilddifferenz liegt nach einem fest gelernten Versatz im Greiferrahmen im Median 7-13 mm neben der Klauenmitte. Eine daraus gelernte Abbildung (Pixel, Hoehe) -> Ort erreicht 8-12 mm statt der noetigen ~1 mm, denn der Fehler ist systematisch (posenabhaengig) und mittelt sich nicht weg. Passive Differenz (der Arm bewegt sich ohnehin) ist unbrauchbar (Median 29-35 mm). Gezieltes Zappeln von Greifer oder Handgelenk ist besser, traegt aber als Etikettquelle in dieser einfachen Form nicht.
tags: [act23, wahrnehmung, hand, kamera, perceive_all, selbstueberwacht]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-10-14T00:00:00Z }
sources:
  - id: sonde
    resource: "Sonde im Scratchpad (nicht committet): Haken an BracketArmSim.step (Nachlade-Haken wegen ACT14_DOF), jede 4. Schrittgruppe; eigener Renderer 240 px, Arm sichtbar, Segmentierung nur als Pruefer; Seeds 9701/9702 x 12 Ep, Kopie df320cd0, Stand c8815bd"
    title: Handdifferenz-Sonde
  - id: sicht
    resource: /befunde/hand-sichtbarkeit.md
    title: Handsicht
  - id: plan
    resource: /fragen/perceive-all-abloesen.md
    title: perceive_all abloesen
---

# Frage

Schritt 1 in [perceive_all abloesen](/fragen/perceive-all-abloesen.md) will den Bildort aus der eigenen
Hand lernen: Bildpunkt der Hand plus Ort aus dem Koerpermodell ergibt ein Etikett. Die
[Handsicht](/befunde/hand-sichtbarkeit.md) hat gezeigt, dass die Hand praktisch immer im Bild ist; dort
fand sie aber eine Segmentierung, die der Agent nicht hat. Hier geht es darum, ob er sie **ohne Segmentierung**
findet, naemlich ueber das, was sich mit der eigenen Bewegung im Bild aendert. Nutzerauftrag 2026-10-14.

# Aufbau

* Echte act23-Episoden wie in der Handsicht: Seeds 9701/9702 je 12, Netz-Policy, Kopie des Hauptzustands.
  **Geprueft:** die Ergebnisfolge beider Seeds ist zeichengleich mit dem Handsicht-Lauf, die Sonde steuert nichts.
* Jede 4. Schrittgruppe (6352 Aufnahmen) rendert ein **eigener** Renderer die Uebersichtskamera mit Arm (240 px,
  Schatten wie im Modell). Drei Arten der Differenz, Schwelle 12 Grauwerte auf dem staerksten Kanal:
  * **P passiv:** gegen die vorige Aufnahme, also das, was sich durch die laufende Bewegung ohnehin aendert.
  * **G Greifer zappeln:** Kopie des Zustands, nur der Greifer (`joint_5`) um 0,25 rad verstellt.
  * **W Handgelenk zappeln:** dasselbe mit `joint_4` um 0,15 rad.
  * G und W sind **kinematisch** (`mj_forward`, keine Physik): ein gehaltenes Objekt reagiert nicht.
  * Als Bezug dient dieselbe Kopie, neu vorwaerts gerechnet. Ohne das zappelt der ganze Arm um einen Zeitschritt
    mit, weil die Kinematik nach `mj_step` hinter `qpos` herhinkt. Das ist im Rauchtest aufgefallen und behoben.
* Schaetzungen des Handpunkts aus der Differenz: **E1** Schwerpunkt aller Differenzpixel, **E2** Schwerpunkt des
  groessten Flecks, **E3** Schwerpunkt der Pixel, die sich bei G **und** W aendern.
* Wahrheit: die Mitte der beiden Klauen. Der Differenz-Schwerpunkt liegt nicht dort, sondern irgendwo am Greifer.
  Deshalb wird ein **fester Versatz im Greiferrahmen** gelernt, aus einem Seed geschaetzt und am anderen geprueft
  (beide Richtungen). Das ist das Guenstigste, was der Agent haben koennte: einen Etikettpunkt, der fest an der
  Hand haengt.
* Fehler: der Bildpunkt als Strahl, geschnitten mit der Hoehe des Etikettpunkts, Abstand in der Tischebene.

# Zahlen

**Einzelne Aufnahme, mit gelerntem Versatz** (Median / p90 in mm, Pruefseed 9702, Versatz aus 9701; umgekehrt in
Klammern):

    Schaetzung                 alle             Hand 0-70 mm     Tragen
    P passiv, E1               29 / 79  (35)    17 / 45          16 / 38
    G Greifer, E1              13 / 22  (11)    10 / 31           9 / 43
    G Greifer, E2               7 / 39  ( 8)    10 / 45           7 / 65
    W Handgelenk, E1           10 / 15  ( 8)     9 / 15           7 / 12
    W Handgelenk, E2           15 / 35  (13)    11 / 21          11 / 19
    E3 G und W                  9 / 21  (11)    11 / 25           9 / 37

Ohne Versatz liegen alle Schaetzungen 20-100 mm daneben. Hoechstens 19 % der Aufnahmen liegen innerhalb von 3 mm
(eine Ausnahme: G-E2 ueber 70 mm Hoehe, 40 %).

**Woraus die Differenz besteht** (Anteile der Differenzpixel, Mittel, nach Segmentierung):

    Art     Greifer  uebriger Arm  Objekt  Rest (Tisch, also Schatten)   Pixel Median
    P        42 %       36 %        5 %          17 %                      888
    G        65 %        8 %        3 %          23 %                      393
    W        78 %        5 %        3 %          14 %                      889

Passiv bewegt sich fast immer der ganze Arm mit: nur in 9 % der Abtastungen standen die vier Positionsgelenke still.

**Schritt-1-Probe: gelernte Abbildung (Pixel, Hoehe) -> Ort.** Polynom 3. Grades, robust gefittet auf den Etiketten
eines Seeds mit Hand unter 70 mm, geprueft an den wahren Klauenmitten des anderen Seeds:

    Etikettquelle                  Median    p90    (umgekehrte Richtung)
    ideal (wahre Projektion)        0,03     0,07   (0,05 / 0,19)
    W Handgelenk, E1                9,0     15,4    (8,1 / 21,9)
    G Greifer, E1                  10,9     15,6    (11,1 / 16,7)
    E3 G und W                     12,4     18,0    (10,1 / 16,8)
    G-E2, W-E2                     15-31    39-68

Messlatte nach der [Homographie-Messung](/befunde/homographie-genauigkeit.md): rund 1 mm auf dem Tisch.

# Bewertung

* **Die naive Bilddifferenz taugt als Etikettquelle fuer Schritt 1 nicht.** Die gelernte Abbildung landet bei
  8-12 mm, rund zehnmal schlechter als die heutige Homographie. Das Modell ist nicht der Engpass (ideal 0,03 mm),
  die Etiketten sind es.
* **Der Fehler mittelt sich nicht weg.** Die Abbildung ist so schlecht wie eine einzelne Aufnahme, also ist der
  Fehler systematisch. Wo der Schwerpunkt der Differenz relativ zur Klaue liegt, haengt von der Pose ab: von der
  Ansicht des Greifers, von seinem Oeffnungsgrad und von seinem **Schatten** (14-23 % der Differenzpixel liegen auf
  dem Tisch). Ein fester Versatz im Greiferrahmen faengt das nicht ein.
* **Passiv bringt am wenigsten.** Laeuft der Arm ohnehin, gehoert nur gut 40 % der Aenderung zum Greifer.
* **Aktiv zappeln ist besser und billig.** Das Handgelenk liefert die stabilste Differenz (78 % Greifer, p90
  15 mm), der Greifer die kleinste. Fuer ein **grobes** "wo ist meine Hand" (rund 1 cm) reicht das, etwa fuer
  Blicklenkung oder um den Arm aus einer Maske zu nehmen. Fuer die Kalibrierung reicht es nicht.

# Was das nicht ausschliesst

* **Ein Detektor, der aus diesen Differenzen lernt.** Die Zappel-Masken sind schwache Etiketten fuer *welche Pixel
  zur Hand gehoeren*, nicht fuer *welcher Punkt die Klauenmitte ist*. Ein Netz, das daraus eine Handmaske und dann
  einen festen Handpunkt lernt (etwa die Spitze der Maske), haette den Schattenanteil nicht. Ungemessen.
* **Einen anderen Etikettpunkt.** Hier wurde der Schwerpunkt mit der Klauenmitte verglichen. Ein Punkt, den Bild
  und Koerpermodell gleichermassen "sehen", etwa die Kontaktstelle beim Antippen des Tischs, waere enger. Ungemessen.
* **Mittelung ueber gezielte Mehrfachblicke:** dieselbe Pose mit mehreren Handgelenkwinkeln, der Drehpunkt der
  Differenz. Ungemessen.
* Physik beim Zappeln: kinematisch gerechnet; ein echter Arm zappelt mit Nachschwingen und wackelt am Objekt.

# Verwandt

* [perceive_all abloesen](/fragen/perceive-all-abloesen.md)
* [Sieht die Uebersichtskamera die eigene Hand?](/befunde/hand-sichtbarkeit.md)
* [Wie genau sind die Tisch-Homographien?](/befunde/homographie-genauigkeit.md)
* [Pruefstandsfalle](/mechanismen/pruefstandsfalle.md) - dies ist ein Pruefstand, keine act23-Wirkung
