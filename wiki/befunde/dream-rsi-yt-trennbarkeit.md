---
type: Befund
title: D0 - Y und T sind im Deskriptor unterscheidbar, aber nicht fuer eine junge Open-Set-Klasse
description: Ein lokaler Oracle-Nachbar trennt Y/T meist, doch die reale Dreisicht-Anspruchsregel beansprucht 59 von 64 T-Sichten als Y. Die Formrepraesentation reicht fuer diese D0-Lernaufgabe nicht.
tags: [act23, dream-rsi, d0, wahrnehmung, formklasse, negativ]
status: stable
evidenz: einzelmessung
ebene: pruefstand
generated: { by: codex, at: 2026-09-18T05:25:00Z }
sources:
  - id: protocol
    resource: /messungen/dream-rsi-yt-trennbarkeit.md
    title: Vorab festgelegte Y/T-Trennbarkeits-Sonde
  - id: data
    resource: log/dream_rsi_d0_20260918/yt_separation_01/summary.json
    title: Zwei frische Seeds, je 3 Y-Stuetzen und 32+32 zurueckgehaltene Ansichten
  - id: rows
    resource: log/dream_rsi_d0_20260918/yt_separation_01/observations.json
    title: Einzelansprueche, Deskriptorabstaende und Lokalisierungsfehler
---

# Behauptung

Die vorhandene Formrepraesentation enthaelt ein Y/T-Signal, kann dieses aber mit einer jungen,
aus drei Blicken gebildeten Open-Set-Klasse nicht zuverlaessig nutzen. Daher ist Y gegen T
weiterhin keine zugaengliche D0-Lernaufgabe. Das ist ein Wahrnehmungs-Pruefstand, kein Befund
ueber ACT23-Ausfuehrung oder eine Aussage, dass Y und T prinzipiell ununterscheidbar seien.

# Zahlen

| Seed | Y-Anspruch | falscher T-Anspruch | 1-NN mit LOO auf 64 Testdeskriptoren | Y-Abstand p50 | T-Abstand p50 | Anspruchsradius |
|---|---:|---:|---:|---:|---:|---:|
| 1703 | 32/32 | 29/32 | 90,6 % | 6,38 | 7,44 | 12,52 |
| 1704 | 32/32 | 30/32 | 92,2 % | 6,00 | 7,76 | 12,12 |

Alle 134 Szenen einschliesslich der sechs Stuetzansichten wurden lokalisiert; der groesste
Positionsfehler betraegt 7,54 mm. Die vorab gesetzte operative Schwelle verlangt mindestens
24/32 Y-Ansprueche und hoechstens 1/32 T-Fehlanspruch je Seed. Der Y-Teil besteht, der T-Teil
verfehlt die Grenze um 28 bzw. 29 Szenen. Das Eingabe-Pickle blieb unveraendert bei SHA256
`ad9d768c...`; zwei frische cube/L/U-Bootstraps erreichen je 1,0 Trainingsgenauigkeit.

# Aufbau

Pro neuem Seed trainierte ein frischer Klassifikator auf 2500 gelabelten Grundform-Sichten.
Danach erhielt ein Wegwerf-Readout genau drei Y-Deskriptoren als hypothetische junge Klasse.
`resolve` und seine selbst kalibrierte Neuheitsschwelle blieben unveraendert; weder T noch Y
wurde im Test gelernt oder in eine Zustandsdatei geschrieben. Je 32 neue Y- und T-Bilder
variieren Tischposition, Yaw und Farbe. Die externe Koerper-ID dient nur der Auswertung.

Der LOO-1-NN nutzt dagegen alle 64 Testetiketten nachtraeglich und darf deshalb nur als
explorative Diagnose gelesen werden: Er zeigt lokale Struktur im Deskriptorraum, keine
ausfuehrbare Selbstlernleistung. Dass sein Wert hoch ist und die reale Anspruchsregel trotzdem
fast jedes T einsammelt, lokalisiert den Engpass bei Stichprobendichte, Anspruchsradius und
Perspektivstreuung der jungen Klasse, nicht bei einer vollstaendigen geometrischen Identitaet.

# Bewertung und Folgen

Die vorherige D0-Gegenprobe ist damit genauer eingeordnet: Die T-Verwechslung war kein
einzelner ungluecklicher Kontrollsatz. Sie tritt in zwei neuen Seeds unter 64 neuen T-Szenen
wieder auf. Gleichzeitig verbietet der 1-NN-Wert die vereinfachende Aussage, Y und T seien im
Merkmalsraum identisch. Eine nachtraegliche Verengung von `OPEN_MARGIN`, Dickenwache oder
Schwellensuche waere ein neuer Architekturvergleich und keine Rettung dieses Piloten; solche
Wege haben bereits eigene negative Vorbefunde.

**D0 bleibt offen.** Vor D1 braucht es eine neue Lernaufgabe, deren eigener Lernpfad sowohl
gehaltene Wiedererkennung als auch Abgrenzung gegen nahe Formen zeigt. Weitere Seeds oder
laengere Wiederholungen dieser Sonde sind nicht vorgesehen. Rohbelege liegen lokal unter
`log/dream_rsi_d0_20260918/yt_separation_01/`; der Runner ist
`src/pc_cvnn/act23_dream_rsi_yt_separation.py`.
