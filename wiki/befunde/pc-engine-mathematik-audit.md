---
type: Befund
title: PC-Engine - mathematischer Audit von Inferenz, Lernen und PCNode
description: Unabhängige Gradientenprüfung findet drei Abweichungen in der Zustandsinferenz; einzelne Lernregeln und Ausführungspfade bestehen ihre Kontrollen.
tags: [pc-cvnn, engine, audit, s1]
status: stable
evidenz: gemessen
ebene: pruefstand
sources:
  - resource: ../../src/pc_cvnn/pc_engine_math_audit.py
    title: Isolierter mathematischer Prüfstand
  - resource: ../../log/pc-engine-audit-20261002/with-reference.json
    title: Numerische Ergebnisse und SHA256 der vier Engine-Dateien
  - resource: ../../log/pc-engine-audit-20261002/vector-regression.txt
    title: Acht bestehende Vektorregressionen
---

# Urteil und Geltungsbereich

Die aktuelle Zustandsinferenz erfüllt den unten definierten Energiegradientenvertrag nicht.
Das ist durch unabhängige zentrale Differenzen, eine analytische Referenz und ein exaktes
Gegenbeispiel belegt. Daraus folgt weder, dass jedes bisherige Lernergebnis wertlos ist,
noch dass PC-CVNN oder direkte Servosteuerung ungeeignet wären. Vor einem erneuten
S1-Architektururteil muss die Engine einen expliziten mathematischen Vertrag erhalten.

Geprüft wurden PCNode, PCConnection, PCNetwork und RelaxPlan ohne Simulator, PKL oder
Roboterbewegung. Die Produktionsdateien wurden nicht geändert. Reproduktion:
[Messvorschrift](/messungen/pc-engine-mathematik-audit.md).

# Referenzvertrag

Für Knoten j mit k_j eingehenden Verbindungen gilt wie im Code:

`p_j = (1/k_j) * sum_i W_ij.T @ f(mu_i)`, `epsilon_j = mu_j - p_j`.

Ohne Eingang ist p_j=0. Referenzenergie ist `E = 0.5 * sum_j ||epsilon_j||²`.
Komplexe Zustände werden als Paare reeller Koordinaten differenziert. Alpha, Beta, Gamma
und pressure_scale sind eins; Clipping und Decay sind für Gradiententests ausgeschaltet.
Der Begriff pressure bezeichnet interne Fehlerrückgabe, keinen physischen Drucksensor.

Die negative Zustandsableitung enthält neben `-epsilon_i` für jeden Nachfolger j den Anteil
`J_f(mu_i)^T [conj(W_ij) @ epsilon_j / k_j]`. J_f ist dabei der reelle 2D-Jacobian pro
komplexer Komponente. Die negative W-Ableitung ist
`outer(conj(f(mu_i)), epsilon_j) / k_j`.

Andere Gewichtungen der Energie sind möglich. Beliebige getrennte Rückgabe- und Lernfaktoren
sind aber nicht automatisch der Gradient einer gemeinsamen Energie; das wurde hier nicht bewiesen.

# Gemessene Abweichungen

Je drei Seeds (11, 17, 23), zentrale Differenz h=1e-6, relative Toleranz 1e-6:

| Kontrollfall | Relativer Fehler der Zustandsrichtung | Befund |
|---|---:|---|
| Identität, komplex, ein Eingang | 0,451–0,783 | Rückgabe verwendet W statt conj(W) |
| tanh, reell, ein Eingang | 0,132–0,449 | Aktivierungs-Jacobian fehlt |
| Identität, reell, zwei Eingänge | 0,167–0,266 | Mittelungsfaktor fehlt in Rückgabe |
| tanh, komplex, ein Eingang | 0,390–0,824 | Kombinierte Abweichungen |

Alle zwölf Zustandskontrollen verfehlen den Vertrag. Die unabhängig implementierte analytische
Referenz trifft dieselben numerischen Zustandsgradienten mit maximal 4,55e-10 relativem Fehler.
Damit ist die numerische Prüfung nicht nur ein Vergleich zweier Engine-Ausführungspfade.

Ein exakter linearer Gegenfall mit W=i, freiem Zustand z=0, geklemmtem Ziel 1 und Schrittweite
0,1 erhöht E von **0,50 auf 0,61**. Die falsche Richtung ist also nicht nur eine Skalierungsfrage.

Das W-Lernen besteht alle neun Ein-Eingang-Kontrollen (Fehler höchstens 5,4e-10).
Bei zwei Eingängen ist sein Schritt doppelt so groß wie die Referenzableitung (relativer
Fehler 1); auch dort fehlt 1/k. Die analytische W-Referenz bleibt unter 8,91e-10.
Bei konstanter Eingangsanzahl könnte eine angepasste Lernrate diese Skalierung ausgleichen;
die aktuelle Regel ist dennoch nicht die Ableitung des angegebenen Vertrags.

# PCNode kritisch geprüft

* **Radiales tanh:** f(z)=tanh(|z|) z/|z|. Radiale Ableitung ist sech²(|z|), tangentiale
  Ableitung tanh(|z|)/|z| (Grenzwert 1 bei Null). Eine einzelne komplexe Multiplikation
  bildet diesen Jacobian im Allgemeinen nicht ab. Die gespeicherte activation_deriv kann
  als radiale Ableitung verstanden werden, aber nicht als vollständige Zustandsableitung.
  Als Jacobian-Vektorprodukt benutzt: Fehler 0,756; korrekte 2D-Referenz: 8,13e-11.
  Die aktuelle Zustandsinferenz benutzt activation_deriv ohnehin nicht.
