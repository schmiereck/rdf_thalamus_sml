---
type: Befund
title: B1-Abdeckung - die Kamera verfehlt meist die Klauen, der Gelenkraum ist dünn belegt
description: Exakter Replay aller 224 Posen zeigt 145 Fälle mit beiden Klauen außerhalb des Bildes; Testfehler bleibt auch innerhalb der Trainingshülle erhöht.
tags: [s1, koerpermodell, kamera, abdeckung]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: codex, at: 2026-10-03 }
sources:
  - resource: /messungen/s1-koerpermodell-abdeckung.md
    title: Vorab festgelegte Diagnose, keine neue Erfolgsgrenze
  - resource: ../../src/pc_cvnn/act23_s1_body_coverage_audit.py
    title: Reproduzierbarer Audit und Abbildung
  - resource: ../../log/s1-body-coverage-20261003/result.json
    title: Zusammenfassung mit Hashkontrollen
  - resource: ../../log/s1-body-coverage-20261003/pose-coverage.json
    title: Gelenkabstände, Hülle und Fehlergruppen
  - resource: ../../log/s1-body-coverage-20261003/train401-evaluation.json
    title: Sichtbarkeit und Kameraprojektion aller Trainingsposen
  - resource: ../../log/s1-body-coverage-20261003/test409-evaluation.json
    title: Sichtbarkeit und Kameraprojektion aller Testposen
---

# Behauptung

Die bestehende B1-Kombination aus S1-Bewegungsbox und Übersichtskamera ist **für ein
visuelles Handmodell schlecht geeignet**: In 145/224 Posen liegen beide Klauenboxen vollständig
außerhalb des Kamerabilds. Höhere Auflösung bei gleichem Bildausschnitt löst diese Fälle nicht.
Zusätzlich ist die räumliche Abdeckung im fünfdimensionalen Gelenkraum dünn. Beides ist kein
vollständiger kausaler Nachweis für den RGB-Generaliserungsfehler des [B1-Decoders](/befunde/s1-visuelles-koerpermodell.md).

# Kontrollen

160 Trainingsposen und 64 Testposen separat vom ursprünglichen Simulationsstart wiederholt,
mit den gespeicherten Stellwerten und je 400 Physikschritten. **224/224 Encodervektoren,
Geschwindigkeiten, Greiferstellungen, Zeitstempel und RGB-Bilder exakt reproduziert.**
Keine Zeile entfernt, kein Fit, keine neue Kameraeinstellung und keine Änderung am Decoder.
Originaldaten, Modell, Vorhersagen und B1-Ergebnis behalten ihre SHA256-Prüfsummen.

Geometrie-IDs liest ausschließlich der getrennte Evaluator. Segmentierung nutzt die echte
Verdeckung des Renderers. Acht Eckpunkte jeder Klauenbox werden in die unveränderte
96×96-Kamera projiziert: vollständig jenseits einer gemeinsamen Bildkante bedeutet eindeutig
außerhalb. Projektionsachsen an bekannten Punkten geprüft; bei allen Posen wird außerdem
geprüft, dass eine so außerhalb liegende Box keine sichtbaren Segmentierungspixel hat.
Diese Daten sind keine Lernetiketten und kein neuer Laufzeit-Landmark.

# Kamerasicht

| Messgröße | Training (160) | Test (64) |
|---|---:|---:|
| Irgendein Armteil einschließlich Sockel sichtbar | 160 | 64 |
| Mindestens eine Klaue mit mindestens einem sichtbaren Pixel | 53 | 22 |
| Beide Klauen sichtbar | 17 | 3 |
| Beide Klauenboxen vollständig außerhalb des Bildes | 106 | 39 |
| Mindestens ein Klauenzentrum im Bild | 46 | 16 |
| Kein Klauenpixel, aber nicht beide Boxen eindeutig außerhalb | 1 | 3 |
| Mittlere sichtbare Klauenfläche bei 96×96 | 12,63 Pixel | 10,75 Pixel |
| Mittlere äquivalente Fläche nach Pooling auf 24×24 | 0,789 Pixel | 0,672 Pixel |
| Mindestens eine 24×24-Zelle mit ≥50 % Klauenbelegung | 50 | 18 |

Flächenmittel schließen unsichtbare Posen mit null ein. Über alle 224 Posen ist wenigstens
eine Klaue in 75 Fällen (33,5 %) sichtbar, beide nur in 20 (8,9 %). Bei vier unsichtbaren
Fällen ist das eindeutige Außerkamera-Kriterium nicht erfüllt; Verdeckung oder Rasterauflösung
sind ohne weitere Messung nicht unterschieden. Sichtbarkeit eines Pixels ist zudem noch
keine brauchbare Auflösung für einen Handlandmark.

