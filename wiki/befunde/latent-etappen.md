---
type: Befund
title: Die Latent-Etappen - eine tot, eine schlafend, der Attraktor schaedlich
description: Drei Latent-Etappen waren gebaut und im 314-Episoden-Lauf allesamt INERT. Nach dem Fix: der Latent-Attraktor als Platzierpfad liefert 3/32 gegen 14/32. Ursache belegt, Bedingungen fuer einen zweiten Versuch benannt.
tags: [act23, latent, planung, negativ]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-07-24T00:00:00Z }
verified: { by: human:thomas, at: 2026-07-24T00:00:00Z }
sources:
  - id: chronik
    resource: /chronik/act23.md
    title: act23-Chronik, Branch etappe1-latent-goal-space
---

# Was funktioniert: das Ziel als Latent

**Etappe 4a** ist ein architektonischer Gewinn ohne Kosten: das Platzierziel ist ein
**Ziel-Latent**; `post_goal_fn` kodiert das festgelegte Ziel, `place_servo_fn` treibt das
Trageziel ueber die **Latent-Differenz** zur Hand-Latenz.

    RoPE-Ziel-Latent auf diesem Arbeitsraum gemessen:
      Babble 0,8 mm | Servo 0,0 mm | gegen Decode ohne Rueckkopplung 22,1 mm | ~12 s Start
    USER-VALIDIERT (240 Ep guard-frei): Latent-Platzierung GLEICHAUF mit Koordinaten-Platzierung
    -> der architektonische Gewinn kostet nichts

**Etappe 4b**: der Auto-Lauf **traeumt** seine Ziele - Kandidaten nach Distanz-Neuheit im
Ziel-Latentraum bewertet (dieselbe Mannigfaltigkeit, auf der der 4a-Servo handelt),
Traumgedaechtnis beschraenkt auf 40 und persistiert.

# Was nicht lief: drei inerte Etappen

Ein 314-Episoden-Nachtlauf sollte die drei neuen Latent-Etappen zeigen. **Keine war aktiv** -
die 34 % Lieferung sind das Basissystem.

* **E3 schlafend:** der Attraktor treibt `place_servo_fn` nur `if state.choreo == "attractor"`,
  aber **nichts setzt je "attractor"** - der GUI-Umschalter kippt nur netz <-> fsm, der Auto-Lauf
  erzwingt netz.
* **E2 tot:** der Dynamikblock nutzt die Variable `action`, die in `run_self_learning_steering`
  **nicht existiert** (die Aktion heisst `a_exec`). `NameError` in jeder Episode, verschluckt von
  einem blanken `except Exception: pass`. Die `[Latent-Dynamics]`-Zeile erschien 0x, **kein
  einziger Uebergang wurde je trainiert**.
* **E1 lebt**, aber nur als Verrohrung - kosmetisch, kein Verhaltensbeleg.

# Nach dem Fix: der Attraktor schadet

A/B auf dem fairen gematchten 32-Episoden-Fenster (gleicher Seed, gleiche Basis):

    netz       14/32 = 44%   Median 26 mm
    attractor   3/32 =  9%   Median 98 mm

**Ursache belegt:** die Latent-Dynamik startet pro Lauf **leer** und trainiert erst ab Puffer
>= 10 (MSE = 0 die ersten 10 Episoden); bei Episode 33 erst MSE ~ 0,019 auf 33 Ein-Schritt-
Uebergaengen. `plan_step` minimiert die Energie ueber 32 Kandidaten mit diesem Modell und
schleudert das Objekt an Zufallsziele (126/186/399 mm). Der Basis-Kandidat (= der Servo-Schritt)
**degradiert nicht sauber**, weil die untrainierte Dynamik falschen Kandidaten niedrige Energie
gibt.

# Was ein zweiter Versuch braeuchte

1. Eine **vortrainierte und persistente** Dynamik mit vielen Uebergaengen - **pro Schritt**
   statt einem je Episode.
2. Ein Tor: "Attraktor erst, wenn der MSE unter einer Schwelle liegt, sonst reiner Servo".

Nachtrag zur Persistenz: die Latent-Dynamik startet inzwischen **nicht** mehr leer, `pack()`
speichert den Puffer (Stand der Bestandsaufnahme: 183 Uebergaenge). Der Kern des Negativbefunds
bleibt: ein Uebergang je Episode ist fuer Planung viel zu duenn.

# Fallen

* **Ein blankes `except: pass` verbirgt einen Totalausfall.** Ersetzt durch einen **geloggten**
  Fehler.
* **Die Beschreibung taeuschte, selbst wenn E3 aktiv gewesen waere:** der Attraktor ersetzt
  **nur** das Platzier-Ziel-Servo, **nicht** die FSM und nicht den Griff (die Runtime-Policy
  faehrt weiter). "Abloesung der starren FSM" war ueberzeichnet. Ein Null-Ergebnis der A/B
  bedeutet also "Attraktor-Platzierung ~ alter Latent-Servo", nichts weiter.
* **Dimensionsfalle:** `LatentDynamicsModule(action_dim=4)`, aber `a_exec` ist 6-dimensional
  ([dx, dy, cos2w, sin2w, grip, gentle]) - `grip` und `gentle` fallen bei der Trunkierung weg.
  Und `a_exec` kann `None` sein (Teacher-Episoden).
* **Eine A/B mit ungleichen Armlaengen** (netz 120 Ep vollstaendig, attractor nach 32 gekillt)
  ist nur auf dem **gematchten** Fenster auswertbar.

# Folgen

`LatentAttractor` steht in der [Modullandschaft](/mechanismen/act23-modullandschaft.md) als
"gemessen negativ, nicht nutzen". Der Latent-Servo (netz) bleibt der Platzierpfad. Die
Wegwerfkopien wurden nicht befoerdert.

# Verwandt

* [Modullandschaft](/mechanismen/act23-modullandschaft.md) - dort steht, wo die komplexe Zahl
  und RoPE tatsaechlich tragen
* [Latente Augmentierung](/fragen/latente-augmentierung.md) - dieselbe RoPE-Eigenschaft, anders
  genutzt
