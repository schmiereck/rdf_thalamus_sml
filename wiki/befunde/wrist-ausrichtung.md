---
type: Befund
title: Wrist-Ausrichtung - die eine selbst gelernte Aktions-Policy, und warum sie nicht traegt
description: Schraege Griffe liefern 17% statt 35%. Mit dem Kreuz-Merkmal lernte das Netz die Ausrichtung erstmals selbst (D gegen E, p~0,03). Live bleibt die Wahl Zufall - dem Weltmodell fehlen die Gegenbeispiele.
tags: [act23, wrist, weltmodell, selbstlernen]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-07-27T00:00:00Z }
verified: { by: human:thomas, at: 2026-07-27T00:00:00Z }
sources:
  - id: chronik
    resource: /chronik/act23.md
    title: act23-Chronik, Eintraege 2026-07-16 bis 2026-07-27
---

# Behauptung

Die Griff-Ausrichtung **ist** ein echter Hebel (17 % gegen 35 % Lieferung), das Netz **kann** sie
aus eigener Wahrnehmung lernen (belegt in einem Dosislauf), und es tut es im Normalbetrieb
trotzdem nicht - weil dem Weltmodell genau die schaedlichen Faelle nie als Etikett vorgelegt
werden.

# Zahlen

**Die Ausrichtung wirkt** (610-Episoden-GUI-Lauf, `relwrist` gefaltet auf 0-90 Grad, weil die
Klaue mod 180 symmetrisch ist):

    SCHRAEG (30-60 Grad)   9/53  = 17%
    AUSGERICHTET          51/146 = 35%      Fisher p = 0,015
    L einzeln             21% gegen 49%     p = 0,013
    "nicht gegriffen"     schraeg 57% gegen 42%   p = 0,077

    Formabhaengige Praeferenz, GEGENLAEUFIG:
      U besser SENKRECHT (60-90 Grad: 32% gegen 13% bei 0-30)
      L besser PARALLEL  (0-30 Grad: 56% gegen 36% bei 60-90)

**Erzwungen bringt es den erwarteten Wert** (je 20 Episoden, privilegierte Knoepfe, nie
Laufzeitregel):

    L-Form  Baseline 9/20 -> Wrist erzwungen 14/20 (p einseitig 0,10) -> Griffpunkt erzwungen 8/20
    U-Form  Baseline 9/20 -> Wrist 10/20 -> Griffpunkt 5/20 (schlechter)
    Kombi-Arm (beides): L 11/20, U 11/20 - schlaegt den reinen Wrist-Arm NICHT

**Selbst gelernt - der Durchbruch** (600 gepinnte L-FSM-Episoden + 40 Netz-Auswertung):

    Arm D (Kreuz-Merkmal AN)   Eval 27/40 = 67,5%   aligned-Wahlen 48%   (Baseline 45% / 20%)
    Arm E (Kontrolle, AUS)     Eval 18/40 = 45%     aligned-Wahlen 22%   = Zufallsniveau
    D gegen E einseitig p ~ 0,03

    INTERNE KONTROLLE gegen den Reifungs-Konfounder der 600 Extra-Episoden:
      in D liefern ALIGNED-Wahlen 17/19 = 89%, NICHT-aligned 10/21 = 48% = Baseline-Niveau
      -> der Gewinn kommt spezifisch aus den Episoden, in denen das Netz aligned WAEHLT

Die Kette ist damit vollstaendig: erzwungener Wert (+25 % beim L) -> **Repraesentation**
(Rotation = Phase, das Kreuz-Merkmal `cos2(w-yaw)`, `sin2(w-yaw)`) -> Dosis (0,27 Etiketten je
Episode x 600) -> **selbst gelernt aus eigener Wahrnehmung und eigenem Urteil**, kein
privilegiertes Signal im Lerner.

**Repraesentation schlaegt Tiefe um das ~20-fache in Dateneffizienz:** dieselbe Architektur
braucht auf sauberen synthetischen Daten der wahren L-Regel ~3000 Zeilen; **mit** dem
Kreuz-Merkmal als explizitem Eingang lernt sie bei n ~ 150. Ein tieferes Netz aendert die
Bernoulli-Statistik nicht.

# Warum es live nicht traegt

**1. Das Kandidatengitter war absolut.** `np.linspace(0, pi, 8, endpoint=False)` = acht feste
Winkel im **Weltrahmen**; 100 % der gewaehlten Wrists lagen exakt darauf. Bei beliebigem
Objekt-Yaw ist der relative Winkel damit gar nicht frei waehlbar. Behoben
(`ACT23_WRIST_REL`, Vorgabe AN): das Gitter spannt um die **wahrgenommene Objektachse** auf.
Das ist keine Regel, sondern reine **Repraesentierbarkeit**.

