---
type: Entscheidung
title: Die Wissensbasis wird ein Wiki im Repo
description: Warum das Projektwissen ab 2026-09-07 als versioniertes Markdown-Wiki unter wiki/ liegt statt nur im agenteneigenen Memory-Bestand, und welche Frage dabei noch offen ist.
tags: [meta, wissensbasis]
status: stable
evidenz: vermutung
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

# Entscheidung

Das Projektwissen - Messergebnisse, Architekturentscheidungen und deren Bewertung - wird als
Wiki nach [Verfahren](/wiki.md) unter `wiki/` gefuehrt: versioniert im Repo, von jedem Agenten
lesbar und fortzuschreiben.

# Begruendung

Der bisherige Bestand lag in zwei getrennten Formen:

1. **Der agenteneigene Memory-Bestand** unter
   `~/.claude/projects/.../memory/` - 46 Dateien, inhaltlich sehr reich, aber ausserhalb des
   Repos, nicht mitversioniert, nicht mit dem Code diffbar und an einen Werkzeugtyp gebunden.
2. **Verstreute Markdown-Dateien im Wurzelverzeichnis** - `ARCHITECTURE_2026-07-25.md`,
   `RESEARCH-RESULT-001..008.md`, `experiment_log.md`, `research_journal.md`,
   `current_state.md`, `goal.md`. Teils aus frueheren Projektphasen, ohne gemeinsame Form,
   ohne Querverweise, ohne erkennbaren Aktualitaetsstand.

Beides zusammen heisst: eine Aussage findet nur, wer weiss, dass es sie gibt. Das Wiki fuegt
drei Dinge hinzu, die beide Formen nicht haben - einen **Katalog** (`index.md`), eine **Chronik**
(`log.md`) und ein **Frontmatter, das Evidenzgrad und Messebene mitfuehrt**.

# Bewertung

Die Wahl ist bewusst werkzeugarm: Markdown plus git, kein Index-Bau, keine Suchmaschine, keine
Datenbank. Der Preis ist, dass die Pflege Disziplin verlangt statt Automatik - genau das, was
die Vorlage einem Agenten zutraut und einem Menschen nicht.

# Der Zuschnitt (Nutzerentscheid 2026-09-07)

**Der act23-Teil des Memory-Bestands wandert ins Wiki, die aelteren Akte bleiben liegen.**
Konkret:

* Die ~20 act23-Notizen und die drei Prinzipien-Notizen (Projektziel, Laufzeitregeln,
  Greif-Lerndeckel) sind **uebertragen** - als Verdichtungen, nicht als Kopien. Wo eine Seite aus
  dem Bestand stammt, ist das in `sources` vermerkt.
* Die Akte **act5 bis act22** bleiben im Memory-Bestand. An ihnen wird nicht mehr gearbeitet;
  eine Uebertragung waere Aufwand ohne Gegenwert.
* Die alten Markdown-Dateien im Wurzelverzeichnis bleiben unangetastet und werden nur von
  [Rohbelege](/raw/index.md) aus referenziert - **Herkunft, nicht Wahrheit**.

# Offen

Ob das Verfahren im Alltag traegt, ist noch nicht gemessen - deshalb `evidenz: vermutung`. Nach
ein paar Wochen Gebrauch gehoert hier ein ehrliches Urteil hin: wird nach jedem Lauf wirklich
eingetragen, oder verlaeuft es wie die verstreuten Wurzeldateien davor?

# Verwandt

* [Das Verfahren](/wiki.md)
