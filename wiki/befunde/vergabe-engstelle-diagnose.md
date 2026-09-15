---
type: Befund
title: Die Vergabe-Engstelle ist nicht der belegte Knopf - die Auto-Schleife erweitert ihre Objektliste ueberhaupt nie
description: KORRIGIERT am 2026-09-15 (obj_X steht im frischen Lauf gar nicht in der Szene). Genau EINE Klasse je Lauf kann kommandierbar werden, weil der Knopf fest an den einen reservierten Probe-Koerper verdrahtet ist. Das Eigenschafts-Kommando wurde gebaut, um die Geburt zu umgehen - es umgeht sie aber nicht, weil im autonomen Lauf nur der BEREITS gewaehlte Koerper umetikettiert wird und die Auswahl nur aus state.OBJECTS zieht. Gemessen an zwei frischen 300-Episoden-Laeufen: 12 bzw. 4 Geburten, je genau 1 vergebener Knopf, und obj_X wird in 300 Episoden kein einziges Mal adressiert.
tags: [act23, selbstlernen, formklassen, kommando]
status: stable
evidenz: gemessen
ebene: code
generated: { by: claude/opus-5, at: 2026-09-15T00:00:00Z }
sources:
  - id: code
    resource: "pc_act23.py: _register_open_class (:2905), _try_bind (:2921), add_object (:995), add_eigenschaft (:1002), _auto_eig_umschreiben (:1781), _eig_setzen (:1834), curious_pick (:5041)"
    title: Der Vergabepfad
  - id: laeufe
    resource: "Zwei frische 300-Episoden-Laeufe (ACT23_FRESH=1), log/pc_act23_2026-09-14_07-22-23_*.txt"
    title: Empirische Gegenprobe
---

# Was der Langlauf-Befund sagte

[Offene Faeden](/fragen/offene-faeden-act23.md), Engpass 1: 13 geborene Klassen, **alle 13**
verhungert mit derselben Meldung - *"kein Knopf zu vergeben - der Probe-Koerper ist schon
gebunden"*. Diagnostiziert als Vergabe-Engstelle.

Das stimmt, greift aber zu kurz.

# Der Pfad, Zeile fuer Zeile

    _register_open_class(cname)
        if NOVEL_BODY in state.SHAPE_KEY or NOVEL_BODY not in scene:
            print("... kein Knopf zu vergeben ...")
            return                      <- VOR _bind_hits.setdefault
        _bind_hits.setdefault(cname, [])

    _try_bind(dets)
        if NOVEL_BODY in state.SHAPE_KEY or ... or not _bind_hits:
            return
        ...
        state.add_object(label, NOVEL_BODY, cname)      <- IMMER derselbe Koerper

Der Knopf ist fest an `NOVEL_BODY` verdrahtet (Vorgabe `obj_T`). Ist er vergeben, kehrt
`_register_open_class` zurueck, **bevor** die Klasse ueberhaupt Kandidatin wird - sie steht nie in
`_bind_hits`, und `_try_bind` kann sie folglich nie binden.

> **Es kann pro Zustand genau EINE selbst geborene Klasse kommandierbar werden. Danach ist der
> Pfad zu, nicht eng.**

# Und das Eigenschafts-Kommando umgeht das NICHT

Das [Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md) wurde ausdruecklich gebaut, um
ohne Formklasse und ohne Knopf adressieren zu koennen: *"Wer so adressiert, braucht die Geburt
nicht."* `add_eigenschaft` haengt einen Eintrag an `state.OBJECTS` an, ganz ohne `shape_key`.

Es hat nur drei Aufrufer, und keiner hilft im autonomen Lauf:

    :1537  ACT23_EIG_BODY       Startvariable, EIN Koerper, von Hand
    :1838  _eig_setzen          die GUI-Waehlfelder -- braucht einen MENSCHEN, der klickt
    :1936  _auto_eig_umschreiben  `_b = state.selected()[1]` -- etikettiert den BEREITS
                                 gewaehlten Koerper um, fuehrt keinen neuen ein

Und die Auswahl selbst zieht nur aus der vorhandenen Liste:

    curious_pick():  for k, (_l, nm, _m) in enumerate(state.OBJECTS): ...

> **Im autonomen Lauf gibt es keinen einzigen Pfad, der `state.OBJECTS` erweitert.** Die
> Wuerfelei benennt um, was schon da ist. Das Werkzeug, das die Geburt umgehen sollte, kann nur
> fuer Objekte benutzt werden, die die Geburt schon hinter sich haben.

