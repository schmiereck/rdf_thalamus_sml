---
type: Entscheidung
title: D0b beginnt mit visuellem Greifzustand statt weiterer Wrist-Variation
description: Nach dem negativen D0-Wrist-Pilot wird zuerst geprüft, ob Fovea-Bildfolgen und eine eigene Hubbewegung einen gehaltenen Gegenstand selbstbeobachtbar machen. Direkte Servosteuerung und höhere Auflösung bleiben davon getrennt.
tags: [act23, dream-rsi, d0b, fovea, greifen, selbstlernen]
status: stable
evidenz: vermutung
ebene: code
generated: { by: codex, at: 2026-09-23T10:00:00Z }
sources:
  - id: d0-negative
    resource: /befunde/dream-rsi-d0-seed29-wrist-evaluation.md
    title: Negativ geschlossener D0-Wrist-Pilot
  - id: open-thread
    resource: /fragen/offene-faeden-act23.md
    title: Offener Faden zur gelernten Schliessentscheidung
  - id: fovea-plan
    resource: /fragen/dream-rsi-fovea.md
    title: F0-F3, insbesondere Objekt im Greifer als erste Fovea-Aufgabe
  - id: pressure-negative
    resource: /mechanismen/laufzeit-regeln.md
    title: Negativer Drucksensor-Weg und verbleibende Laufzeitregel
  - id: motor-plan
    resource: /fragen/dream-rsi-servosteuerung.md
    title: S0-S3, direkter Motorpfad erst mit eigenem Signal
---

# Entscheidung

Der D0-Wrist-Pilot wird nicht nachtrainiert oder durch eine weitere Wrist-Variante ersetzt.
Der nächste Kandidat heißt **D0b: visueller Greifzustand**. Zuerst wird geprüft, ob der Agent
aus Fovea-Bildfolgen und der Konsequenz einer eigenen kleinen Hubbewegung erkennen kann, ob ein
Objekt mit der Hand mitbewegt wird. Das ist eine Wahrnehmungs- und Selbstbeobachtungsaufgabe;
sie steuert anfangs weder Schließen noch die Servos.

# Warum dieser Kandidat

Der bisherige D0-Kredit enthielt genug Zeilen und Wrist-Zellen, aber die Wirkung blieb über zwei
unabhängige Trainingsseeds aus. Mehr Daten desselben Rezeptes wäre nachträgliches Tuning. Die
Drucksensor-Varianten für die Schließentscheidung sind ausdrücklich negativ geschlossen. Offen
ist dagegen ein **wahrgenommenes Objekt-im-Greifer-Signal**. Es betrifft einen dominanten
Fehler: Viele Greifmisserfolge entstehen, weil die Klaue nichts trägt. Gleichzeitig erfüllt es
den Wunsch, die vorhandene Fovea für weitere Aufgaben zu verwenden, ohne ihren gewachsenen
Zustand oder die Auflösung vorschnell umzubauen.

Die Aufgabe hat einen beobachtbaren Lernkanal: Nach einem normalen Schließen führt der Agent
eine kurze, vorab festgelegte Hubbewegung aus. In zwei zeitlich getrennten Fovea-Blicken wird
gemessen, ob ein Kandidat relativ zur Hand konsistent mitwandert. Dieses Bewegungsereignis ist
das Trainingssignal. Simulator-Kontakt, Weld-Status und Objektpose dürfen ausschließlich in
einem getrennten Auswertungsprotokoll stehen, nie als Lerninput oder Trainingsetikett.

# D0b-Vorprüfung und Vertrag

Vor jedem neuen Training werden diese Punkte als eigener Vertrag festgelegt und geprüft:

1. **Beobachtbarkeit:** Fovea-Blick vor Hub, während Hub und danach samt Handpose, Zeitstempel,
   Objektkandidat und Gültigkeit erfassen. Die Daten werden nach Szene und Trajektorie getrennt,
   nicht zeilenweise zufällig.
2. **Selbstetikett:** Ein positives Etikett entsteht nur aus sichtbarer, zeitlich konsistenter
   Mitbewegung; fehlende Sicht, Verdeckung oder mehrdeutige Zuordnung ist Enthaltung. Es gibt
   keine Umdeutung in ein negatives Etikett.
