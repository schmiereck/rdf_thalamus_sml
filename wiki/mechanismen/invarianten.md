---
type: Mechanismus
title: Invarianten - was man in act23 nicht verletzen darf
description: Die Regeln, die aus je einem konkreten Schaden gelernt wurden: Szenen-Invarianten, Zustand und Persistenz, Etikettenfluss, GUI-Nebenlaeufigkeit, Betriebsarten. Lies das vor jeder Aenderung an pc_act23 oder pc_act16.
tags: [act23, regeln, invarianten]
status: stable
evidenz: gemessen
ebene: code
generated: { by: claude/opus-5, at: 2026-09-07T00:00:00Z }
sources:
  - id: chronik
    resource: /chronik/act23.md
    title: act23-Chronik - jede Regel hier stammt aus einem dort datierten Schaden
---

# Szene und Geometrie

* **`act16.PERSIST=True` ist Pflicht.** Ohne das streut `run_combined` **jede** Episode neu, und
  `set_object_size()` deformiert die ERSTE Geom der zusammengesetzten L/U-Koerper ("ein Segment
  dreht sich um 90 Grad" - vom Nutzer gemeldet). **`set_object_size` auf einem zusammengesetzten
  Koerper deformiert ihn immer.**
* **Jede neue Codebahn, die `set_arm3_targets` ruft, MUSS `joint_4` neu setzen.** Die Funktion
  ueberschreibt es bei jedem Aufruf auf HOME; ohne Neusetzung peitscht das Handgelenk beim ersten
  Hubschritt am Boden nach Hause und schleudert Objekte.
* **Ein zusaetzlicher KOERPER im Modell veraendert das gerenderte Bild - immer.** Gemessen beim
  Einbau des Sockels (2026-09-17): Zustand bitgleich (`qpos` und `qvel` Zeichen fuer Zeichen
  identisch), **Bild aber nicht** - 2 von 57.600 Pixeln, +44 im Rotkanal an der Silhouettenkante
  des roten Wuerfels. Der Sockel stand dabei geparkt weit ausserhalb des Bildes, und der Effekt
  bleibt **unveraendert 2 Pixel**, wenn man ihn voellig durchsichtig, winzig oder in eine
  ausgeblendete Geom-Gruppe setzt: es ist der Szenengraph, nicht sein Aussehen.
  **Folge:** die ganze Wahrnehmung haengt am Bild, also driftet ein Lauf danach auseinander (im
  Warmup ab Schritt ~100, `sensor_err` 40,05 gegen 40,04). **Wer einen Koerper hinzufuegt, kann
  keinen Lauf mehr bitweise mit einem Lauf von davor vergleichen; beide Arme eines A/B muessen
  dieselbe XML fahren.** Verhaltensneutral ist es trotzdem: 4 von 5 Episoden millimetergenau
  gleich, eine 87 gegen 89 mm, Befehle und Ausgaenge identisch.
* **Wer `perceive_all` ruft, muss `mocap_pos` zuruecksetzen.** `perceive_all` parkt die magenta
  Zielscheiben; wer sie nicht wiederherstellt, bekommt ein geparktes Ziel. **Ein Endabstand
  jenseits des Arbeitsraums ist immer eine geparkte Groesse, nie schlechte Ausfuehrung.**
* **Nach JEDER Objektgeometrie-Aenderung greift die Welt-Konsistenzpruefung beim Laden** -
  Geometrieaenderungen entwerten die persistierte Formmannigfaltigkeit still (gemessen: der alte
  U-Klassifikator sah die verbreiterte U in 27 von 30 Faellen als NEUARTIG). Das Laden probiert
  jede trainierte Form an zwei Posen; ein Fehlschlag loest ein **selektives** Nachtrainieren aus.
* **Objekte, die aus dem Arbeitsraum gezogen wurden, bleiben sonst fuer immer draussen** - der
  Arm faehrt dann durch die Szene und stoesst alles um, und die Neugier frisst deren dauerhaft
  hohes sigma. Zwischen den Episoden wird grosszuegig aufgeraeumt (gedruckt, keine Agentenregel).

# Zustand und Persistenz

* **Nie auf der Live-Pkl testen** - `run_one` speichert nach **jeder** Episode. Immer auf einer
  Kopie, oder mit `ACT23_NO_PERSIST=1`.
* **Beim Aendern der Struktur eines Lerners `STATE_SCHEMA` hochzaehlen** (Aktionsdimensionen,
  Merkmalsdimensionen, neue Felder). Beim Laden laufen ausserdem DOF- und Dimensionspruefungen
  plus ein funktionaler Rauchtest je Lerner; bei Nichtpassung wird die Datei auf `.bak` umbenannt
  und mit gedruckter Begruendung neu trainiert.
* **Gepickelte Module haben spaeter deklarierte Ports nicht** (`__init__` laeuft beim Laden
  nicht) - sonst `KeyError` auf dem Live-Zustand.
* **Ein gespeicherter Zustand in einem frischen Prozess verhaelt sich anders als derselbe Zustand
  mitten in einem laufenden Lauf.** Der uebersehene Konfounder aus der Nagelmessung.
* **`state.OBJECTS` haelt ADRESSEN, nicht Koerper.** Derselbe Koerper darf mehrfach darin stehen
  (einmal ueber seinen Namen, einmal ueber ein Eigenschafts-Tripel). Jede daraus abgeleitete
  **Koerper**liste muss entdoppeln - `act16.OBJS`, `SCENE_N` und die Liste in
  `randomize_objects`. Sonst zieht `pc_act16.py:307` mehr Koerper als es gibt und der Start
  bricht mit `ValueError: Cannot take a larger sample than population` ab. Behoben in `3b9e4b2`:
  entdoppeln an zwei Stellen, Eigenschafts-Adressen gar nicht erst persistieren, beim Laden
  herausfiltern (Selbstheilung fuer bereits beschaedigte Staende).
* **Eine Aenderung, die den persistierten Zustand beruehrt, braucht eine Speichern-Neustart-
  Runde.** Der obige Absturz entsteht **erst beim zweiten Start**. Alle meine Sonden liefen mit
  `ACT23_NO_PERSIST=1` auf sauberem Zustand und konnten ihn deshalb prinzipiell nicht finden;
  gemeldet hat ihn der Nutzer.

# Etikettenfluss

* **Ergebnis-Etiketten fliessen nur zu dem Lerner, dessen eigene Entscheidung den Ausgang
  dominiert hat.**
* **Ein Kontrollpunkt isoliert die Aktion nur, wenn die ausfuehrende Choreographie
  vertrauenswuerdig ist.**
* **Aktions-Kandidaten nur dort anbieten, wo ihre Fehlschlaege beobachtbar sind.**
* **Jedes lifelong geloggte Signal an der Quelle mit einer physikalischen Plausibilitaetsschranke
  wachen.** Ein Wahrnehmungsfehler, der in einen Lifelong-Puffer laeuft, vergiftet den Lerner
  dauerhaft; der Fix braucht **beides** - den Bugfix und eine Pufferheilung.
* **Der Teacher korrigiert Fehlschlaege; er darf einen selbst validierten Erfolg nicht
  ueberschreiben.** Eine Episode steuert entweder ihre eigenen sicheren Aktionen oder die
  Teacher-Korrekturen bei, nie beide.
* Naeheres in [Kredit und Selbst-Urteil](/mechanismen/kredit-und-selbsturteil.md).

# GUI und Nebenlaeufigkeit

* **Jede szenenveraendernde GUI-Aktion muss `state.busy` respektieren.** Matplotlib fuehrt
  Knopf-Rueckrufe **innerhalb** des `flush_events` einer laufenden Episode aus; ein mitten im
  Lauf eingefuegtes Objekt liess die Objektliste ueber den Posen-Schnappschuss hinauswachsen
  (`KeyError` beim Wiederherstellen, Szene mutierte unter der Klaue).
* **act23 hat ZWEI Auto-Schleifen** - die kopflose und die der GUI, mit eigenem Code. Ein
  Schalter, der nur in einer steht, sieht in der kopflosen Kontrolle sauber aus und tut in der
  GUI nichts. Zweimal passiert. **Eine Aenderung muss dort geprueft werden, wo sie faehrt.**
* **Kopflos wird gar kein Panel gebaut** (`panel = None`) - jeder Panel-Pfad bleibt dabei
  ungetestet. Fuer GUI-Pruefungen `run_self_learning_steering(headless=False)` mit echtem Panel
  unter `MPLBACKEND=Agg`.
* **Experimente muessen hinter nicht-vorgabemaessigen Schaltern oder in einem eigenen Worktree
  sitzen, bis sie gemessen sind.** Die GUI des Nutzers startet aus **demselben** Arbeitsbaum; ein
  nicht eingecheckter Versuchsstand, der nur durch einen vorgabemaessig eingeschalteten Knopf
  gesichert war, ging in einer 200-Episoden-Sitzung live und liess das lange Objekt einbrechen
  (6/12 -> 1/15).

# Betriebsarten und Auswertung

* **Der Steuerungslauf braucht `ACT23_VIZ=1` und `ACT23_VIZ_HEADLESS=1`** (plus `ACT14_DOF=4`,
  `ACT23_HOME_Z_MIN=0`); ohne die VIZ-Flags landet man in der Diagnose-Betriebsart.
* **`ACT23_CHOREO` ist per Vorgabe `fsm`, nicht `netz`.** Wer den Netzpfad rauchtesten will
  (Selbst-Imitation haengt daran), muss `ACT23_CHOREO=netz` setzen.
* **`ACT23_DEBUG=1` verschiebt den Zufallsstrom** - fuer gepaarte A/Bs also in **beiden** Armen
  setzen.
* **Bei jeder act23-Pufferanalyse `import pc_cvnn.pc_act16` verwenden.** Es gibt zwei Dateien
  dieses Namens mit verschiedenen Vorgaben (`J5_OPEN` 1.08 gegen 0.54); mit den falschen
  Schwellen kippt die Regime-Zuordnung komplett.
* **Ergebnisse nie mit `Select-String` zaehlen** - es ist gross-klein-unempfindlich, und Erfolg
  und Misserfolg haben unterschiedliche Logformate. Immer mit einem Python-Parser, der Episode
  und Ergebnis paart.
* **Bei `relwrist` immer `min(r, 180-r)`.**
* **Der Steuerungslauf gibt kein "Steering beendet" aus** - Warteschleifen darauf laufen ins
  Leere.
* **"killed"-Meldungen von Hintergrundauftraegen sind irrefuehrend**, die Schleife laeuft weiter.
  Vor dem Aufraeumen `Get-CimInstance Win32_Process` pruefen.
* **Lange kopflose Laeufe brauchen einen abgekoppelten Prozess** - Hintergrundaufgaben der
  Werkzeugkette werden nach etwa 45 Minuten beendet. Die Speicherung je Episode macht einen
  Neustart verlustfrei.
* **`SCENE_N=6` kostet ~32 Minuten je 30-Episoden-Lauf**, `SCENE_N=4` nur ~13. Sweeps
  entsprechend planen.

# Verwandt

* [Kopfloses A/B](/messungen/act23-headless-ab.md)
* [Ports und Takte](/mechanismen/ports-und-takte.md) - die Bitgleichheits-Pruefung
* [act23-Chronik](/chronik/act23.md)