* **modReLU:** Die implementierte unverschobene Betrags-ReLU ist numerisch die Identität
  (Abweichung 2,23e-16). Sie liefert keine zusätzliche Nichtlinearität. Das ist eine
  Eigenschaft dieser Definition, kein Nachweis eines numerischen Defekts.
* **Zeitmodell:** commit_step berechnet `V @ f(mu)`, ohne äußeres f. Dazu passt das isolierte
  V-Lernen (Gradientenfehler 2,28e-10); abweichende Beschreibungen als `f(V @ f(mu))` passen nicht.
* **Temporal deaktivieren:** eta_temporal=0 verhindert Lernen, aber nicht Nutzung des V-Warmstarts
  und nicht das Clipping von V. Ein eingefrorenes Modell ist damit nicht automatisch zeitlos.
* **Reset und Clamp:** Clamp bleibt im geprüften Update unverändert; Reset erhält V und löscht
  Verlauf. SensorNode.reset hebt allerdings Clamp auf. SensorNode erzeugt zudem ein V ohne
  durchgereichten Modell-RNG. Ein anschließend freier Ausgabesensor ist deshalb besonders zu prüfen.
* **Nichtendliche Zustände:** Ein nichtendlicher Update setzt den gesamten Zustandsvektor still
  auf Null. Das kann Ursachen verdecken; ein Diagnosesignal fehlt. Kein Beleg, dass dieser Pfad
  die bisherigen S1-Zahlen verursacht hat.
* **Top-Knoten:** Ohne Eingang gilt pi=0; der eigene Fehler führt daher einen quadratischen
  Nullprior ein. Das muss eine bewusste Modellentscheidung sein, nicht unbeachtete Randbedingung.

# Bestandene Gegenkontrollen

Eine bekannte komplexe lineare Abbildung wird bei geklemmter Quelle in 2.000 Updates gelernt:
Gewichts-MSE 0,4613 → 1,38e-33. Damit ist nicht das gesamte komplexe Lernen defekt.

Der neue kleine Objekt-/Vektorvergleich ist exakt gleich. Zusätzlich bestehen alle acht
vorhandenen Tests in test_relax_vec.py, einschließlich realer Fovea (321 Knoten, 1.883
Verbindungen), gemischter Dimensionen, Clamping, nichtendlicher Werte, externer Änderungen,
Clipping, Pickle-Wiederaufbau und separater Prozesse. Maximale numerische Differenz unter
9e-16. Das bestätigt Implementierungsgleichheit, nicht mathematische Richtigkeit.

# Entscheidung und nächste Arbeitspakete

1. **E0 – Vertrag festlegen:** Mittelung oder Summe, Nullprior, gewichtete Fehlerenergie,
   Zustands-/Parametergradienten und Bedeutung der Rückgabefaktoren explizit spezifizieren.
   Der oben geprüfte ungewichtete Vertrag ist die kleinste kontrollierbare Referenz.
2. **E1 – Isolierte korrekte Variante:** Komplexes Adjungieren, vollständigen Aktivierungs-VJP
   und Eingangsanzahl in Zustands- und W-Regel konsistent implementieren. Zunächst separat
   oder explizit umschaltbar; bestehende Netze nicht still auf andere Dynamik umstellen.
   Tor: alle zwölf Gradientenfälle <1e-6, Gegenbeispiel fällt, lineare Lernkontrolle bleibt bestanden.
3. **E2 – Lebenszyklus klären:** Zeitmodell aus/eingefroren/lernend unterscheiden, Sensor-RNG,
   Reset/Clamp, Lernfreiheit und nichtendliche Werte mit explizitem Vertrag prüfen.
   Training und Evaluation müssen dieselbe definierte Inferenz verwenden.
4. **E3 – Beide Ausführungspfade:** Erst nach E1/E2 den Vektorpfad angleichen und bestehende
   Regressionen erneut bestehen. Alte gespeicherte Modelle brauchen eine bewusste Versionsentscheidung.
5. **E4 – Synthetik, dann S1:** Geklemmte und freie lineare sowie nichtlineare Vorwärtsaufgaben
   mit bekannter Lösung und Konvergenzkontrollen; anschließend S1 nach festem Vertrag erneut
   gegen Persistenz prüfen. Keine Architektur-/Hyperparametersuche auf dem bisherigen Testsatz.

Stand 2026-10-02: E0–E4 offen; der Audit selbst setzt die Reparatur nicht um.

Fortsetzung 2026-10-03: [Isolierte Energie-Inferenz](/messungen/s1-energie-inferenz.md)
erfüllt E0/E1 für den ungewichteten Vertrag. E2 ist für den explizit zeitlosen Modus geprüft;
lernende/eingefrorene Zeitmodelle bleiben ausgenommen. E3 (Produktions-Vektorpfad und Migration)
bleibt offen, da die Referenz bewusst separat ist. Analytische lineare Inferenz und
nichtlineares Decoderlernen bestehen als E4-Gegenkontrollen; der abgeschlossene
[S1-Vergleich](/befunde/s1-energie-inferenz.md) verfehlt trotz bestätigter Testinferenz das Leistungstor.
Globale Engine-Änderungen weiterhin vor Beginn über das Board koordinieren.
