---
type: Befund
title: Der blinde Fleck der Aneignung - der Zaehler UND der Verhungerungsschutz sehen nur den Knopf
description: Beide lesen state.SHAPE_KEY und uebersehen das Eigenschafts-Kommando. Der Zaehler verfaelscht damit jede Aneignungsaussage; der Schutz entfernt Klassen, die der Agent gerade benutzt. Der Zaehler-Fix ist gebaut und verifiziert, der Schutz gebaut und mangels Geburtenrate noch nicht messbar.
tags: [act23, selbstlernen, formklassen, messfehler]
status: stable
evidenz: gemessen
ebene: code
generated: { by: claude/opus-5, at: 2026-09-11T16:00:00Z }
sources:
  - id: lauf
    resource: log/pc_act23_2026-09-10_09-10-01_8996.txt
    title: Langlauf, in dem der Widerspruch auffiel (neu-373)
  - id: smoke
    resource: "Kopfloser Steuerungslauf, 6 Episoden, Zustandskopie -- Verifikation des Zaehler-Fixes"
    title: Rauchtest nach dem Fix
---

# Zwei Stellen, ein Fehler

`state.SHAPE_KEY` ist der **Knopf**-Pfad. Seit dem
[Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md) gibt es einen zweiten Weg, eine
Klasse zu adressieren - `state.EIGENSCHAFT`. Zwei Stellen kennen ihn nicht:

    pc_act23.py:4547   acq[...]["cmd"]   -- der Aneignungs-Zaehler      -> verfaelscht die MESSUNG
    pc_act23.py:2896   protect=set(...)  -- der Verhungerungsschutz     -> veraendert das VERHALTEN

**Der zweite wiegt schwerer.** `_starve_and_cap` entfernt jede ungeschuetzte Klasse nach
`STARVE_N = 25` Blicken. Eine Klasse, die ueber Eigenschaften kommandiert wird, gilt als
ungeschuetzt - **die Aufraeum-Mechanik loescht also genau die Klassen, die der Agent gerade
benutzt.**

# Der Beleg

Im [Langlauf vom 10.09.](/befunde/langlauf-entkoppelt.md) stand `neu-373` in **allen 363**
Aneignungszeilen mit `kommandiert 0x`. Dasselbe Protokoll zeigt fuenf Kommandos:

    [Auto 409] neu-373 + mittel      [Auto 511] farbe-4 + neu-373
    [Auto 517] farbe-2 + neu-373     [Auto 610] farbe-5 + neu-373
    [Auto 614] neu-373 + mittel

Sie verhungerte trotzdem - nach 229 Episoden, als einzige der dreizehn so spaet. Und sechs der
dreizehn erreichten 50-75 % Wiedererkennung, funktionierten also und starben dennoch.

# Was gebaut ist

**1. Der Zaehler sieht beide Pfade** (unbedingt, kein Schalter - ein Messfehler wird repariert,
nicht zur Wahl gestellt). Faellt `SHAPE_KEY` leer aus und ist das Verfahren `eigenschaft`, zaehlt
die **Formachse** des Tripels.

Dazu wurde die Zahl ueberhaupt erst **sichtbar**: sie stand nur in den Zeilen junger Klassen. Fuer
die bestehenden war nicht erkennbar, ob sie benutzt werden - und ohne das ist der Fix nicht
nachpruefbar. Verifiziert im Rauchtest:[^smoke]

    [Aneignung] bestehende Klassen wiedererkannt: neu-9 100%  neu-13 0%
                neu-34 0% (1x kdo)  neu-285 57% (5x kdo)

Alle sechs Kommandos liefen ueber Eigenschaften; vor dem Fix haette dort ueberall `0x` gestanden.

**2. `ACT23_EIG_SCHUETZT` (Vorgabe 0)** nimmt die Formachsen aus `state.EIGENSCHAFT` in
`protect` auf. **Bewusst eng:** geschuetzt wird nur, was wirklich als Tripel registriert ist -
nicht jede je gesehene Klasse. Sonst verhungerte nichts mehr und der Bestand liefe in den
`MAX_OPEN = 12`-Deckel.

`state.EIGENSCHAFT` wird **nicht persistiert**, der Schutz wirkt also nur auf Tripel des
laufenden Laufs. Das ist richtig so: ein Tripel aus einem alten Lauf sagt nichts darueber, was
**jetzt** benutzt wird.

# Warum Schritt 2 noch nicht gemessen ist

Der Schutz wirkt nur, wenn eine Klasse **geboren** wird und **dann** als Formachse adressiert
wird. Im Langlauf gab es 13 Geburten auf 906 Episoden - **1,4 %**. Ein A/B ueber 120 Episoden je
Arm saehe rund **zwei** Geburten. Das ist keine auswertbare Stichprobe, und ein Null-Ergebnis
daraus waere bedeutungslos.

Ein belastbares A/B braucht entweder einige hundert Episoden je Arm oder eine erhoehte
Geburtenrate (`ACT23_NOVEL_EVERY`, Vorgabe 6). Die Vorgabe bleibt deshalb `0` - **gebaut, nicht
eingeschaltet**.

# Bewertung

* **Der Zaehler-Fix ist keine Verbesserung, sondern eine Reparatur.** Er aendert kein Verhalten,
  er macht eine Messung wieder wahr.
* **Er entwertet rueckwirkend eine Aussage.** "Keine Klasse wird je kommandiert" aus
  [Selbst-Aneignung stockt](/befunde/selbstaneignung-stockt.md) gilt fuer die dortigen
  August-Laeufe (vor dem Eigenschafts-Kommando); fuer alles danach war es teilweise ein
  Messartefakt.
* **Der Schutz ist eine Verhaltensaenderung** und braucht deshalb ein A/B, bevor er Vorgabe wird -
  auch wenn die Begruendung stark ist.

# Fallen

* **Ein zu weiter Schutz waere schlimmer als keiner.** Wuerde man jede gesehene Klasse schuetzen,
  fuellt sich der `MAX_OPEN`-Deckel mit Phantomen, und der haerteste Aufraeumer (die Kappung)
  trifft dann die falschen. Deshalb nur registrierte Tripel.
* **Die Formachse eines Tripels kann `None` sein** (reine Farb- oder Groessenadresse); das ist
  abgefangen.

# Verwandt

* [906 Episoden in der entkoppelten Welt](/befunde/langlauf-entkoppelt.md) - wo es auffiel
* [Selbst-Aneignung stockt](/befunde/selbstaneignung-stockt.md) - die betroffene Aussage
* [Formklassen-Lebenszyklus](/mechanismen/formklassen-lebenszyklus.md)
* [Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md) - der zweite Adressierungsweg
