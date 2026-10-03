---
type: Frage
title: Direkte Servosteuerung als gelernter Motorpfad
description: "Optionaler Forschungszweig S0-S3: kartesische Ausfuehrung schrittweise durch einen lernenden Motorpfad ersetzen, mit eigener Anpassung als Erfolgskriterium."
tags: [act23, dream-rsi, motorik, servos, selbstlernen]
status: draft
evidenz: vermutung
ebene: code
generated: { by: codex, at: 2026-09-17T16:44:47Z }
sources:
  - id: auftrag
    resource: "Nutzerwunsch 2026-09-17: ein oder mehrere Module, die den Arm direkt ueber Servos statt Zielpositionen steuern"
    title: Optionaler Forschungswunsch
  - id: motor
    resource: src/pc_cvnn/arm_modules/motor.py
    title: Bestehendes MotorModule liefert subgoal(4), keine direkten Servokommandos
  - id: ausfuehrung
    resource: src/pc_cvnn/pc_act16.py
    title: run_combined und body.reach_velocity im Codex-Stand b3a38bf
  - id: sim
    resource: src/pc_cvnn/pc_act14.py
    title: target, set_arm_targets und set_arm3_targets
  - id: aktoren
    resource: src/pc_cvnn/assets/bracket_arm.xml
    title: MuJoCo-Positionsaktuatoren m0 bis m5
  - id: negativ
    resource: /befunde/greif-lerndeckel.md
    title: Bisherige Greif-Lernversuche und ihr begrenzter Spielraum
---

# Forschungsfrage und Bedeutung von direkt

Kann ein lernender Motorpfad aus Wahrnehmung, Propriozeption und einer Aufgabenrepraesentation
direkt die Gelenkaktuatoren ansteuern und sich aus eigenen Versuchen an veraenderte Bedingungen
anpassen? Die Forschung ist Teil des [Gesamtplans](/fragen/dream-rsi-forschungsplan.md),
Paketstatus S0-S3 steht dort. Erfolg muss den Teacher nicht uebertreffen.

Die aktuelle Architektur liefert kartesische Zwischenziele; `body.reach_velocity` setzt sie
in Gelenkbewegungen um. Auch das vorhandene `MotorModule` liefert `subgoal = [aim_xyz, gripper]`.
Es ist daher kein bereits fertig vorhandener direkter Servo-Lerner. Die Aktuatoren der
gelesenen XML sind Positionsservos: ein Wert in `ctrl` ist dort eine Winkelvorgabe und kein
Drehmoment.

| Stufe | Gelernte Ausgabe | Bedeutung fuer den Nutzerwunsch |
|---|---|---|
| S1/S2, erster Entwurf | Gelenkweise Stellwerte oder Stellwertaenderungen, einschliesslich spaeterem Wrist/Greifer | Kein erzeugtes kartesisches `aim_xyz` und kein nachgeschaltetes `reach_velocity` im geprueften Motorpfad; der physische Positionsservo bleibt. |
| S3, optional | Geschwindigkeits- oder Drehmomentkommandos | Auch der Winkel-Sollwertregler kann entfallen; braucht einen anderen Aktuatorvertrag und eine eigene Versuchsserie. |

Die erste Stufe erfuellt die Lesart **direkt an die Gelenkservos statt ueber Hand-Zielpositionen**.
Wenn auch Gelenk-Sollpositionen entfallen sollen, ist erst S3 die gewuenschte Stufe. Diese
Unterscheidung ist vor der Umsetzung von S0 festzuhalten. Ein abstraktes Aufgabenziel darf
beide Varianten weiterhin konditionieren; es wird nicht als naechste Handposition ausgefuehrt.

# Was die bisherigen Negative aussagen

Der [Greif-Lerndeckel](/befunde/greif-lerndeckel.md) zeigt Probleme von RL, Suche und
Modell-Argmax beim Einsammeln eines kleinen Restgewinns ueber einem starken Teacher. Das ist
kein kontrollierter Nachweis, dass jeder gelernte direkte Motorpfad unnuetz ist. In den hier
gelesenen Wiki-Seiten ist ein solcher allgemeiner Nachweis nicht vorhanden. Aeltere Versuche
sind in S0 zu inventarisieren, bevor eine bereits getestete Idee wiederholt wird.

Die einschlaegigen Gegenbefunde bleiben dennoch verbindlich:

- [Latent-Attraktor](/befunde/latent-etappen.md): ein duenn trainiertes Dynamikmodell darf
  nicht durch Aktionssuche ausgenutzt werden; niedriger Ein-Schritt-Fehler allein reicht nicht.
- [Laufzeitregeln](/mechanismen/laufzeit-regeln.md): ACT23 hat die Schliessentscheidung noch
  nicht ohne Riegel/Reflex gelernt. Entfernen ist ein gekoppeltes Lernexperiment.
- [Fingerdruck](/befunde/griff-glaube-und-tastsinn.md): derselbe Tastsinn ist ohne neues Signal
  kein begruendeter erneuter Weg zur Schliessentscheidung.
