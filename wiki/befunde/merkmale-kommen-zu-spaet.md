---
type: Befund
title: Ein spaet eingefuehrtes Merkmal erreicht das Weltmodell nie
description: Der Nachbar-Merkmalsblock ist auf 6,0 Prozent der 11563 Pufferzeilen ueberhaupt gefuellt - der Rest traegt den neutralen "nie gemessen"-Wert. Zusammen mit der gemessenen Traegheit des Fits heisst das: wer ein Merkmal nachtraeglich einbaut, gibt ihm keine Chance. Der Engpass ist die Zusammensetzung des Puffers, nicht der Merkmalssatz.
tags: [act23, weltmodell, merkmale, puffer]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-08T18:00:00Z }
sources:
  - id: zustand
    resource: "Kopie von src/pc_cvnn/state/act23_state.pkl, 11563 Weltzeilen, feat_dim 38, NH=8"
    title: Auszaehlung des Nachbar-Blocks im Live-Puffer
  - id: warm
    resource: /befunde/welt-fit-warmstart.md
    title: Die Traegheitsmessung des Fits
---

# Behauptung

Der Nachbar-Merkmalsblock (`_neighbour_feats`, `pc_act23.py:1972`) ist korrekt gebaut,
verdrahtet und kostenlos - aber er ist auf **6,0 %** der Pufferzeilen ueberhaupt gefuellt. Die
uebrigen 94 % tragen den neutralen Wert mit `gueltig = 0`, weil sie aelter sind als das Merkmal.

Zusammen mit der gemessenen Traegheit des Fits[^warm] folgt daraus die eigentliche Aussage:
**der Engpass des Weltmodells ist nicht, welche Merkmale es hat, sondern womit sein Puffer
gefuellt ist.** Ein nachtraeglich eingefuehrtes Merkmal kann sich gegen den Altbestand nicht
durchsetzen.

# Zahlen

    Puffer: 11563 Zeilen, Merkmalsbreite 38 (6 + NH 8 + Nachbar 5 + Fovea + Koerper)

    Nachbar-Block (Spalten 14..18)
      gueltig                       690 / 11563 = 6,0 %
      d_nah   Median 80 mm, 10./90. Perzentil 57 / 115 mm, am Deckel (>=120 mm) 7 %
      n_nah   Mittel 1,84   Verteilung [51, 228, 234, 135, 38] fuer 0..4 Nachbarn

    Signal auf den 690 gueltigen Zeilen (Ausgang = abgestuftes Erfolgslabel)
      Nachbar  < 60 mm   Ausgang 0,320  (n =  95)
      Nachbar >= 60 mm   Ausgang 0,287  (n = 595)
      Spearman(d_nah, Ausgang) = -0,072  (p = 0,059)
      Spearman(n_nah, Ausgang) = +0,134  (p = 0,0004)

# Bewertung

**Zur Menge.** 690 informative Zeilen gegen 10873 neutrale. Die Traegheitsmessung aus
[Welt-Fit: Warmstart](/befunde/welt-fit-warmstart.md) zeigt, wie wenig das bewegt: 30 Zeilen mit
umgedrehtem Etikett verschoben die Vorhersage darauf in 8 Episoden nur von 0,576 auf 0,531 - bei
Sollwert 0. Ein Merkmal, das auf 6 % der Zeilen steht, hat gegen diese Masse keine Hebelwirkung.
Das ist eine **Folgerung** aus zwei Messungen, nicht selbst gemessen - und sie ist billig
pruefbar (nur auf den 690 gueltigen Zeilen fitten, oder sie hochgewichten).

**Zur Richtung - und sie ist unerwartet.** Naeher stehende und *mehr* Nachbarn gehen mit einem
**besseren** Ausgang einher, nicht mit einem schlechteren. Das widerspricht der Intuition hinter
dem Merkmal (die Klaue rammt Nachbarn, Blobs verschmelzen). Wahrscheinlichste Erklaerung:
Konfundierung - Gedraenge tritt in der Tischmitte auf, wo der Arm ohnehin besser arbeitet. Der
Zusammenhang ist damit **kein** Beleg, dass Nachbarschaft nicht schadet; er ist ein Beleg, dass
dieses Merkmal ohne Kontrolle fuer die Lage nicht interpretierbar ist.

**Was das fuer die offene Frage heisst.** [Exekutionsvarianz](/befunde/exekutionsvarianz.md)
haelt fest: zwischen Grundrate 54 % und Obergrenze 82 % liegen ~27 Punkte lernbares Signal, vier
Rezepte sind null, und *"was fehlt, ist ein Merkmal, nicht ein Verfahren"*. Dort steht
ausserdem, der Merkmalsblock sei **nicht pruefbar** gewesen (Gueltig-Flag zu 0 %). Er ist es
immer noch fast nicht - nach ueber 4800 weiteren Episoden erst zu 6 %. Die Frage ist also nicht
beantwortet worden, sondern **nie gestellt worden koennen**.

# Folgen - was daraus zu tun waere

Drei Wege, keiner gebaut, in aufsteigendem Aufwand:

1. **Auf den gueltigen Zeilen messen.** Fit nur auf den 690, oder Hochgewichtung, und die
   Vorhersageguete gegen den heutigen Fit stellen. Kostet keinen Lauf und beantwortet zum ersten
   Mal, ob der Nachbar-Block ueberhaupt traegt.
2. **Alte Zeilen nachruesten, wo es ehrlich geht.** Fuer Zeilen mit gespeicherter Szene liesse
   sich der Block nachtraeglich berechnen. Wo die Szene fehlt, bleibt `gueltig = 0` - **ein
   erfundener Sachwert waere eine Luege im Trainingssatz**, wie der Docstring selbst festhaelt.
3. **Die allgemeine Lehre einbauen.** Wenn ein neues Merkmal grundsaetzlich zu spaet kommt,
   braucht der Puffer ein Verfahren fuer Merkmalswechsel - etwa einen zweiten, jungen Puffer,
   auf dem neue Merkmale ohne Altbestand bewertet werden.

# Fallen

* **`ensure_feat_dim` ist nicht schuld, sondern ehrlich.** Es fuellt Altzeilen mit einem
  neutralen Wert und einem Gueltig-Flag statt zu raten. Genau richtig - der Preis ist, dass das
  Merkmal dadurch verduennt wird, und dieser Preis war bisher unbeziffert.
* **6 % ist nicht "fast fertig".** Der Anteil waechst nur mit neuen Episoden, und der Puffer
  waechst mit. Bei ~0,2 neuen Zeilen je Episode dauert es Tausende Episoden bis zu einem Anteil,
  der etwas bewegen koennte.

# Verwandt

* [Exekutionsvarianz](/befunde/exekutionsvarianz.md) - "was fehlt, ist ein Merkmal, nicht ein Verfahren"
* [Welt-Fit: Warmstart](/befunde/welt-fit-warmstart.md) - die Traegheit, die das Merkmal erdrueckt
* [Latente Augmentierung](/fragen/latente-augmentierung.md) - der andere Weg, mehr aus einer Episode zu holen
* [Offene Faeden](/fragen/offene-faeden-act23.md)
