---
type: Befund
title: S1-PC-Vorwärtsmodell - generativer Ein-Latent-Experte verliert klar gegen Persistenz
description: Der isolierte komplexe PC-Experte rekonstruiert die Servoübergänge besser als eine Konstante, verfehlt aber die kurzfristige Encoder-Persistenz um Faktor 154.
tags: [act23, dream-rsi, s1, servo, propriozeption, pc-cvnn]
status: stable
evidenz: einzelmessung
ebene: pruefstand
generated: { by: codex, at: 2026-09-27T09:00:00Z }
sources:
  - id: contract
    resource: /messungen/s1-pc-vorwaertsmodell.md
    title: Vorab festgelegter PC-Vertrag und Ergebnis
  - id: tool
    resource: ../../src/pc_cvnn/act23_s1_pc_forward_audit.py
    title: Isolierter komplexer PC-Forward-Audit
  - id: data
    resource: ../../log/s1-proprio/seed101-50x60-safe/transitions.jsonl
    title: Trajektoriengetrennter druckfreier Servoübergangssatz
  - id: result
    resource: ../../log/s1-pc-forward/seed17.json
    title: Unveränderliche Audit-Auswertung
---

# Behauptung

Der erste komplexe PC-Vorwärtsmodellexperte ist für die direkte Servoaufgabe ungeeignet. Seine
gemeinsame generative Rekonstruktion von Kontext und Folgezustand bildet die sehr kleine
kurzfristige Servodynamik nicht präzise genug ab.

# Zahlen

| Testmaß, 600 ganze Testübergänge | MSE rad² |
|---|---:|
| PC-Experte | 0,021131 |
| konstante Trainingsmitte | 0,065823 |
| Persistenz `q_next=q` | 0,000138 |
| PC / Persistenz | 153,59× |
| Gelenke besser als Persistenz | 0 / 5 |

Die Daten und der Experte enthalten keinen Drucksensor, Kontakt, Objekt, Kamera, IK oder
Teacher. Die Prüf- und Trainingsrollouts sind vollständig getrennt.[^contract]

# Bewertung

Der PC-Experte lernt gegenüber einer Konstante etwas von der Gelenkverteilung. Für eine
Motorikvorhersage ist das wertlos, weil der echte Schritt bei diesem kurzen Takt fast vollständig
durch den aktuellen Encoderzustand erklärt wird. Die Persistenzreferenz ist deshalb die richtige
und deutlich strengere Kontrolle.

Dieser Befund widerlegt weder direkten Servoansatz noch Propriozeption. Er verwirft die konkrete
Architektur: ein einzelner latenter generativer Knoten, der Kontext und `q_next` zugleich
dekodiert, ist kein brauchbares bedingtes Vorwärtsmodell für diese Daten.

# Folgen

Keine Epochen-, Größen- oder Lernraten-Suche und keine inverse Policy auf diesem Modell. S1 bleibt
offen, braucht aber eine neue Vorhersagehypothese mit eigenem Vertrag, etwa eine explizite
aktionskonditionierte Delta-Darstellung und eine Mehrschrittprüfung. ACT23 bleibt unverändert.
