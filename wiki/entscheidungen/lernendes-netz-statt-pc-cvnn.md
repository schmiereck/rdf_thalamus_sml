---
type: Entscheidung
title: Regel 1 heisst "lernendes Netz", nicht "PC-CVNN"
description: Nutzerentscheidung 2026-11-10 - die Architekturregel verlangt ein lernendes Netz; PC-CVNN war ein Versuch. Netze aus NetResearch (Backprop, DAgger) duerfen als Experten antreten und der Roboter dient dort als End-Benchmark.
tags: [ziel, prinzip, architektur, netresearch]
status: stable
evidenz: vermutung
ebene: code
generated: { by: claude/fable-5.2, at: 2026-11-10T12:00:00Z }
verified: { by: human:thomas, at: 2026-11-10T12:00:00Z }
sources:
  - id: nutzer
    resource: "Nutzeraussage 2026-11-10 (NetResearch-Sitzung): Regel auf lernendes Netz erweitern. PC-CVNN-Netz war dort nur ein Versuch. Umgekehrt koennen wir eben auch das Backprop bei uns erweitern."
    title: Thomas Schmiereck
  - id: experte
    resource: /entscheidungen/architektur-evolution-expertenpfad.md
    title: Architektur darf wachsen, aber nur ueber isolierte Expertenpfade
---

# Entscheidung

Die erste Architekturregel aus [Projektziel](/ziel.md) lautet ab jetzt: **Alles laeuft durch ein
lernendes Netz.** Welches Lernverfahren das Netz hat (praediktive Codierung, Backprop, DAgger,
lokale Regeln), ist nicht vorgeschrieben. PC-CVNN war ein Versuch, kein Dogma. Das schaerft, was
[Expertenpfade](/entscheidungen/architektur-evolution-expertenpfad.md) schon sagt.

Die zweite Regel (keine festen Regeln zur Laufzeit ausserhalb des Trainings) bleibt unveraendert.
Gerechnete Wahrnehmung (`perceive_all`) bleibt Uebergangsgeruest.

# Folgen

* Netze aus dem Nachbarprojekt NetResearch duerfen als Experten antreten, nach dem Verfahren der
  Expertenpfade (isolierte Aufgabe, Baseline, getrennte Halteteile, Integrationsvertrag).
* Umgekehrt darf NetResearch Verfahren von hier uebernehmen. Die Bruecke und ihre Stufen stehen in
  [Bruecke zu NetResearch](/fragen/netresearch-bruecke.md).
* Aeltere Seiten, die "PC-CVNN-Netz" als Pflicht nennen, sind in diesem Punkt ueberholt; im Zweifel
  gilt diese Seite.
