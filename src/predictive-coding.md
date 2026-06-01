# Predictive Coding

Naming: 
*	Node-Name: <layer><layer-node-number> (b1 = Top, a1 = Mitte, i1 = Sensor)
*	Call-Funktion-Number: <phase>.<n>.<m>.

Phase 1: Vorhersage (Top-Down & Temporal)  \
Phase 2: Fehlerberechnung (Bottom-Up)  \
Phase 3: State-Inference (Die "Relaxation" Schleife)  \
Phase 4: Learning (Weight Update)  

## LOGISCHE LAYER-STRUKTUR MIT VOLLSTÄNDIGEM ZEITLICHEM ABLAUF

```
Node i1 (Sensor Input Layer - Ganz oben):
	hierarchical:
		input:
			i1-input                                                      # Reale Sensordaten / Ground Truth)
			i1-prediction-state                                           # Erwartung von a1, kommt von unten hoch
		internal:
			1.1.   i1-state = i1-input                                    # Realität einziehen
		output:
			2.1.1. i1-out-error = compare(i1-state, i1-prediction-state)  # Sichert nach unten zu a1

Node a1 (Hidden Layer - Mitte):
	hierarchical:
		input:
			a1-prediction-state                                           # Erwartung von b1, kommt von unten hoch)
			i1-out-error                                                  # Fehlersignal von i1, kommt von oben runter
		internal:
			1.2.1. a1-state = a1-prediction-next-state                    # Initialen State aus Vorperiode laden
			3.2.1. a1-state = update_state(a1-out-error, i1-out-error)    # [RELAXATION-SCHLEIFE] Druck von oben & unten
			4.2.1. W_ai = update_weights(W_ai, i1-out-error, a1-state)    # Generative Gewichte anpassen
		output:
			1.2.3. i1-prediction-state = predict_up(W_ai, a1-state)       # Schiebt Vorhersage hoch zu i1
			2.2.1. a1-out-error = compare(a1-state, a1-prediction-state)  # Sichert nach unten zu b1
	temporal:
		input:
		internal:
			4.2.2. a1-prediction-next-state = predict_forward(V_a, a1-state) # Zukunft vorhersagen
			4.2.3. V_a = update_weights(V_a, a1-state)                       # Temporale Gewichte anpassen
		output:
			1.2.4. a1-prediction-next-state = activation_function(V_a, a1_state)  # Puffer für den nächsten Zeitschritt

Node b1 (Deep Abstraction Layer - Ganz unten):
	hierarchical:
		input:
			a1-out-error                                                  # Fehlersignal von a1, kommt von oben runter
		internal:
			1.3.1. b1-state = b1-prediction-next-state                    # Initialen State aus Vorperiode laden
			3.3.1. b1-state = update_state(b1-out-error, a1-out-error)    # [RELAXATION-SCHLEIFE] Reagiert auf a1-Fehler
			4.3.1. W_ba = update_weights(W_ba, a1-out-error, b1-state)    # Generative Gewichte anpassen
		output:
			1.3.3. a1-prediction-state = predict_up(W_ba, b1-state)       # Schiebt Vorhersage hoch zu a1
	temporal:
		input:
		internal:
			4.3.2. b1-prediction-next-state = predict_forward(V_b, b1-state) # Zukunft vorhersagen
			4.3.3. V_b = update_weights(V_b, b1-state)                       # Temporale Gewichte anpassen
		output:
			1.3.4. b1-prediction-next-state = activation_function(V_b, b1_state) # Puffer für den nächsten Zeitschritt
```
