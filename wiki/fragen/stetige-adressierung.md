---
type: Frage
title: Stetig adressieren statt Klassen vergeben - die Aneignungsprobleme sind Artefakte der Diskretisierung
description: Alle drei Kommando-Achsen werden aus stetigen Groessen in Namen verwandelt - Farbe und Form ueber Klassifikatoren, Groesse ueber Baender. Erst diese Namen haben einen Lebenszyklus mit Geburt, Bestaetigung und Verhungern. Der Formvektor desc_embed existiert dagegen fuer jedes Objekt, auch fuer nie gesehene, und stirbt nie. Die Frage ist, ob das Kommando direkt auf ihm arbeiten kann - dann waeren Geburt, Knopfvergabe und Saettigung gegenstandslos.
tags: [act23, kommando, selbstlernen, latent, idee]
status: stable
evidenz: vermutung
ebene: code
generated: { by: claude/opus-5, at: 2026-09-16T00:00:00Z }
---

# Die Idee, in den Worten des Nutzers

*"In meiner urspruenglichen Vorstellung zeigen wir dem Netz ein Bild eines (neuen) Objektes und
koennen dann seine Repraesentation im Latent-Space (oder auf einem Connector) abgreifen. Der Vektor
fuer die Repraesentation kann sich natuerlich mit der Zeit, wenn das Netz sich aendert/lernt,
aendern. Diese Repraesentation benutzen wir fuer die Kommunikation mit dem Netz, wenn wir sagen
'greife und transportiere Objekt X'. ... Ziel war 'die Sprache des Netzes' zu lernen und auf der
Ebene mit ihm kommunizieren zu koennen. Oder zumindest eine gemeinsame 'Sprache' zu entwickeln,
ohne ein Language-Model zu trainieren."*

# Die Haelfte davon ist gebaut

`ShapeClassifier.desc_embed` liefert genau diesen Vektor:

> *"Compact OPEN-WORLD shape embedding from the raw |F| descriptor ... Unlike a class one-hot this
> exists for ANY object -- known or novel -- so downstream models can condition on the FORM ITSELF
> and generalise to shapes that have no class slot."*

NH Dimensionen (heute 8), standardisiert mit den Trainingsstatistiken `fmu`/`fsd` - er verschiebt
sich also mit, wenn das Netz weiterlernt, genau wie in der Idee beschrieben. **Das Weltmodell
konditioniert bereits darauf**, nicht auf Klassennamen (`situation_feats`:
`[pos, Winkelphasen, desc_embed(NH), NB, FOV, BD]`).

# Die andere Haelfte fehlt: das Kommando vergleicht Namen

    finde_nach_eigenschaften:
        if form is not None and str(det.get("shape")) != str(form):
            continue

`det["shape"]` kommt aus `resolve(desc)` - der Schritt, der aus dem stetigen Deskriptor ein
**diskretes Etikett** macht. Und erst dieses Etikett hat einen Lebenszyklus:

    Geburt (3 Sichtungen) -> Kandidat -> Bestaetigung (3 von 6 Blicken) -> Knopf -> Verhungern

Der Vektor hat davon nichts. Er wird nicht geboren, er verhungert nicht, er braucht keinen Knopf,
und es gibt von ihm keinen begrenzten Vorrat.

# Und es gilt fuer ALLE drei Achsen

    Farbe     colours.classify(chroma)       -> Klassenname
    Form      resolve(desc)                  -> Klassenname
    Groesse   groessen_band(dicke, span)     -> Bandname

Damit erklaert sich rueckblickend ein ganzer Arbeitstag:

* **Bandgrenzen** - das [7-mm-Raster](/befunde/spannen-raster-7mm.md) scheiterte an einem
  zusaetzlichen obersten Band, aus dem keine Adresse zurueckfand. Ein Zahlenwert haette diese
  Falle nicht.
* **Verschmelzungsgeborene Farbklassen** - `farbe-50`, `farbe-64`: Etiketten, die auf einer
  Mischchroma entstanden und dann das falsche Material heraustrennten
  ([Befund](/befunde/eig-split-farbquelle.md)). Eine Chromatizitaet hat diesen Fehlermodus nicht,
  nur ihre Klassifikation.