- [Invarianten](/mechanismen/invarianten.md): `set_arm3_targets` setzt `joint_4` zurueck.
  Ein neuer Aktuatorpfad muss alle beanspruchten Kanaele kontrollieren; kein zweiter Schreiber.

# Geplanter Modulvertrag

Entwurf fuer ein `ServoMotor`-Modul: Eingaben sind gemessene Gelenkstellungen/-geschwindigkeiten,
vorherige Stellwerte, wahrgenommener Hand-/Objektzustand samt Gueltigkeit und ein Aufgabenlatent.
Ausgaben sind Stellwerte pro aktivem Aktuator zu einem expliziten Steuerungstakt. Der Vertrag
legt Einheiten, Kanalreihenfolge, Integrationsschritt und Sattigung offen.

Das Zielmodul darf Aufgaben repraesentieren; `BodyModel` kann fuer Vorhersage und Training
weiterleben. Im autonomen Motorpfad darf dessen inverse Abbildung die Aktionswahl nicht
heimlich ersetzen. Ein Test protokolliert Aufrufe von IK, kartesischer Zielausfuehrung und
Teacher-Aktionsuebernahme. Vorhersagefehler aus eigenen Uebergaengen koennen ein lernendes
PC-CVNN-Koerper-/Dynamikmodell trainieren. Wie diese Uebergaenge die Motorpolicy verbessern,
wird in S1 als expliziter Lernverlust und Updatepfad festgelegt.

Ein kleiner MLP kann als Kapazitaets-/Kostenkontrolle dienen. Der angestrebte Motorpfad
verwendet ein lernendes PC-CVNN; ein reeller Vergleichskopf wird nicht als Erfuellung dieses
Architekturziels ausgegeben. Die komplexe Darstellung allein ist kein Wirksamkeitsbeleg.

# S0 - Aktionsraum und signalreiche Aufgabe

**Festlegung 2026-09-26:** Der Motorzweig verwendet keinen Drucksensor als Lernsignal oder
Laufzeitvoraussetzung. S0/S1 beginnen ausschließlich mit Stellwerten, Encoder-/Propriozeptions-
Folgen und sicheren freien Bewegungen. Kontakt und Greifen bleiben spätere, getrennte Fragen;
eine reale Hardwareübertragung darf nicht von sauberem Fingerdruck abhängen.

- [ ] Fruehere direkte Motorversuche samt Logs suchen und ihre Aktions-/Beobachtungsraeume,
  Lernziele und Abbruchgruende festhalten.
- [ ] Tatsaechlich aktive DOFs, Aktuatorgrenzen, Stellgroessen und Steuerfrequenz erfassen.
  S1/S2 als Gelenkservopfad und S3 als optionale Aktuatorumstellung unterscheiden.
- [ ] Erste Aufgabe: kurze freie Armbewegung bzw. Erreichen eines wahrgenommenen Ziels aus
  verschiedenen Startposen. Vorab definierte unbekannte Last-/Daempfungsbedingungen testen
  Anpassung; die unveraenderte Welt bleibt als Kontrolle erhalten.
- [ ] Messgroessen fixieren: Zielnaehe/Kompetenz, Anpassungsversuche, Stabilitaet,
  Teacher-/IK-Anteil und Aufwand; Freiraumbewegung ist noch kein Greifnachweis.

**Tor S0:** direkter Aktuatorzugriff ist eindeutig, die Aufgabe hat messbaren Lernspielraum,
und der behauptete Gewinn geht ueber das alte Teacher-Deckel-Experiment hinaus.

# S1 - Eigene Uebergaenge und geschlossener Regelkreis

- [ ] Reale Uebergaenge je Steuerungsschritt speichern: Beobachtung, Aktion, Folgezustand,
  Gueltigkeit und Task-Ergebnis. Keine einzelne Sammelaktion pro Episode als Dynamikdatensatz.
- [ ] Optionaler Bootstrap mit bisherigen Stellwerten als Trainingslabels; im Test ohne
  Teacher- oder IK-Ausfuehrung. Getrennt eigene, begrenzte Explorationsbewegungen sammeln.
- [ ] Erster selbstueberwachter Lernentwurf: kurze eigene Aktionen mit ihrer tatsaechlich
  erreichten sensorischen/propriozeptiven Aenderung paaren. Ein gelernter inverser Motorpfad
  erhaelt Ausgangsbeobachtung und gewuenschte Aenderung im Latentraum und lernt das zugehoerige
  Servokommando; ein Vorwaertsmodell sagt die beobachtete Folge vorher. So entstehen Labels
  aus eigenen Bewegungen. Mehrdeutige inverse Zuordnungen und verborgene Dynamik mit kurzer
  Historie untersuchen. Das ist eine Hypothese fuer S1, keine bereits wirksame Lernregel.
- [ ] Zuerst gelernte kurze Bewegungen rueckgekoppelt ausfuehren. Imitationsfehler offline
  gegen tatsaechlichen Fehler im geschlossenen Kreis abgleichen.
