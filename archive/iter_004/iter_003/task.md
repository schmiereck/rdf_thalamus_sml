## Phase 2 Statistical Analysis, Falsification Testing, and Report

Create the final Phase 2 report with statistical analysis and falsification testing. Read the pre-registered hypothesis and criteria from `src/pre_registration.md` first.

### Data Files
- `phase_2/p2d_results.csv` — P2-D results (3 configs × 5 seeds = 15 runs)
- `phase_2/baseline_results.csv` — P2-A/B/C results (6 configs × 5 seeds = 30 runs)

### Task 1: Statistical Analysis

Compute the following across all 9 configurations (3 P2-D + 6 P2-A/B/C), all metrics:
- Mean and std for each config across 5 seeds
- Paired t-tests where relevant (especially ZeroShot vs Untrained for F0/F1)
- Effect sizes (Cohen's d)

### Task 2: Falsification Criteria Testing

Test ALL four pre-registered criteria:

**F0 (Zero-Shot Transfer JEPA Loss):** Loss_spatial_trained / Loss_untrained ≥ 0.85 → FALSIFIED
- Compute: mean(ZeroShot JEPA loss) / mean(Untrained JEPA loss)
- Report the ratio and verdict

**F1 (Transfer failure):** Spatially-trained classification accuracy ≤ 5pp above untrained → FALSIFIED
- Compute: mean(P2-D-ZeroShot accuracy) - mean(P2-D-Untrained accuracy)  
- Report the difference and verdict

**F2 (Temporal JEPA failure):** P2-D trained classification < 60% → FALSIFIED
- Compute: mean(P2-D-Trained accuracy)
- Report and verdict

**F3 (P2-D non-competitiveness):** P2-D trained ≥ 20pp worse than best alternative → FALSIFIED
- Compute: mean(P2-D-Trained accuracy) - max(mean(P2-A/B/C-Trained accuracy))
- Report and verdict

### Task 3: Additional Analysis

Analyze these important secondary findings:

1. **JEPA Loss by encoder type (trained):** P2-D achieves the lowest JEPA loss (3.9) despite not having the highest classification accuracy. P2-B achieves 5.8 JEPA loss but only 62.9% accuracy. Interpret: P2-D's kernel-3 sliding window may create more locally predictable codes, while P2-B's recurrent state creates codes that are harder for a simple linear predictor to predict but may carry richer temporal information.

2. **Classification vs Prediction tradeoff:** Trained encoders have HIGHER classification accuracy but LOWER next-step cosine similarity (on classification task) than untrained encoders. This is because trained encoders learn category-separating features that are NOT raw next-step predictive. Discuss this.

3. **Why zero-shot transfer fails:** The spatial JEPA objective learns to predict adjacent SPATIAL positions. This creates weights that capture spatial adjacency patterns (e.g., "what does a blob look like from the left/middle/right?"). Temporal transitions have completely different statistics (e.g., "what state follows A?"). The UniversalNode's W_enc is a (3d, d) matrix that maps 3-slot input patterns to codes — spatial patterns and temporal patterns occupy different regions of the (3d)-dimensional input space, so spatially-optimized W_enc doesn't help with temporal inputs.

4. **The Periodicity Loophole confirmed:** Both ZeroShot (57.7%) and Untrained (58.5%) achieve ~58% classification accuracy, well above chance (33.3%), purely from deterministic propagation preserving periodicity. This validates the Research Manager's concern.

### Task 4: Write `phase_2/REPORT.md`

Write a comprehensive report with:
1. Executive Summary (2-3 paragraphs)
2. Experimental Design table
3. Full Results Table (all configs, all metrics, mean ± std)
4. Falsification Criteria Assessment (each criterion with computation and verdict)
5. Analysis of secondary findings
6. Implications for the universal-node hypothesis
7. Recommendations for Phase 3

### Key Findings to Emphasize

1. **Zero-shot spatial→temporal transfer is FALSIFIED** (F0: ratio=0.99, F1: -0.8pp gap)
2. **Temporal JEPA training WORKS** (F2: 65.3% ≥ 60%)  
3. **P2-D is COMPETITIVE** with dedicated temporal mechanisms (F3: only 1.7pp below P2-A)
4. **P2-D achieves the lowest JEPA loss** among all trained encoders (3.9 vs 5.8 for P2-B)
5. **The universal node CAN learn temporal structure** — it just needs to be trained on temporal data, not transferred from spatial training

### Implications

The universal-node hypothesis is PARTIALLY SUPPORTED:
- ✅ The same architectural form (kernel-3, 3-slot input) works for both spatial and temporal processing
- ✅ The same JEPA objective works for both spatial and temporal training
- ✅ P2-D is competitive with dedicated temporal mechanisms
- ❌ Zero-shot weight transfer across axes does NOT work
- The implication: one node TYPE, but NOT one set of weights. Future work should explore fine-tuning (starting from spatial weights) or joint spatio-temporal training.

Write the report to `phase_2/REPORT.md`. Do NOT overwrite the existing p2d_results.csv or baseline_results.csv.
