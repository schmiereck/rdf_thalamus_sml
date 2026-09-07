---
type: Referenz
title: act23-Entwicklungslinie
description: Verdichtete Chronik der act23-Linie von Juni 2026 bis September 2026 - Etappen, Commits, Messungen. Der Einstieg in "warum ist das so geworden"; die belastbaren Ergebnisse stehen als eigene Befund-Seiten.
tags: [act23, chronik]
status: stable
evidenz: gemessen
ebene: code
generated: { by: claude/opus-5, at: 2026-09-07T00:00:00Z }
sources:
  - id: memory
    resource: "~/.claude/projects/.../memory/act23-gui-and-fovea-goal.md"
    title: Volltext-Chronik, 1001 Zeilen - die Quelle dieser Verdichtung
---

Dies ist eine **Verdichtung**. Der Volltext mit allen Commit-Hashes, Knopfnamen und
Zwischenmessungen liegt im agenteneigenen Memory-Bestand (`act23-gui-and-fovea-goal.md`,
1001 Zeilen); dort steht auch, was hier weggelassen ist. Die belastbaren Ergebnisse haben eigene
Seiten - hier steht die **Reihenfolge**, in der sie entstanden sind, und was jeweils der Anlass
war.

# Ausgangspunkt (Juni 2026)

`pc_act23.py` mit Steuer-GUI im Stil von act21: eine Knopfreihe je konkretem Objekt, Umschalter
"Greifer: Teacher / Selbst-gelernt", Armkamera, Fovea und Ueberraschungs-Panel. Die Szene bleibt
je Kommando **stabil** (Schnappschuss aller Posen, Wiederherstellung aller nicht kommandierten
Objekte danach), damit sich nur das kommandierte Objekt bewegt.

Lokalisierung anfangs: Wuerfel ueber **Farbe**, L/U ueber **Form**, das lange Objekt
**privilegiert**.

# Die vier Entskriptungs-Stufen

| Stufe | Was | Ergebnis |
|---|---|---|
| **1** | Die von Hand kodierten `body=='obj_U'`-Regeln (Griffweite, sanftes Tragen) werden **Modellentscheidungen**, konditioniert auf den wahrgenommenen Deskriptor. Aktionsvektor 6-dimensional. | U geliefert bei 21 mm mit selbst gewaehlter Griffweite aus vier eigenen Versuchen |
| **2** | Gelernte **Runtime-Policy** (act19-Policy 11 -> 4) statt der FSM; jede Episode labelt ihre besuchten Zustaende mit dem markovschen reaktiven Teacher (**nie** der Phasenmaschine) | Schattenmass 141 -> 29 mm in 6 Episoden; erste Policy-Rollouts 0/5 = erwartete BC-Luecke |
| **3** | **Open-Set-Farben**, vollstaendig selbst etikettiert (`ColourOpenSetModule`); Chromatizitaet, Streuung innerhalb <= 0,075 gegen 0,197 zwischen -> TH = 0,12. Das lange Objekt verliert sein Privileg | kopflos "via Farbklasse farbe-4" -> geliefert bei 11 mm |
| **4a/4b** | Platzierziel als **Ziel-Latent** (RoPE); der Auto-Lauf **traeumt** seine Ziele nach Distanz-Neuheit im Latentraum | Latent-Platzierung gleichauf mit Koordinaten - siehe [Latent-Etappen](/befunde/latent-etappen.md) |

Parallel: **Open-Set-Formen** (kNN-Neuheit auf den |F|-Exemplaren, LOO-kalibriert). Wichtige
Messung dabei: Klassenprototyp und Mahalanobis-Abstand **trennen nicht**, kNN schon. Und es gibt
eine **Dichteanforderung** - bei 250 Trainingsschritten ueberlappen die Mannigfaltigkeiten, mit
den GUI-Vorgaben (2500) nicht. Kleine Rauchtest-Knoepfe koennen deshalb prinzipiell nichts
entdecken.

# Der Dreischritt zur Selbstbeurteilung (Juli)

Nutzerplan: (1) selbst geurteilter Ausgang, (2) Kredit-Routing, (3) Selbst-Imitation. Alles
selbstueberwacht - siehe [Kredit und Selbst-Urteil](/mechanismen/kredit-und-selbsturteil.md).

Der erste lange reale Lauf (~355 Episoden, guard-frei): Netz-Bilanz **verdoppelt** von 6-8/30 auf
16-17/30 (~57 %), Weltmodell +117 Aktualisierungen ueber das Kredit-Routing, Selbst-Urteil ~90 %
Uebereinstimmung.

**Die A/B dazu ist ehrlich ernuechternd:** das **Kredit-Routing** ist der Hebel (Arm ohne
Selbst-Imitation steigt allein von 35 % auf 51 %); die **Selbst-Imitation** zeigt keinen klaren
kausalen Gewinn (+9/200, ganz in der ersten Haelfte, waechst nicht mit dem Puffer). Sie schadet
aber auch nicht - und eine spaetere Probe zeigte, dass sie sehr wohl **tragend** ist, siehe
[Imitationspuffer](/befunde/imitationspuffer.md).

# Die Fovea wird detektorfrei (Juli)

Gelernter Blick, Zoom, Identitaets-Konditionierung, Objektgedaechtnis, Zellen-Winkelablesung -
verdichtet in [Fovea und Blick](/mechanismen/fovea-und-blick.md). Kurzfassung: Blickdrift von
~38 px auf **8,5 px**, die praeziseste detektorfreie Verfolgung, die hier je gemessen wurde. Die
Lieferrate beruehrt es nicht.