- [ ] Fuer modellgestuetzte Aktionsverbesserung zusaetzlich gehaltene Mehrschrittvorhersagen
  und Kalibrierung nachweisen; ansonsten diesen Teil zurueckstellen. Kein Neustart des
  alten Attraktors allein wegen neuer Modulnamen.

**Tor S1:** der Motor steuert die festgelegten Gelenke aus Rueckmeldungen autonom in neuen
Startposen. Eine auswendig gelernte Folge oder reine Offline-Imitation besteht dieses Tor
nicht. Grenzverletzungen/Abbrueche sind Ergebnisse. Gelenk-/Aktuatorgrenzen bleiben technische
Versuchsgrenzen, keine verborgene Aufgabenpolicy; jeder Eingriff wird gezaehlt.

# S2 - Anpassung und ACT23-Integration

**Nutzerergänzung 2026-10-03:** Die Servopositionen von Beginn an als explizite Latent-Information
für ein lernendes Körpermodell erhalten, statt sie später aus einem unbeschrifteten Übergangs-Latent
zurücklernen zu müssen. Der [isolierte Portvertrag](/mechanismen/servo-latent-port.md) ist gebaut:
reversible gemessene Position, Geschwindigkeit, aktionsbedingter gelernter Latent und vorhergesagte
Position getrennt. [Neue S1-Rollouts](/befunde/s1-unabhaengige-rollouts.md) bestehen das
Vorhersagetor; ein lernender Körpermodell-Verbraucher und autonome Steuerung bleiben offen.

**B1 ausgeführt:** Der [erste visuelle Verbraucher](/befunde/s1-visuelles-koerpermodell.md)
lernt direkt aus den Phasen auf Encoder-/Kamerapaaren. Sein Vorhersagetor ist verfehlt
(Test-MSE 1,28× Mittelbild). Positionsinformation bleibt erhalten. Vor weiterem Training
Abdeckung und Generalisierung auditieren; autonome Steuerung bleibt offen.

**Audit abgeschlossen:** [B1-Abdeckung](/befunde/s1-koerpermodell-abdeckung.md): beide Klauen
in 145/224 Posen außerhalb der Kamera; dünne Gelenkraumabdeckung erklärt den Testfehler nicht
allein. Nächster Schritt: geeigneten festen Körperblick am Einrichtungs-/Trainingssatz prüfen,
danach neuer B2-Vertrag mit frischen Testposen. Kein Nachtraining auf B1.

- [ ] Bei unbekannter Last/Daempfung autonom lernend gegen denselben eingefrorenen Motor
  vergleichen, mit identischem Startzustand und ohne neue Teacher-Labels.
- [ ] Danach ein Segment der ACT23-Handlung ersetzen, etwa Anfahrt im freien Raum. Klar
  markieren, welche Segmente weiterhin die bestehende Ausfuehrung steuert.
- [ ] Wrist, Greifer, Kontakt und Schliessen erst in getrennten Erweiterungen aufnehmen.
  Ein Kontaktbegriff aus [Fovea F1](/fragen/dream-rsi-fovea.md) ist eine Hypothese, keine
  Voraussetzung fuer die erste freie Bewegung und kein schon bewiesenes Greifsignal.
- [ ] Regel-/Teacher-Hilfen trainierend abbauen und zur Auswertung abschalten. Reine
  Residualkorrekturen zum alten Controller sind eine moegliche Zwischenstufe, aber noch
  keine autonome direkte Steuerung.

**Tor S2:** eigene Erfahrung verbessert die vereinbarte neue Aufgabe gegen den eingefrorenen
Motor, der gelernte Pfad haelt die vorab definierte Zuverlaessigkeit und seinen Aufwandsrahmen
ein. Einen geringeren Teacher-Score mit belegter Eigenanpassung als architektonischen Gewinn
bewerten, wenn dies im Evaluationsvertrag vorgesehen ist. Kein Nutzen: Zweig abschliessen;
Bestandscontroller bleibt verfuegbar.

# S3 - Nur bei begruendetem Bedarf tiefer an den Aktuator

Geschwindigkeits- oder Drehmomentsteuerung braucht eigene Aktuatoren/Verstaerkungen,
Zeitschritte und Trainingsdaten. Ein `ctrl`-Write in die heutige XML ist noch kein solcher
Versuch. Die Ausgangskontrolle muss in derselben veraenderten Physik mit passendem Regler
laufen. Mehrgewinn kann etwa gelernte Nachgiebigkeit unter Kontakt sein; er ist separat gegen
den Aufwand zu pruefen. Weder Robotersicherheit noch Sim-to-Real-Uebertragung sind durch einen
MuJoCo-Vergleich belegt.

# Anschluss an Dream-RSI

Die Historie kann Budget auf Motor-Trainingslinien und Aufgaben verteilen. Sie kann keine
unbeobachtete Servoaktion vorhersagen. Motorische Imagination benoetigt ein eigenes geprueftes
Dynamikmodell und bleibt eine weitere Hypothese. S0-S2 koennen auch dann wissenschaftlich
sinnvoll sein, wenn D5 keinen Scheduler-Vorteil zeigt.