„Arm sichtbar“ ist kein Gegenargument: Die Maske enthält auch die stationäre Basis.
Die beiden festen Bildbeispiele zeigen diese deutlich. 84,7 % der Trainings-Bildvarianz
liegen in 24×24-Zellen, die irgendwann Arm enthalten. Das ist eine Ortsüberlappung, keine
semantische Zerlegung: wechselnde Verdeckung und Schatten bleiben mögliche Beiträge.
Der Befund lautet deshalb nicht „das Netz lernt ausschließlich Hintergrund“.

# Gelenkraum und Generalisierung

Abstände: euklidisch in fünf gemessenen Gelenkwinkeln, jede Achse durch die feste Breite
des S1-Kommandobereichs geteilt. Keine testbasierte Skalierung oder neue Modellwahl.

| Messgröße | Ergebnis |
|---|---:|
| Nächste andere Trainingspose, Median | 0,26081 |
| Nächste Trainingspose für Test, Median | 0,26512 |
| Test außerhalb mindestens eines marginalen Trainings-Min/Max | 3 / 64 |
| Test innerhalb der konvexen Trainingshülle | 28 / 64 |
| Test außerhalb der konvexen Trainingshülle | 36 / 64 |
| Rangkorrelation Abstand / Decoderfehler, beschreibend | 0,36058 |

Die ähnlichen Nachbarabstände stützen **keinen starken Train-/Test-Verteilungsbruch**.
Die Stichproben stammen weiterhin aus derselben Erhebungsregel. Eine konvexe Hülle in fünf
Dimensionen kann trotz ähnlicher Randverteilungen viele neue Punkte ausschließen; das ist
kein Beleg für einen fehlerhaften Split. Es zeigt die begrenzte gemeinsame räumliche Abdeckung.

| Gruppe | n | Decoder-MSE | Verhältnis zum Mittelbild derselben Gruppe |
|---|---:|---:|---:|
| Nähere Hälfte der Testposen | 32 | 0,00117852 | 1,16337 |
| Fernere Hälfte | 32 | 0,00190406 | 1,36496 |
| Innerhalb Trainingshülle | 28 | 0,00104905 | 1,12482 |
| Außerhalb Trainingshülle | 36 | 0,00192414 | 1,35978 |

Auch die nähere Hälfte und die Punkte innerhalb der Hülle schlagen das Mittelbild nicht.
„Nur mehr Randposen hinzufügen“ ist somit nicht als ausreichende Reparatur belegt.
Die Auswertung ist nachgelagert auf bereits bekanntem Testseed 409; weder kausale
Abdeckungsintervention noch unabhängiger Wirksamkeitsnachweis.

# Entscheidung und nächster Schritt

**Vor neuem Training zuerst den visuellen Erhebungsaufbau korrigieren und auditieren.**
Eine feste zusätzliche Körperansicht beziehungsweise ein passender fester Blick soll den
relevanten Bewegungsraum tatsächlich sehen. Zunächst nur an Trainings-/Einrichtungsposen
Sichtbarkeit und Detailauflösung prüfen; Kriterien vor neuer Erhebung festlegen. Keine
geometrische Handkoordinate als Decoderziel übernehmen. Spätere Hardware braucht ebenfalls
einen geeigneten realen Kamerablick und zeitlich zugeordnete Encoderbilder.

Erst danach einen neuen B2-Vertrag mit neuen, unberührten Testposen und besser verteilter
Trainingserhebung festlegen. Gleichen Decoder als Ausgangskontrolle beibehalten, damit
eine Änderung des Beobachtungsaufbaus nicht gleichzeitig mit einer Netzänderung vermischt
wird. Weitere Architekturentscheidungen anhand dieser Kontrolle treffen, nicht anhand von
Nachoptimierung auf Seed 409. Größere Fovea bleibt optional; zunächst muss die Hand im Blick sein.

B1 bleibt ein gültiges Negativ für seinen eigenen Bildvorhersagevertrag, wird nicht gelöscht
oder nachträglich bestanden erklärt. Positions-Latent und erfolgreicher propriozeptiver
S1-Forecast sind unverändert. Keine ACT23-Integration, keine Änderung gemeinsamer PKLs.

# Artefakte

`log/s1-body-coverage-20261003/`: `result.json`, `pose-coverage.json`, beide
`*-evaluation.json`, zwei `*-evaluation-masks.npz`, `coverage.png`. Masken sind bewusst
vom Lern-Datensatz getrennt. Die Abbildung zeigt Sichtbarkeitsquoten, Fehler über
Gelenkabstand und die festen Testposen 0/1. Kein Lauf mehr aktiv.