**Die Vorhersage trat nicht ein:** der Schraeg-Anteil fiel nicht (27 % -> 31 %, p = 0,77).

**2. Das Modell hat die Regel nie gelernt.** Am gespeicherten Modell direkt befragt (400 echte
Situationen, nur der Wrist relativ zur Objektachse variiert):

    Guete-Schwankung ueber den GESAMTEN Winkel   0,038 = 6,3% des Mittels
    Schwankung allein durch den GRIP-Modus       0,289 = 7,6x mehr
    Reihenfolge: 90 Grad 0,620 > 45 Grad 0,608 > 67 0,601 > 0 0,585 > 22 0,582
    -> das Modell bevorzugt leicht SCHRAEG, also die in den Daten schlechteste Stellung

Ein Schaerfe-Merkmal `|cos2(w-yaw)|` (`ACT23_WORLD_SHARP`, Vorgabe AN) **halbiert** die
Fehlpraeferenz (+0,082 -> +0,041), **dreht sie aber nicht**.

**3. Der eigentliche Grund - das Weltmodell bekommt die Gegenbeispiele nie zu sehen.** Das
Kredit-Routing labelt nur "sicher geliefert" und "verrutscht"; "nicht gegriffen (Policy)" ist
**Enthaltung**.

    im 610-Ep-Lauf: 220 Fehlgriffe = 36% der Episoden komplett unsichtbar
    nur 29% der Episoden mit relwrist werden gelabelt, davon ~95% Erfolge
    in den 3112 Pufferzeilen ist schraeg deshalb sogar BESSER: 0,813 gegen 0,768

    ALLE Episoden      schraeg 17% gegen 35%   p = 0,015
    nur gelabelte              50% gegen 85%   p = 0,018 (zirkulaer)
    nur Enthaltungen            7% gegen 12%   p = 0,55

Das Modell lernt korrekt aus einem Datensatz, dem genau die schaedlichen Faelle fehlen.

# Fallen

* **Bei `relwrist` immer `min(r, 180-r)` verwenden.** Eine erste Auswertung faltete nicht und
  meldete das L mit **umgekehrter Richtung** als signifikant (p = 0,033) - 170 Grad wurde als
  "quer" statt als "fast parallel" gezaehlt.
* **Vor dem Urteil ueber einen Aktions-Auswahl-Fix das MODELL direkt befragen** (mu ueber die
  variierte Aktionsdimension auf echten gespeicherten Situationen). Das kostet Sekunden und
  haette hier einen 30-Episoden-Rauchtest ersetzt.
* **`Select-String` ist gross-klein-unempfindlich** - `'\] GELIEFERT'` trifft auch
  `[Selbst-Urteil] geliefert`. Ein Zwischenstand war dadurch aufgeblaeht. Ergebnisse **immer**
  mit dem Python-Parser (Episode + Ergebnis gepaart) zaehlen.
* **Label-Hunger-Schleife:** Etiketten je Objekt haengen an der Erfolgsquote, weil "nicht
  gegriffen" Enthaltung ist. Genau die Objekte, die das Lernen am noetigsten haetten, verhungern
  (im 498-Ep-Lauf: gruen 34, lang 42 - aber L nur 14, U 8). Der Teufelskreis dreht erst vorwaerts,
  wenn die Quote steigt: nach den Dosis-Merges hatte L 55 Etiketten.

# Folgen

Umbau bleibt: objektrelatives Gitter und Schaerfe-Merkmal sind **notwendig, aber nicht
hinreichend** - ohne sie nuetzt auch ein Modell nichts, das die Regel kennt.

Der naechste Hebel waere das **Kredit-Design**, und er ist heikel: die Fehlschlagroute existiert,
ist unter der gelernten Choreographie aber abgeschaltet, weil sie dort vergiftet
([Kredit und Selbst-Urteil](/mechanismen/kredit-und-selbsturteil.md)). Denkbare Zwischenwege:
nur bei sauberem Anfahrkriterium labeln, oder das Fehlgriff-Etikett **nur auf die
Ausrichtungsdimension** wirken lassen statt auf die ganze Aktion. Nicht gebaut.

# Verwandt

* [U-Form-Engpass](/befunde/u-form-engpass.md) - dort traegt die Ausrichtung gerade nicht
* [Fovea und Blick](/mechanismen/fovea-und-blick.md) - woher der verlaessliche Yaw kommt