3. **Diagnose gegen Grundwahrheit:** Auf zurückgehaltenen Szenen wird Precision, Recall,
   Kalibrierung und Enthaltungsquote des Selbstetiketts gegen getrennte Simulator-Grundwahrheit
   gemessen. Diese Messung entscheidet, ob das Selbstetikett tragfähig ist.
4. **Repräsentation vor Eingriff:** Ein kleiner Auslesekopf auf eingefrorenen Fovea-Zuständen
   wird gegen Rohzellwerte, untrainierte Zustände und eine Konstantvorhersage verglichen. Erst
   wenn der Fovea-Zustand ein gehaltenes Signal auf gehaltenen Szenen trägt, darf ein lernender
   Kopf angeschlossen werden.
5. **Handlungswirkung getrennt:** Erst nach bestandenem Wahrnehmungstor darf ein einziger
   gelernter Verbraucher die Schließ-/Abbruchentscheidung beeinflussen. Der Test schaltet
   Druckregel, Reflex und jede Simulatorinformation für diese Entscheidung aus und protokolliert
   deren Nichtbenutzung. Lieferung ist dann eine Regression, kein Ersatz für den
   Wahrnehmungsnachweis.

Das erste Tor ist damit absichtlich kleiner als der frühere Wrist-Vertrag: D0b behauptet noch
keine bessere Lieferquote und keine direkte Motorik. Es muss zuerst zeigen, dass der Agent eine
für seine eigene Handlung relevante, neue Zustandsvariable aus zugänglicher Wahrnehmung bilden
kann.

# Bewusst zurückgestellte Wege

**Kein erneuter Wrist-Kredit:** Er wäre eine Variation des gerade über zwei Trainingslinien
negativ geprüften Rezeptes. Ein anderer Kreditkanal wäre nur nach einem neuen, unabhängig
nachgewiesenen Wahrnehmungssignal ein neuer Kandidat.

**Keine Auflösungserhöhung als erster Schritt:** Mehr Pixel lösen keine fehlende zeitliche
Bindung oder eine unklare Sichtbarkeit. F16 bleibt eingefroren, bis D0b auf gehaltenen Daten
zeigt, dass Detailauflösung der begrenzende Informationsfaktor ist. Dann folgt der bereits
geplante, bestandserhaltende F2-Zweig.

**Keine direkte Servosteuerung als Ersatzpilot:** Der S0-Motorpfad bleibt ein eigenständiger
Forschungszweig. Ohne einen verlässlichen Hand-/Objektzustand wäre seine erste Greifaufgabe
schlecht beobachtbar und würde die bereits negativen Teacher-nahen Greifversuche vermischen.
Nach D0b kann der visuelle Zustand später ein möglicher Sensor für S2 sein, aber weder Fovea
noch Servo werden vorab als Wirkung ausgegeben.

# Nächster konkreter Schritt

Der [Portaudit](/befunde/d0b-fovea-portaudit.md) bestätigt Instrumentierung, Hubabdeckung und die
strikte Trennung der Auswertungswahrheit auf eingefrorenen Kopien. Die Gegenprüfung verwirft das
verkürzte Signal „Fovea-Auswahl sichtbar“: ein Fehlgriff besitzt dieselbe Auswahl über eine
vollständige Carryphase. Handlandmark und drei isolierte Fovea-Landmark-Ausleser wurden daraufhin
negativ geprüft.

Der neue [Hubantwort-Befund](/befunde/d0b-hubantwort.md) umgeht die fehlende Handposition ohne
Homographie: Während des Hebens bleibt der Blick fixiert und der Auswahl-Schwerpunkt verschiebt
sich in der ersten Stichprobe bei getragenen Trajektorien stärker. Die danach fixierte,
enthaltende Rohantwort scheitert jedoch schon auf Seed 103 an drei falsch-positiven Fehlgriffen
(Precision 0,786 statt 0,80). Sie wird nicht nachoptimiert oder integriert. Ein Lernvergleich
und jeder Eingriff in Schließen oder Servos bleiben gesperrt, bis eine neue, unabhängige
Wahrnehmungshypothese einen eigenen Vertrag besteht.