* **Sterbende Formklassen** - die ganze Kette aus
  [Vergabe-Engstelle](/befunde/vergabe-engstelle-diagnose.md), [freier
  Vergabe](/befunde/freie-vergabe-erste-tuer.md) und [29-Episoden-Saettigung](/befunde/kette-haelt-30-episoden.md).

> **Das waren durchweg Diskretisierungsartefakte, nicht Wahrnehmungsfehler.** Die Wahrnehmung
> liefert stetige Groessen; die Fehler entstehen beim Zerschneiden.

# Die Frage

**Kann das Eigenschafts-Kommando direkt auf den stetigen Groessen arbeiten?** Statt
`(farbe-3, neu-9, mittel)` waere eine Adresse ein Zielpunkt mit Toleranz - ein Chroma-Wert, ein
Formvektor, eine Spanne in Millimetern -, und `finde_nach_eigenschaften` waehlte die Detektion mit
dem kleinsten gewichteten Abstand.

Bedient wuerde das so, wie es die Idee vorsieht: **auf ein Objekt zeigen, den Vektor nehmen.**
"Nimm das, was diesem hier aehnlich ist" statt "nimm neu-3".

Dann waeren gegenstandslos: die Geburt einer Klasse, die Bestaetigung, die Knopfvergabe, der
Verhungerungsschutz, `NOVEL_BODY`, und die Saettigung bei sieben Koerpern.

# Was dagegen spricht, und es ist nicht wenig

**Eine Klasse leistet etwas, das ein Vektor nicht mitbringt: die Entscheidung, wann zwei Dinge
DASSELBE sind.** Beim Vektor wird daraus eine Schwelle - und Schwellen haben an genau dieser Stelle
schon dreimal ihre eigenen Fehler produziert
([Verschmelzungs-Indiz](/befunde/eig-split-im-lauf.md): "ein Schwellwert, der auf Abstand prueft,
siebt bevorzugt die groessten Abstaende heraus").

Weitere offene Punkte:

* **Die Namen sind die Schnittstelle zum Menschen.** "neu-3" laesst sich sagen, ein
  8-dimensionaler Vektor nicht. Zeigen statt Nennen loest das fuer die GUI, nicht fuer ein
  Protokoll oder eine Auswertung.
* **Die drei Achsen haben verschiedene Masse.** Chroma-Abstand, Deskriptor-Abstand in
  Standardabweichungen und Millimeter muessen zu EINER Entfernung verrechnet werden; die Gewichte
  waeren drei neue Zahlen, und dieses Projekt hat mit geratenen Zahlen schlechte Erfahrungen.
* **Der Deskriptor hat einen Rauschboden.** Gemessen 13-16 % der Klassentrennung schon bei 2 mm
  Verschiebung ([Daempfungsfunktion](/befunde/daempfungsfunktion.md)) - eine Aehnlichkeitsschwelle
  muss darueber liegen.
* **Die Klassen tragen heute mehr als das Kommando.** Der Verhungerungsschutz, die Konsolidierung
  und die Fovea haengen an ihnen. Ein stetiges Kommando wuerde sie nicht ersetzen, sondern
  danebenstellen.

# Der billigste erste Schritt

Er kostet keinen Lauf: **die Adress-Wiedervorlage**
(`src/pc_cvnn/act23_adress_wiedervorlage.py`) kann beide Adressierungen auf denselben echten
Laufszenen gegeneinander stellen - Klassenname gegen Deskriptor-Aehnlichkeit, gemessen an groben
Adressierungsfehlern und Rueckfall. Damit waere vor jedem Umbau beziffert, ob die stetige Achse
ueberhaupt trennscharf genug ist.

# Status

**Idee, nichts gebaut, nichts gemessen.** Sie ist hier festgehalten, weil sie als erste seit Langem
am ZIEL ansetzt statt an einem Verbraucher - und weil sie erklaert, warum so viele Reparaturen
dieser Woche an derselben Stelle scheiterten.

# Verwandt

* [Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md) - der heutige, diskrete Weg
* [Die Aneignungskette traegt 29 Episoden](/befunde/kette-haelt-30-episoden.md) - die Saettigung, die hier gegenstandslos waere
* [Die Daempfungsfunktion](/befunde/daempfungsfunktion.md) - der Rauschboden des Deskriptors
* [Latente Augmentierung](/fragen/latente-augmentierung.md) - dieselbe Nutzeridee, andere Anwendung
* [Ziel](/ziel.md)
