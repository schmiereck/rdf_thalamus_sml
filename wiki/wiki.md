---
type: Referenz
title: Das Verfahren
description: Wie dieses Wiki funktioniert - Aufbau, Frontmatter, Operationen. Angepasst aus Karpathys LLM-Wiki und dem Open Knowledge Format v0.2.
tags: [meta, verfahren]
status: stable
evidenz: gemessen
ebene: code
generated: { by: claude/opus-5, at: 2026-09-07T00:00:00Z }
sources:
  - id: llm-wiki
    resource: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
    title: LLM Wiki (Karpathy)
  - id: okf
    resource: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md
    title: Open Knowledge Format v0.2
---

# Woher das kommt

Zwei Vorlagen, beide bewusst abgewandelt:

* **LLM Wiki** liefert die **Idee**: nicht bei jeder Frage aus Rohmaterial neu synthetisieren
  (RAG), sondern ein dauerhaftes, verlinktes Markdown-Wiki fortlaufend fortschreiben. Das
  Wissen wird einmal verdichtet und dann *aktuell gehalten*, nicht bei jeder Frage neu
  hergeleitet.[^llm-wiki]
* **Open Knowledge Format v0.2** liefert das **Dateiformat**: ein Verzeichnisbaum aus Markdown
  mit YAML-Frontmatter, reservierte `index.md`/`log.md`, Herkunft (`sources`), Vertrauen
  (`generated`/`verified`), Lebenszyklus (`status`/`stale_after`), Verlinkung als gewoehnliche
  Markdown-Links.[^okf]

[^llm-wiki]: LLM Wiki (Karpathy)
[^okf]: Open Knowledge Format v0.2

# Die eine wesentliche Abweichung

Beide Vorlagen gehen von **fremdem** Material aus, das ein Mensch einsammelt und das der Agent
einsortiert. Hier ist es umgekehrt: der groesste Teil des Wissens **entsteht in diesem Projekt
selbst** - Messlaeufe, A/B-Vergleiche, Architekturentscheidungen und deren Bewertung. Externe
Quellen (Papers, Doku) kommen selten dazu.

Daraus folgen drei Anpassungen:

1. **Die Rohschicht ist die Beweisschicht.** `raw/` sammelt keine fremden Dokumente, sondern
   zeigt auf die eigenen unveraenderlichen Belege: Laufprotokolle unter `log/`, Auswertskripte,
   Commits, Plots. Sie werden **nicht kopiert**, nur referenziert. Kein Wiki-Satz ohne Beleg.
2. **Der Evidenzgrad ist ein Feld, keine Prosa.** In diesem Projekt sind mehrfach Vermutungen
   aus kleinen Stichproben als Befund durchgegangen und spaeter widerlegt worden. Deshalb
   tragen `evidenz` und `ebene` im Frontmatter, was eine Aussage traegt.
3. **Ehrliche Negative sind vollwertige Seiten.** Ein gemessenes "bringt nichts" ist hier das
   haeufigste und teuerste Ergebnis. Es wird als `Befund` mit `evidenz: gemessen` abgelegt,
   nicht weggeworfen und nicht relativiert.

# Aufbau

```
wiki/
  wiki.md            dieses Dokument
  index.md           Katalog aller Seiten (Einstieg beim Suchen)
  log.md             Chronik, neueste zuerst
  befunde/           gemessene Ergebnisse, einschliesslich ehrlicher Negative
  mechanismen/       wie ein Teil des Systems funktioniert (Module, Wahrnehmung, Griff, Lernpfade)
  entscheidungen/    getroffene Entscheidungen samt Begruendung und spaeterer Bewertung
  messungen/         reproduzierbare Messvorschriften (Skript + Schalter + Kriterium)
  fragen/            offene Fragen und Hypothesen, die noch keine Messung haben
  chronik/           je Entwicklungslinie eine verdichtete Zeitachse: was wann warum entstand
  raw/               Verweise auf Rohbelege (Logs, Skripte, Commits) und seltene externe Quellen
```

