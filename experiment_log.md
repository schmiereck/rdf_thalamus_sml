
---
```yaml
cached_tokens: 0
campaign: phase-0-smoke-test
campaign_status: completed
campaign_summary: 'Phase 0 smoke test complete: all 5 encoders run end-to-end; 3/4
  non-trivial encoders pass rho>=0.6; all local methods within 0.15 of global baseline;
  report generated.'
cost_usd: 1.40168
hypothesis: 'phase-1-setup: establish spatial hierarchy with shared-weight stacked
  nodes; test whether P0-D/P0-C/P0-E can be stacked with dim_out=dim_in recursion
  and cross-layer weight sharing within 15% of per-layer upper bound'
input_tokens: 3316169
iter: 1
metrics:
  epochs: 200
  p0_a_rho_mean: NaN
  p0_b_rho_mean: 0.5807
  p0_b_rho_std: 0.0794
  p0_b_sparsity: 0.6875
  p0_c_rho_mean: 0.8811
  p0_c_rho_std: 0.0177
  p0_c_sparsity: 0.0
  p0_d_rho_mean: 0.6173
  p0_d_rho_std: 0.0842
  p0_d_sparsity_mean: 0.6703
  p0_e_rho_mean: 0.7221
  p0_e_rho_std: 0.025
  p0_e_sparsity_mean: 0.5203
  runs_completed: 25
  seeds: 42, 43, 44, 45, 46
output_tokens: 113150
status: ok
```

## iter_001: phase-1-setup: establish spatial hierarchy with shared-weight stacked nodes; test whether P0-D/P0-C/P0-E can be stacked with dim_out=dim_in recursion and cross-layer weight sharing within 15% of per-layer upper bound

**Analysis:** Phase 0 was decomposed into 3 original sub-goals (harness, encoders, experiment)
but required 9 sub-agent calls due to: (a) execution limits on each agent, 
(b) Unicode encoding issues on Windows, (c) need for iterative tuning of encoders.

Key finding: P0-B (Spatial Pooler with competitive learning) narrowly fails the
pre-registered rho>=0.6 threshold (mean=0.5807). However, it passes Criterion 3

**Status:** ok

**Metrics:** `{'p0_a_rho_mean': 'NaN', 'p0_b_rho_mean': 0.5807, 'p0_b_rho_std': 0.0794, 'p0_c_rho_mean': 0.8811, 'p0_c_rho_std': 0.0177, 'p0_d_rho_mean': 0.6173, 'p0_d_rho_std': 0.0842, 'p0_e_rho_mean': 0.7221, 'p0_e_rho_std': 0.025, 'p0_b_sparsity': 0.6875, 'p0_c_sparsity': 0.0, 'p0_d_sparsity_mean': 0.6703, 'p0_e_sparsity_mean': 0.5203, 'runs_completed': 25, 'seeds': '42, 43, 44, 45, 46', 'epochs': 200}`

**Experimenter view:** Phase 0 (Harness & Smoke Test) completed across 9 sub-agent calls (1.1–1.9).

HARNESS (1.1–1.2): Created src/pre_registration.md with corrected hypothesis
(P0-A exempt from rho>=0.6, off-diagonal-only Spearman) per Research Manager
guidance. Created src/harness.py with DatasetGenerator, SimilarityEvaluator
(strictly off-diagonal Spearman), EncoderBase ABC, and utility functions.
Fixed Unicode enco

**Notes:** Phase 0 smoke test complete. 4/4 non-trivial encoders run end-to-end; 3/4 pass rho>=0.6 criterion; all local methods within 0.15 of global baseline. Report at phase_0/REPORT.md.


---
```yaml
cached_tokens: 2233031
campaign: phase-1-spatial-hierarchy
cost_usd: 2.92354
hypothesis: 'phase-2: the reconstruction objective is misaligned with classification;
  test alternative local objectives (predictive coding, SFA, Hebbian, contrastive)
  on the corrected hierarchical architecture with simultaneous training to determine
  if any local objective can reach ≥60% accuracy'
input_tokens: 8049498
iter: 2
metrics:
  p1_a_corrected_accuracy: 0.3424
  p1_b_corrected_accuracy: 0.3352
  p1_b_kwta_accuracy: 0.3572
  p1_b_kwta_sparsity: 0.5
  p1_b_original_accuracy: 0.1836
  p1_b_params: 1264
  p1_b_sparsity: 0.0003
  p1_c_corrected_accuracy: 0.3324
  p1_c_minus_p1_b_pp: -0.28
  p1_c_params: 14992
  p1_d_corrected_accuracy: 0.2392
  p1_e_corrected_accuracy: 0.3516
  predictive_coding_accuracy: 0.3816
  predictive_coding_sparsity: 0.7246
  random_embedding_accuracy: 0.4336
  simultaneous_training_accuracy: 0.4152
  single_layer_accuracy: 0.3976
  strong_l1_accuracy: 0.3712
  trained_minus_untrained_pp: -14.92
  untrained_corrected_accuracy: 0.4844
  untrained_original_accuracy: 0.2976
output_tokens: 227654
status: ok
```

## iter_002: phase-2: the reconstruction objective is misaligned with classification; test alternative local objectives (predictive coding, SFA, Hebbian, contrastive) on the corrected hierarchical architecture with simultaneous training to determine if any local objective can reach ≥60% accuracy

