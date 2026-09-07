---
type: Befund
title: Rechnerlast beeinflusst die Lieferquote nicht
description: Der lange gehegte Verdacht, die Lieferquote haenge an der CPU-Auslastung, ist mit zwei natuerlichen Lastfenstern (n=185 gegen 747) und einem Bitgleichheitstest der Physik widerlegt. Last kostet Zeit, nicht Qualitaet.
tags: [act23, messhygiene, physik, negativ]
status: stable
evidenz: gemessen
ebene: langlauf
generated: { by: claude/opus-5, at: 2026-09-07T16:00:00Z }
sources:
  - id: lauf932
    resource: log/pc_act23_2026-09-05_22-06-51_5152.txt
    title: GUI-Langlauf, 932 Episoden, 05.09. 22:10 bis 07.09. 15:06
  - id: det
    resource: "Scratchpad-Sonde: BracketArmSim, 4000 mj_step, sha256 ueber qpos/qvel, leer gegen 12 Brennerprozesse"
    title: Bitgleichheitstest der Physik unter Volllast
---

# Behauptung

Wenn `run_history` im Vollbild mitlaeuft, steigt die **Episodendauer** deutlich - die
**Lieferquote** aber nicht. Die MuJoCo-Physik ist unter Volllast **bitgleich**; Reibung,
Gravitation und Kontaktkraefte aendern sich nicht. Der wiederkehrende Eindruck "unter Last
liefert er besser" ist Blockrauschen.

# Aufbau

Natuerliches Experiment im laufenden GUI-Lauf.[^lauf932] `run_history` wurde vom Nutzer zweimal
gestartet und wieder geschlossen; die Lastfenster sind an einem **Sprung** der Lernzeit
(gleitender Median ueber 5, Schwelle 100 s) objektiv ablesbar, nicht nach Erinnerung gesetzt:

    BEGINN Last  Ep 196  05:50:17      ENDE Last  Ep 279  10:07:37
    BEGINN Last  Ep 796  06:20:09      ENDE Last  Ep 898  13:02:49

Damit 185 belastete gegen 747 freie Episoden, gleicher Zustand, gleiche Mechanik, keine
Codeaenderung dazwischen. Fisher exakt, wie in `CLAUDE.md` verlangt.

Dazu eine direkte Physikprobe[^det]: `BracketArmSim` mit 4000 `mj_step` und deterministischer,
bewegter Sollwertfolge (Kontakte, Reibung, Gravitation alle beteiligt), sha256 ueber
`qpos`/`qvel` alle 100 Schritte - einmal auf leerem Rechner, einmal mit 12 Brennerprozessen auf
12 Kernen.

# Zahlen

    Lieferquote
      belastet   102/185 = 55,1 %   Median-Abstand 22 mm
      frei       385/747 = 51,5 %   Median-Abstand 24 mm
      Fisher exakt p = 0,41
      die beiden Lastfenster einzeln:  Ep 196-278  51/83  = 61,4 %
                                       Ep 796-897  51/102 = 50,0 %

    Kontrolle, Quote je 50 Episoden NUR in den freien Abschnitten:
      48,0 | 54,0 | 48,0 | 64,0 | 50,0 | 66,0 | 60,0 | 52,0
      44,0 | 50,0 | 50,0 | 54,0 | 40,0 | 48,0 | 44,7   [%]

    Physik im Lauf (Median)
      Griffdruck heben     belastet 4,12 N   frei 4,43 N
      Griff hielt nicht    belastet 18,4 %   frei 16,5 %   Fisher p = 0,51
      Regelschritte/Ep     belastet   583     frei   598

    Griffdruck "heben" je Objekt, belastet gegen frei [N]
      obj_L 4,51/4,06   obj_T 4,44/4,12   obj_X 3,79/4,10   obj_blue 4,55/4,94
      obj_green 6,86/5,89   obj_red 6,57/5,62   obj_U 1,05/4,59

    Bitgleichheit unter Volllast
      leer:      sha256 4d6b84b8739c9d0846e3d5abe42c2c6f7fb2cd8af06eae685dc980ae19c95a0f
      12 Kerne:  sha256 4d6b84b8739c9d0846e3d5abe42c2c6f7fb2cd8af06eae685dc980ae19c95a0f
      Summe |qfrc_constraint| auf 12 Stellen identisch, qpos auf 17 Stellen identisch
      (Laufzeit 23,6 s gegen 25,7 s - die Last war messbar da)

