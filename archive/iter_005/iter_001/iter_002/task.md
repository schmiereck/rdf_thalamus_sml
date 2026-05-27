Update `src/spatiotemporal_dataset.py` with the modulo wrapping-based generators for all 4 classes:
- Moving blob (linear trajectory modulo 16)
- Expanding blob (oscillating width modulo 16)
- Periodic spatiotemporal (sinusoidal center oscillation modulo 16)
- Object permanence (stays put modulo 16, disappears for some steps)
Verify that all 4 classes use the same distributions for starting position (uniformly 0 to 15) and base width (2 to 4), and that the self-test passes with ALL shortcut baselines (single-frame and temporal-average) achieving <= 50% test accuracy.