Die **Konzept-ID** einer Seite ist ihr Pfad ohne `.md`, z.B. `befunde/exekutionsvarianz`.
`index.md` und `log.md` sind reserviert und keine Konzeptseiten.

# Frontmatter

```yaml
---
type: Befund                      # PFLICHT
title: Ausfuehrungsvarianz ist nicht der Deckel
description: Ein Satz, der in den Katalog passt.
tags: [act23, weltmodell]
status: stable                    # draft | stable | deprecated | widerlegt
evidenz: gemessen                 # vermutung | einzelmessung | gemessen | widerlegt
ebene: act23-ab                   # code | pruefstand | act23-ab | langlauf
generated: { by: claude/opus-5, at: 2026-08-11T12:29:00Z }
verified: { by: human:thomas, at: 2026-08-11T13:00:00Z }
stale_after: 2027-01-01T00:00:00Z # optional
sources:
  - id: exv-lauf
    resource: /raw/index.md
    title: log/pc_act23_2026-08-11_10-52-00.txt, 6732 Weltzeilen
---
```

**`type`** ist das einzige immer erforderliche Feld. Verwendete Werte: `Befund`, `Mechanismus`,
`Entscheidung`, `Messvorschrift`, `Frage`, `Referenz`. Neue Typen sind erlaubt; wer liest, muss
unbekannte Typen einfach als Konzept behandeln.

**`evidenz`** - was die Aussage traegt:

| Wert            | Bedeutung                                                            |
|-----------------|----------------------------------------------------------------------|
| `vermutung`     | plausibel, nicht gemessen. Darf nie als Befund zitiert werden.        |
| `einzelmessung` | eine Stichprobe, keine Kontrolle, kein p-Wert. Nur Richtungsangabe.   |
| `gemessen`      | A/B mit Kontrolle, n und Streuung im Text. Belastbar.                 |
| `widerlegt`     | war einmal geglaubt, ist gemessen falsch. Seite bleibt stehen.        |

**`ebene`** - wo gemessen wurde. Das ist die teuerste Lehre dieses Projekts:

| Wert         | Bedeutung                                                               |
|--------------|-------------------------------------------------------------------------|
| `code`       | am Quelltext verifiziert, nicht gefahren                                 |
| `pruefstand` | isolierter Teilaufbau (Greif-Pruefstand, Wahrnehmungssonde, Offline-Fit) |
| `act23-ab`   | sauberes A/B im vollen act23-Lauf                                        |
| `langlauf`   | GUI-Langlauf ueber hunderte Episoden                                     |

> **Regel:** ein `pruefstand`-Ergebnis sagt einen act23-Lauf **nicht** vorher. Das ist hier
> dreimal dokumentiert schiefgegangen - siehe [Prueftstandsfalle](/mechanismen/pruefstandsfalle.md).
> Wer eine Wirkung auf act23 behaupten will, braucht `ebene: act23-ab` oder hoeher.

**`status`** - `draft` (unfertig), `stable` (Vorgabe), `deprecated` (ueberholt, bleibt fuer
Verweise), `widerlegt` (inhaltlich falsch; der Text bleibt, weil der Irrweg selbst Wissen ist).
Fehlt `status`, gilt `stable`.

**`sources`** - woraus die Seite stammt. Jeder Eintrag braucht `resource` (Pfad, URL oder
Bereichsbeschreibung); `id` erlaubt die Zuordnung einzelner Aussagen per Markdown-Fussnote:

```markdown
ICC 0,61 ueber 40 Szenen.[^exv-lauf]

[^exv-lauf]: log/pc_act23_2026-08-11_10-52-00.txt
```

Die Fussnoten-Marke ist der Schluessel in `sources` - deshalb eine stabile `id` und keine
Position (`sources[0]`): Agenten schreiben diese Listen staendig um.

**Akteure** in `generated.by` / `verified[].by`: `claude/opus-5` fuer Agenten, `human:thomas`
fuer den Menschen, `process:<name>` fuer automatische Laeufe. Nur ein `human:`-Eintrag unter
`verified` bedeutet "vom Menschen geprueft".