# Bewertung

**Das entscheidende Argument sind nicht die 3,6 Punkte, sondern dass die beiden Lastfenster
einander widersprechen** (61,4 % und 50,0 %). Ein Effekt der Last muesste in beiden gleich
gerichtet auftreten. Beide liegen zudem mitten in der freien Streuung von 40 bis 66 %.

Die Hypothese des Nutzers - unter Last aendere sich die Berechnung von Reibung oder
Gravitationskraft, deshalb rutsche das Objekt seltener aus der Klaue - ist **dreifach
widerlegt**:

1. Die Rutschquote bewegt sich nicht (18,4 gegen 16,5 %, p = 0,51).
2. Der Griffdruck verschiebt sich je Objekt in **verschiedene** Richtungen
   (+0,45 / +0,32 / -0,31 / -0,39 / +0,97 / +0,95 N). Eine geaenderte Physik muesste alle
   Koerper gleich gerichtet treffen. Der einzige grosse Ausschlag (obj_U, -3,54 N) ist ein
   **Umkehrschluss**: obj_U liefert unter Last nur 32,4 % statt 44,6 %, und ein fehlgeschlagener
   Griff hebt nichts an - der Druck folgt dem Ausgang, nicht die Physik dem Druck.
3. Der Integrator liefert unter Volllast **bitgleiche** Zustaende.

Dazu die Codeebene: im gesamten Steuerpfad steht **keine** Wanduhr. `pc_act16.py` enthaelt
keinen einzigen Zeitaufruf, `pc_act23.py` genau drei `perf_counter` (Zeilen 3333, 3775, 4297),
alle nur fuer die `[Zeit]`-Zeile. Episoden laufen nach Schritt**zahl**. Es gibt keinen Pfad, ueber
den Auslastung die Physik erreichen koennte. Die frueher rein logisch getroffene Ausschluss-
begruendung des Nutzers war richtig; jetzt steht eine Messung mit echtem Lastkontrast daneben.

**Was das nicht heisst:** Last ist nicht folgenlos. Sie kostet Zeit, und zwar viel - siehe
[Episodendauer](/befunde/episodendauer.md).

# Fallen

* **Der Eindruck ist echt, die Ursache nicht.** Der Nutzer hat den Zusammenhang zweimal
  unabhaengig bemerkt. Das erste Lastfenster liegt tatsaechlich 10 Punkte ueber dem Schnitt - nur
  liegt der Block **davor** noch hoeher. Wer nur den Lastabschnitt und den Gesamtschnitt
  vergleicht, sieht einen Effekt, der bei Aufteilung verschwindet.
* **Mein eigener erster Anlauf war zu klein.** Eine fruehere Auswertung desselben Laufs bei
  279 Episoden fand +8,5 Punkte bei p = 0,17 und stuetzte sich auf **ein** Lastfenster. Erst das
  zweite Fenster entschied - und zeigte in die andere Richtung.

# Folgen fuer die Messhygiene

> **Ein 50-Episoden-Fenster schwankt allein aus Zufall um 26 Punkte** (40,0 bis 66,0 % ueber 15
> freie Bloecke desselben Laufs, gleicher Zustand, gleicher Code). Wer zwei Einstellungen an je
> 50 Episoden vergleicht, misst mit hoher Wahrscheinlichkeit nur das.

Das ist die bislang direkteste Nachweisgrenze fuer act23-A/Bs und gehoert vor jeden Vergleich
dieser Groessenordnung. Sie erklaert rueckblickend mehrere Fehlvorhersagen aus kleinen
Stichproben, siehe [Die Pruefstandsfalle](/mechanismen/pruefstandsfalle.md).

# Verwandt

* [Episodendauer](/befunde/episodendauer.md) - was die Last stattdessen kostet
* [Kopfloses A/B](/messungen/act23-headless-ab.md)