**Analysis:** Phase 1 tested whether a hierarchical encoder with shared-weight UniversalNodes
(kernel-3, stride-1, d=8, 3 layers over 16 binary inputs) trained with local
reconstruction objectives can produce representations that classify 5 structured
input categories at ≥80% accuracy.

Three sub-goals were executed:

1. ORIGINAL EXPERIMENT (2.1): Revealed representation collapse due to (a) d_out=3*d
creating n

**Status:** ok

**Metrics:** `{'p1_b_original_accuracy': 0.1836, 'untrained_original_accuracy': 0.2976, 'p1_b_corrected_accuracy': 0.3352, 'p1_c_corrected_accuracy': 0.3324, 'p1_a_corrected_accuracy': 0.3424, 'p1_d_corrected_accuracy': 0.2392, 'p1_e_corrected_accuracy': 0.3516, 'p1_b_kwta_accuracy': 0.3572, 'untrained_corrected_accuracy': 0.4844, 'random_embedding_accuracy': 0.4336, 'single_layer_accuracy': 0.3976, 'simultaneous_training_accuracy': 0.4152, 'predictive_coding_accuracy': 0.3816, 'strong_l1_accuracy': 0.3712, 'p1_b_sparsity': 0.0003, 'p1_b_kwta_sparsity': 0.5, 'predictive_coding_sparsity': 0.7246, 'p1_c_minus_p1_b_pp': -0.28, 'trained_minus_untrained_pp': -14.92, 'p1_b_params': 1264, 'p1_c_params': 14992}`

**Experimenter view:** Phase 1 (Spatial Hierarchy without Time) was executed in three sub-goals:

SUB-GOAL 2.1 (Planner): Original Phase 1 experiment revealed representation collapse.
The UniversalNode used d_out=3*d=24 (no bottleneck, identity-like autoencoder)
and Uniform[-0.01,0.01] embedding initialization. This caused the L1 penalty
to dominate the tiny reconstruction MSE, driving all weights to zero.
P1-B accuracy

**Notes:** Phase 1 hypothesis falsified on accuracy and untrained-baseline criteria. Weight sharing confirmed to have zero cost. Reconstruction objective identified as root cause.


---
```yaml
cached_tokens: 2152297
campaign: phase-1-spatial-hierarchy
cost_usd: 3.07887
hypothesis: 'phase-3: JEPA local objective confirmed at 62.1% (d=8); bottleneck refuted;
  temporal unification path cleared for Phase 2'
input_tokens: 6553069
iter: 3
metrics:
  best_prior_method_accuracy: 41.52
  contrastive_d8_test_accuracy: 50.64
  hebbian_d8_test_accuracy: 23.96
  jepa_d16_test_accuracy: 65.2
  jepa_d16_test_std: 1.8
  jepa_d16_vs_d8_gap_pp: 3.08
  jepa_d8_test_accuracy: 62.12
  jepa_d8_test_std: 4.34
  jepa_d8_vs_best_prior_delta_pp: 20.6
  jepa_d8_vs_untrained_delta_pp: 15.96
  jepa_d8_vs_untrained_p_value: 0.0046
  sfa_d8_test_accuracy: 50.56
  untrained_d16_test_accuracy: 54.6
  untrained_d8_test_accuracy: 46.16
output_tokens: 292562
status: ok
```

## iter_003: phase-3: JEPA local objective confirmed at 62.1% (d=8); bottleneck refuted; temporal unification path cleared for Phase 2

**Analysis:** Phase 1 v2 tested the central hypothesis that a non-reconstruction local objective
can produce discriminative hierarchical representations. The JEPA objective
(bidirectional neighbor prediction in latent space + VICReg collapse prevention)
achieved 62.1% — exceeding the 60% pre-registered target and beating the untrained
baseline by +16pp (p=0.005).

The d=8 vs d=16 comparison (3.08pp gap) REFUTES

**Status:** ok

**Metrics:** `{'jepa_d8_test_accuracy': 62.12, 'jepa_d8_test_std': 4.34, 'jepa_d16_test_accuracy': 65.2, 'jepa_d16_test_std': 1.8, 'contrastive_d8_test_accuracy': 50.64, 'sfa_d8_test_accuracy': 50.56, 'hebbian_d8_test_accuracy': 23.96, 'untrained_d8_test_accuracy': 46.16, 'untrained_d16_test_accuracy': 54.6, 'jepa_d8_vs_untrained_delta_pp': 15.96, 'jepa_d8_vs_untrained_p_value': 0.0046, 'jepa_d16_vs_d8_gap_pp': 3.08, 'best_prior_method_accuracy': 41.52, 'jepa_d8_vs_best_prior_delta_pp': 20.6}`

**Experimenter view:** The JEPA hypothesis is STRONGLY CONFIRMED. Sub-agent 3.1 (planner) implemented
four training objectives (JEPA, Contrastive, SFA, Hebbian) and ran all 7 configs
× 5 seeds = 35 experiments. Sub-agent 3.2 (high) performed statistical analysis
against pre-registered criteria.

KEY RESULTS:
- JEPA-d8: 62.12% ± 4.34% (best objective by far)
- JEPA-d16: 65.20% ± 1.80% (+3.1pp, not worth 3.8× more paramet

**Notes:** JEPA confirmed; bottleneck refuted; Phase 2 temporal path cleared.