Bezeichnend: `_eig_setzen` (der GUI-Pfad) sucht seinen Koerper aus
`CommandState23.OBJECTS + state.SHAPE_KEY + [NOVEL_BODY]` - **kann** also einen Koerper einfuehren,
der nicht in der Liste steht. Der Mensch kann es, die Schleife nicht. Das ist dasselbe Muster wie
der zweimal dokumentierte [Riss zwischen den zwei
Auto-Schleifen](/mechanismen/invarianten.md): ein Mechanismus existiert im einen Pfad und fehlt im
anderen.

# Die empirische Gegenprobe

Zwei frische Laeufe (`ACT23_FRESH=1`), je 300 Episoden:

    Lauf     Geburten   "kein Knopf zu vergeben"   Knopf vergeben
      A         12               9                      1
      B          4               2                      1

    adressierte Koerper (beide Laeufe identisch):
      obj_L  obj_T  obj_U  obj_blue  obj_green  obj_red

**Genau ein Knopf je Lauf**, wie vorhergesagt. Und die Liste der adressierten Koerper besteht aus
den fuenf von Anfang an eingetragenen plus `obj_T`, der den einen Knopf bekam.

~~**`obj_X` wird in 300 Episoden kein einziges Mal adressiert** - der siebte Koerper liegt die ganze
Zeit auf dem Tisch und ist fuer das Kommando-Repertoire unsichtbar.~~

> **KORRIGIERT (2026-09-15).** Der erste Teil stimmt, die Begruendung nicht: **im frischen Lauf
> steht obj_X gar nicht in der Szene.** Nachgezaehlt - die `after ep`-Zeile fuehrt nur
> `obj_red obj_green obj_L obj_U obj_blue`, und `obj_X` kommt im gesamten Protokoll **0 mal** vor.
> Er taucht nur in Laeufen aus dem gespeicherten Zustand auf, weil er dort historisch einen Knopf
> bekam und `_try_bind` den Koerper dabei in `act16.OBJS` eintraegt. Damit schliesst sich ein
> drittes Rad: ein Koerper braucht die Szene fuer den Knopf und den Knopf fuer die Szene, und
> eingefuehrt wird nur der eine Probe-Koerper.
> Siehe [Die freie Vergabe oeffnet die erste Tuer](/befunde/freie-vergabe-erste-tuer.md).

# Was daraus folgt

Die Reparatur ist nicht "mehr Probe-Koerper". Sie ist: **die Auto-Schleife muss eine
Eigenschafts-Adresse fuer einen Koerper anlegen koennen, der noch nicht in `state.OBJECTS` steht** -
genau das, was `_eig_setzen` fuer den Menschen bereits tut. Die Maschinerie existiert, sie ist nur
nicht an die Schleife verdrahtet.

Damit waere auch der Knopf entbehrlich: eine junge Klasse braucht keinen Listeneintrag mit
`shape_key`, sondern eine Adresse aus dem, was an ihr sichtbar ist.

**Offen und hier nicht beantwortet:** ob eine so eingefuehrte Klasse dann auch ueberlebt. Der
Verhungerungsschutz zaehlt ueber Eigenschaften kommandierte Klassen als ungeschuetzt
([Der blinde Fleck der Aneignung](/befunde/aneignung-blinder-fleck.md)), und `ACT23_EIG_SCHUETZT`
war dazu gemessen wirkungslos. Es kann sein, dass die Engstelle zwei Tueren hat.

# Fallen

* **`ebene: code`** fuer die Pfadanalyse; die Zahlen aus den zwei Laeufen sind `act23-ab`, aber sie
  bestaetigen nur, was der Code sagt.
* **Zwei Laeufe, ein Seed je Lauf.** Fuer eine strukturelle Aussage ("genau ein Knopf") reicht das,
  fuer die Geburtenzahlen nicht.
* **`obj_X` hat historisch eine eigene Klasse** (`neu-285` im gespeicherten Zustand) - im frischen
  Lauf nicht. Die Aussage "nie adressiert" gilt fuer den frischen Aufbau.

# Verwandt

* [Offene Faeden](/fragen/offene-faeden-act23.md) - Engpass 1, hier praezisiert
* [Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md) - das Werkzeug, das die Geburt umgehen sollte
* [Der blinde Fleck der Aneignung](/befunde/aneignung-blinder-fleck.md) - die moegliche zweite Tuer
* [Die Geburtenrate hat zwei Ursachen](/befunde/geburtenrate-und-saettigung.md)
* [Die freie Vergabe oeffnet die erste Tuer](/befunde/freie-vergabe-erste-tuer.md) - der Einbau, und die Korrektur an dieser Seite
* [Invarianten](/mechanismen/invarianten.md) - der Riss zwischen GUI-Pfad und Auto-Schleife