# Koerper einer Seite

Freies Markdown, aber Struktur vor Prosa. Diese Ueberschriften haben feste Bedeutung und sollen
benutzt werden, wo sie passen:

| Ueberschrift    | Zweck                                                                  |
|-----------------|------------------------------------------------------------------------|
| `# Behauptung`  | die Aussage in ein bis zwei Saetzen, ohne Einschraenkungen              |
| `# Zahlen`      | n, Werte, Kontrolle, p. Roh, ohne Interpretation                        |
| `# Aufbau`      | wie gemessen wurde; verlinkt die Messvorschrift                         |
| `# Bewertung`   | was das heisst - und ausdruecklich, was es **nicht** heisst             |
| `# Fallen`      | Fehllesungen, die hier schon passiert sind (eigene ausdruecklich auch)  |
| `# Folgen`      | was daraufhin im Code geaendert wurde, mit Commit                       |

`# Aufbau` bei einer `Messvorschrift` traegt den ausfuehrbaren Befehl. OKF nennt so etwas eine
*attested computation* und verlangt Quittung plus Pruefcode; hier genuegt die schwaechere Form:
Skript, Schalter, Seed und Abbruchkriterium so notiert, dass ein zweiter Lauf dieselbe Zahl
liefert.

# Verlinkung

Gewoehnliche Markdown-Links. Bundle-relativ mit fuehrendem `/` ist bevorzugt, weil es beim
Verschieben stabil bleibt: `[Exekutionsvarianz](/befunde/exekutionsvarianz.md)`.
**Das `/` meint die Bundle-Wurzel `wiki/`, nicht die Repo-Wurzel** - ein Markdown-Betrachter
loest solche Links deshalb nicht auf, `grep` und `cat` schon. Auf Dateien ausserhalb des Bundles
(Quelltext, alte Dokumente) wird relativ verwiesen: `../ARCHITECTURE_2026-07-25.md`. Ein Link auf
eine noch nicht geschriebene Seite ist **kein Fehler** - er markiert Wissen, das noch fehlt.
Beim Aufraeumen werden solche Luecken eingesammelt.

# Operationen

**Eintragen.** Nach jedem Lauf, jeder Entscheidung, jedem Befund: Seite anlegen oder
fortschreiben, `index.md` ergaenzen, Eintrag in `log.md`. Ein einzelnes Ergebnis beruehrt
typischerweise mehrere Seiten - den Befund selbst, die Frage, die er beantwortet, den
Mechanismus, den er beschreibt. Widerspricht das Neue einer bestehenden Seite, wird die alte
**nicht geloescht**: `status: widerlegt` setzen, den Widerspruch auf beiden Seiten benennen,
verlinken.

**Nachschlagen.** Erst `index.md` lesen, dann in die Seiten. Bei act23-Arbeit ist
[die Modullandschaft](/mechanismen/act23-modullandschaft.md) der Einstieg. Antworten, die Arbeit
gekostet haben, gehoeren zurueck ins Wiki - eine gute Analyse darf nicht im Chatverlauf
versickern.

**Aufraeumen.** Von Zeit zu Zeit pruefen: widersprechen sich Seiten? Sind Aussagen durch neuere
Laeufe ueberholt (`stale_after`, `generated.at`)? Gibt es verwaiste Seiten ohne eingehende
Links? Werden Begriffe benutzt, die keine eigene Seite haben? Steht irgendwo eine `vermutung`,
die inzwischen messbar waere?

# Was bewusst weggelassen ist

* **Keine Suchmaschine.** Bei dieser Groesse reicht `index.md` plus `grep`. Erst wenn das
  spuerbar nicht mehr traegt, ist ein Werkzeug faellig.
* **Keine Attester.** OKF sieht deterministischen Pruefcode vor, der die Quittung eines Laufs
  gegenprueft. Hier genuegt der reproduzierbare Befehl in `# Aufbau`.
* **Kein zentrales Typ-Register**, keine Pflichtwerkzeuge, kein Bauschritt. Wer `cat` kann,
  kann das lesen.
