---
type: Befund
title: S1 - eingefrorener Online-Kopf bestätigt sich auf neuen Rollouts
description: Zwei neue Sammelseeds und 2400 Testübergänge bestehen das Tor ohne Nachtraining; Positions-Latent-Port für das Körpermodell geprüft.
tags: [s1, servo, latent, koerpermodell]
status: stable
evidenz: gemessen
ebene: pruefstand
sources:
  - resource: /messungen/s1-unabhaengige-rollouts.md
    title: Vor Datenerhebung festgelegtes Tor
  - resource: ../../log/s1-independent-eval-20261003/result.json
    title: Eingefrorene Auswertung samt SHA256 und Inferenzdiagnostik
  - resource: ../../log/s1-independent-20261003/seed211/manifest.json
    title: 20 neue Rollouts Seed 211
  - resource: ../../log/s1-independent-20261003/seed307/manifest.json
    title: 20 neue Rollouts Seed 307
  - resource: /mechanismen/servo-latent-port.md
    title: Implementierter separater Positions- und Übergangs-Latent-Port
---

# Ergebnis

Der eingefrorene lokal gelernte Online-Kopf besteht das vorher festgelegte Tor auf beiden
neuen Sammelseeds und gepoolt: MSE <=0,90 der Persistenz und mindestens 4/5 Gelenke besser.
Tatsächlich sind jeweils **5/5 Gelenke** und alle **40 ganzen Rollouts** besser. Kein
Parameter, Normalisierungswert oder Kopf wurde mit neuen Zeilen nachtrainiert.

| Neue Daten | Online-MSE rad² | Faktor Persistenz | Bessere Gelenke |
|---|---:|---:|---:|
| Seed 211, 20x60 Übergänge | 1,25920e-5 | 0,090772 | 5/5 |
| Seed 307, 20x60 Übergänge | 1,31145e-5 | 0,093691 | 5/5 |
| Gepoolt, 2.400 Übergänge | **1,28533e-5** | **0,092238** | **5/5** |

Gepoolte Persistenz-MSE 1,39349e-4 rad²: rund **90,78 Prozent weniger Fehler**.
Unveränderte Batch-Referenz: 1,67085e-7 rad² (Faktor 0,001199). Sie bleibt genauer, wurde
aber nicht in den Online-Kopf kopiert. Voriger Diagnosesplit: Faktor 0,0874; die neue Messung
bestätigt die Größenordnung.

# Was unabhängig ist

Neue vor Erhebung gewählte Zufallsseeds und ganze Trajektorien, alle Zeilen split=test,
keine neue Aufteilung für Lernen. Gleiches Simulator-/Aktuatormodell, gleiche begrenzte
freie Bewegungen, gleicher **20-ms-Horizont**. Das bestätigt neue Trajektorien innerhalb
dieser Verteilung, nicht reale Hardware, Kontakt, neue Lasten oder längere autonome Bewegungen.
Zeitlich abhängige Zeilen werden nicht als 2.400 unabhängige Versuche ausgegeben.

Nur joint_0 bis joint_4; Eingaben sind Encoderposition, Encodergeschwindigkeit und geplanter
Servo-Stellwert. Keine Druck-, Kontakt-, Objekt-, Teacher- oder IK-Eingaben. Gleiche innere
Stell- und äußere Encodergrenzen wie zuvor. Beide Sammlungen vollständig, keine Grenzverletzung
und keine Auswahl gültiger Teilzeilen aus gescheiterten Läufen. Kein physischer Sicherheitsnachweis.

Collector-Änderung: ausschließlich evaluation-only-Ausgabemodus, tatsächlicher Zeithorizont
im Manifest und Schutz gegen Überschreiben bestehender Ordner. Bewegungsrezept und Physik
unverändert. Originaldaten bleiben erhalten.

# Integrität und Latent-Port

Checkpoint vor/nachher bytegleich, SHA256:
`b07e4599a78029b57528553c7d8c927ecb75818cd55113f48cf00ece764016a0`.
Encoder-/Kopf-/Normalisierungsarrays unverändert. Maximaler Zustandsgradient 2,52e-7,
unter dem Tor 1e-5. Schrittfolge und Zustandsanschluss je Rollout geprüft. Einzelne neue
Eingabekomponenten liegen außerhalb der bisherigen Trainingsminima/-maxima; sie wurden
unverändert verarbeitet. Zähler je Komponente stehen im Ergebnis, keine angepasste Skalierung.

Auf Nutzerwunsch ist ein separater `ServoLatentModule`-Adapter gebaut, ohne ACT23 oder das
bestehende Körpermodell umzubauen. Gemessene Position wird reversibel als exp(i*q) erhalten;
Geschwindigkeit, aktionsbedingter 24er-Latent und vorhergesagte Position sind getrennte Ports.
Positionsblock unabhängig vom Stellbefehl und auch ohne Befehl verfügbar.
[Schema, Kontrollen und Grenzen](/mechanismen/servo-latent-port.md).

Ein künftiges Körpermodell braucht somit kein inverses Netz allein zur Wiedergewinnung
bereits vorhandener Gelenkwinkel. Es kann den Positionsblock direkt verwenden. Die Codierung
selbst ist kein gelerntes Körpermodell; dessen physikalische/visuelle Zusammenhänge bleiben
eine eigene Lernaufgabe. Der alleinige 24er-Latent wurde nicht als verlustfreier Positionscode behauptet.

# Entscheidung

S1-Vorhersage erhält die Freigabe für weitere **isolierte Körpermodell-/Anpassungsversuche**
unter diesem Messvertrag. Noch keine autonome Motorpolicy und kein globaler Engine-Austausch.
Als Nächstes einen lernenden Körpermodell-Verbraucher mit explizitem Zielsignal und
Selbstlernprüfung definieren; Positions-Latent von Beginn an als Eingabe. Encoderbasen und
gemessene versus vorhergesagte Position nicht nachträglich vermischen.

Keine bestehende PKL verändert. Neue Rohdaten/Auswertungs-NPZ unter
`log/s1-independent-20261003/` und `log/s1-independent-eval-20261003/`. Alle eigenen Läufe beendet.