Zwei Nutzerbeobachtungen trieben das voran: "die Fovea zeigt oft irgendwohin" (ehrliche Drift,
nach dem `obs`-Fix reine Aufmerksamkeit) und "der Greifer ist beim Greifen schlecht ausgerichtet"
(daraus wurde die Winkelablesung durch die Fovea).

# Die Ausrichtungs-Linie (Juli, Mitte)

Der laengste zusammenhaengende Strang, verdichtet in
[Wrist-Ausrichtung](/befunde/wrist-ausrichtung.md):

    16.07.  Messgeruest [YawAB] auf L/U erweitert. Befund: das Netz hat KEINE Ausrichtungs-Policy
            (R = 0,30 / 0,36 ~ uniform); der Griffpunkt zielt auf die FORM-MITTE, beim U also in
            den offenen Schlitz
    16.07.  Forced-Wrist/Forced-Grasp A/B: der WRIST ist der Hebel fuer L (9/20 -> 14/20), nicht
            der Griffpunkt. Meine Beobachtungs-Lesart war falsch, der kausale Test widerlegt sie
    16.07.  Kombi-Arm schlaegt den reinen Wrist-Arm NICHT. Obergrenze der erzwungenen Paare
            ~55-60% - die Greif-Mechanik duenner Zangenformen bleibt stochastisch
    16.07.  Kapazitaetsprobe: TIEFE ist nicht der Engpass. Roh ~3000 Zeilen noetig, MIT
            Kreuz-Merkmal n ~ 150. Repraesentation schlaegt Tiefe ~20x in Dateneffizienz
    17.07.  DURCHBRUCH Dosislauf D: 600 gepinnte L-Episoden -> Eval 27/40 = 67,5%, erste selbst
            gelernte Ausrichtungs-Policy
    18.07.  Kontrollarm E (Kreuz-Merkmal AUS): 18/40 = 45% = exakt Baseline. ATTRIBUTION SAUBER
    18.07.  Worker-Merge-Geruest fuer parallele Dosislaeufe (~2,8x Durchsatz)
    18.07.  U-Dosislauf: HONEST NEGATIVE - Us Engpass liegt nicht im Aktionsraum
    21.07.  Zwei L-Dosis-Merges in den Live-Zustand (+224, +288 Weltzeilen)
    23.07.  746-Ep-GUI-Lauf: der L-Merge zahlt sich LIVE aus (26 -> 33 -> 57 -> 52% je Viertel,
            kein-Griff 45% -> 30%); der Label-Hunger ist geloest (L 55 statt 14 Etiketten)
    27.07.  Wrist-Gitter objektrelativ: technisch wirksam, WIRKUNGSLOS
    27.07.  Schaerfe-Merkmal |cos2(w-yaw)|: halbiert die Fehlpraeferenz, dreht sie nicht.
            DER EIGENTLICHE BEFUND: das Weltmodell sieht die Fehlgriffe nie

# Die Wahrnehmungs-Splits (Juli, Ende)

Ausgeloest durch drei Nutzerbeobachtungen aus GUI-Laeufen - "roter Wuerfel und L werden
verwechselt", "Neue Form 7 wird nicht gesehen", "das U bleibt beim Ablegen am Greifer haengen".
Alle drei fuehrten auf **dieselbe** Wurzel: verschmolzene Zusammenhangskomponenten. Verdichtet
in [Wahrnehmungs-Splits](/mechanismen/wahrnehmungs-splits.md).

Aus derselben Runde: die **graduelle** Beurteilung (Weltmodell und Selbst-Imitation gewichten
nach Guete statt binaer zu toren) und die
[Ablage-Diagnose](/befunde/ablage-und-platzieren.md).

# Die Aneignungs-Linie (August)

    15.08.  GESPENST-KLASSE: aus DEMSELBEN Kreuz wurden zwei Klassen geboren; die Bindung nahm
            die falsche. Fix: Bestaetigung in 3 von 6 Blicken. Formklassen-Treffer 0/12 -> 8/16
    16.08.  NAMENLOSES FENSTER: die Neugier darf eine noch namenlose Klasse ueben.
            Wiedererkennung 33% -> 83% (ein Seed-Paar)
    17.08.  Sweep ueber 8 Seeds: das namenlose Fenster ist der NORMALFALL (8/8 geboren, 0/8
            sofort gebunden)
    18.08.  ZERSPLITTERUNG GELOEST: Phantomklassen aus verschmolzenen Flecken, -43% ueber 14
            gepaarte Seeds, p = 0,016
    25.08.  Riegel-Messung: Riegel und Reflex sind ein gekoppeltes Paar
    26.08.  Fingerdruck als Ersatz: dreifach negativ
    28.08.  Glaubensfehler widerlegt; Langlauf 1109 Episoden ohne Fortschritt
    29.08.  Nagelneigung: auf act23-Ebene null
    30.08.  Der 1053-Episoden-Zustand wird Vorgabe
    31.08.  obj_Y selbst angeeignet, beide Seeds; farbfreier Split
    02.09.  Uebertragung ueber die Armbreite; eingefrorene Klassen
    03.09.  Formfaktorisierung: die Groesse dominiert die Form
    05.09.  Eigenschafts-Kommando in der GUI bedienbar

# Wo die Linie steht

Die Wahrnehmung ist weitgehend entkrueckt und praezise; die Aneignungs-Maschinerie funktioniert,
**wenn es etwas anzueignen gibt**; die Ausfuehrung ist der stabile Rest. Was **nicht** vorankommt,
ist die Konsolidierung selbst geborener Klassen und die Greif-Zuverlaessigkeit - siehe
[offene Faeden](/fragen/offene-faeden-act23.md).

# Verwandt

* [Invarianten](/mechanismen/invarianten.md) - die Regeln, die aus dieser Chronik destilliert sind
* [Modullandschaft](/mechanismen/act23-modullandschaft.md)
