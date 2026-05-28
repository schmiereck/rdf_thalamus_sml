
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


---
```yaml
cached_tokens: 1772918
campaign: phase-2-temporal-integration
cost_usd: 2.52331
hypothesis: 'phase-4: zero-shot spatial→temporal weight transfer is falsified; P2-D
  with temporal JEPA is competitive (65.3%, only 1.7pp below P2-A); node type is universal
  but weights are axis-specific'
input_tokens: 5232950
iter: 4
metrics:
  cohens_d_f0: -0.7
  cohens_d_f2: 1.95
  f0_loss_ratio: 0.9903
  f1_transfer_gap_pp: -0.8
  f2_p2d_trained_accuracy: 65.33
  f2_p2d_trained_std: 2.74
  f3_gap_vs_best_pp: -1.73
  p2a_trained_accuracy: 67.07
  p2b_trained_accuracy: 62.87
  p2c_trained_accuracy: 61.53
  p2d_trained_jepa_loss: 3.9
  p_value_f2: 0.012
  total_runs: 45
  untrained_test_accuracy: 58.53
  zeroshot_test_accuracy: 57.73
output_tokens: 131112
status: ok
```

## iter_004: phase-4: zero-shot spatial→temporal weight transfer is falsified; P2-D with temporal JEPA is competitive (65.3%, only 1.7pp below P2-A); node type is universal but weights are axis-specific

**Analysis:** Phase 2 tested four pre-registered falsification criteria for the spatial→temporal
transfer of UniversalNode weights. Two criteria are triggered (F0, F1) and two are
not (F2, F3), yielding a partial falsification.

The core finding is nuanced: the node TYPE is universal (kernel-3, 3-slot input,
JEPA objective works on both spatial and temporal data), but the WEIGHTS are
axis-specific. Spatially-tr

**Status:** ok

**Metrics:** `{'f0_loss_ratio': 0.9903, 'f1_transfer_gap_pp': -0.8, 'f2_p2d_trained_accuracy': 65.33, 'f2_p2d_trained_std': 2.74, 'f3_gap_vs_best_pp': -1.73, 'p2d_trained_jepa_loss': 3.9, 'p2a_trained_accuracy': 67.07, 'p2b_trained_accuracy': 62.87, 'p2c_trained_accuracy': 61.53, 'zeroshot_test_accuracy': 57.73, 'untrained_test_accuracy': 58.53, 'total_runs': 45, 'cohens_d_f0': -0.7, 'cohens_d_f2': 1.95, 'p_value_f2': 0.012}`

**Experimenter view:** Phase 2 tested the universal-node hypothesis: can a spatially-trained UniversalNode
transfer zero-shot to temporal data, and is the kernel-3 temporal architecture
competitive with dedicated temporal mechanisms?

SUB-GOAL 4.1 (Planner): Built full temporal infrastructure (temporal_dataset.py,
temporal_encoder.py, run_phase2.py, test_tempal.py). Ran P2-D experiments (15 runs).
Zero-shot transfer is 

**Notes:** Phase 2 complete: zero-shot transfer falsified (F0+F1), but P2-D competitive and JEPA works temporally (F2+F3).


---
```yaml
cached_tokens: 1792704
cost_usd: 1.52794
hypothesis: 'phase-5: unified weights falsified (F1 triggered); deeper problem is
  JEPA-to-classification transfer failure across ALL variants; object_permanence shortcut
  confirmed'
input_tokens: 3667976
iter: 5
metrics:
  experiment_epochs: 30
  experiment_train_per_class: 200
  f1_cohens_d: 0.2206
  f1_p_value: 0.6477
  f2_penalty_pp: 0.0
  f3_gap_pp: 0.5
  f4_p3c_loss_ratio_to_p3b: 1.11
  object_permanence_untrained_acc: 0.692
  p3a_mean_test_acc: 0.445
  p3a_params: 3200
  p3b_mean_test_acc: 0.44
  p3b_params: 3200
  p3c_mean_test_acc: 0.44
  p3c_params: 1600
  p3c_vs_untrained_gain_pp: 1.15
  periodic_st_untrained_acc: 0.106
  untrained_mean_test_acc: 0.4285
output_tokens: 93991
status: ok
```

## iter_005: phase-5: unified weights falsified (F1 triggered); deeper problem is JEPA-to-classification transfer failure across ALL variants; object_permanence shortcut confirmed

**Analysis:** Phase 3 tested whether a single UniversalNode weight set (P3-C) trained jointly
on spatial and temporal JEPA objectives can produce competitive spatiotemporal
representations. The experiment was run with 4 variants × 5 seeds = 20 runs,
using 30 epochs, 200 train/class, 100 test/class, batch=64.

The pre-registered hypothesis is falsified on criterion F1: P3-C achieves only
1.15pp gain over Untrain

**Status:** ok

**Metrics:** `{'p3a_mean_test_acc': 0.445, 'p3b_mean_test_acc': 0.44, 'p3c_mean_test_acc': 0.44, 'untrained_mean_test_acc': 0.4285, 'p3c_vs_untrained_gain_pp': 1.15, 'f1_p_value': 0.6477, 'f1_cohens_d': 0.2206, 'f2_penalty_pp': 0.0, 'f3_gap_pp': 0.5, 'f4_p3c_loss_ratio_to_p3b': 1.11, 'object_permanence_untrained_acc': 0.692, 'periodic_st_untrained_acc': 0.106, 'p3c_params': 1600, 'p3b_params': 3200, 'p3a_params': 3200, 'experiment_epochs': 30, 'experiment_train_per_class': 200}`

**Experimenter view:** 

**Notes:** Phase 3 hypothesis falsified on F1. All variants barely exceed untrained baseline, revealing a deeper JEPA-to-classification transfer problem.


---
```yaml
cached_tokens: 3787683
campaign: phase-3-spatiotemporal-grid
campaign_status: completed
campaign_summary: 'Phase 3 resolved: P3-C with pooled VICReg + spatial_pooled readout
  achieves 61.55% (+9.45pp over untrained, p=0.013, d=1.91). Universal parameter hypothesis
  SUPPORTED.'
cost_usd: 2.72549
hypothesis: 'phase-6: Phase 3 failure resolved — pooled VICReg prevents representation
  collapse (+80.3% std increase) and spatial_pooled readout preserves temporal discriminative
  information (+9.25pp). Combined: P3-C at 61.55% (+9.45pp over untrained, p=0.013,
  d=1.91). Universal parameter hypothesis SUPPORTED.'
input_tokens: 6919963
iter: 6
metrics:
  F1_d_ge_1: true
  F1_gain_ge_8pp: true
  F1_p_lt_005: true
  F2_penalty_le_10pp: true
  F3_within_20pp_P3A: true
  F4_loss_ratio_ok: true
  cohens_d: 1.91
  condition_A_mean: 0.44
  condition_B_mean: 0.535
  condition_C_mean: 0.4915
  condition_D_mean: 0.6155
  condition_D_mean_test_acc: 0.6155
  condition_D_seeds:
  - 0.58
  - 0.6825
  - 0.595
  - 0.57
  - 0.65
  condition_E_mean: 0.414
  condition_F_mean: 0.521
  diagnostic_pooled_std_epoch30: 0.0753
  diagnostic_spatial_l2_std_epoch30: 0.6458
  diagnostic_temporal_l2_std_epoch30: 0.7515
  diagnostic_untrained_pooled_std: 0.0339
  experiment_epochs: 30
  experiment_param_count: 1600
  experiment_seeds: 5
  experiment_train_per_class: 200
  gain_pp: 9.45
  p_value: 0.013
  pooled_std_increase_pct: 80.3
  pooled_std_no_vicreg: 0.0722
  pooled_std_with_vicreg: 0.1302
  pooled_var_loss_no_vicreg: 0.0
  pooled_var_loss_with_vicreg: 0.8698
  untrained_spatial_mean_acc: 0.521
output_tokens: 127551
status: ok
```

## iter_006: phase-6: Phase 3 failure resolved — pooled VICReg prevents representation collapse (+80.3% std increase) and spatial_pooled readout preserves temporal discriminative information (+9.25pp). Combined: P3-C at 61.55% (+9.45pp over untrained, p=0.013, d=1.91). Universal parameter hypothesis SUPPORTED.

**Analysis:** Phase 6 resolved the Phase 3 failure through systematic diagnosis and
targeted fixes, following the approved plan with one critical correction.

SUB-AGENT 6.1 (high): Updated pre-registration. The original hypothesis
("VICReg was omitted from Phase 3 training") was found to be FACTUALLY
INCORRECT — VICReg IS present in JEPALoss with λ_var=25, λ_cov=25. The
pre-registration was updated to reflect t

**Status:** ok

**Metrics:** `{'condition_D_mean_test_acc': 0.6155, 'condition_D_seeds': [0.58, 0.6825, 0.595, 0.57, 0.65], 'untrained_spatial_mean_acc': 0.521, 'gain_pp': 9.45, 'p_value': 0.013, 'cohens_d': 1.91, 'condition_A_mean': 0.44, 'condition_B_mean': 0.535, 'condition_C_mean': 0.4915, 'condition_D_mean': 0.6155, 'condition_E_mean': 0.414, 'condition_F_mean': 0.521, 'pooled_std_no_vicreg': 0.0722, 'pooled_std_with_vicreg': 0.1302, 'pooled_std_increase_pct': 80.3, 'pooled_var_loss_no_vicreg': 0.0, 'pooled_var_loss_with_vicreg': 0.8698, 'diagnostic_pooled_std_epoch30': 0.0753, 'diagnostic_spatial_l2_std_epoch30': 0.6458, 'diagnostic_temporal_l2_std_epoch30': 0.7515, 'diagnostic_untrained_pooled_std': 0.0339, 'F1_gain_ge_8pp': True, 'F1_p_lt_005': True, 'F1_d_ge_1': True, 'F2_penalty_le_10pp': True, 'F3_within_20pp_P3A': True, 'F4_loss_ratio_ok': True, 'experiment_epochs': 30, 'experiment_train_per_class': 200, 'experiment_seeds': 5, 'experiment_param_count': 1600}`

**Experimenter view:** Two root causes were identified for Phase 3's failure and both were fixed:

ROOT CAUSE 1: VICReg on intermediate codes is INEFFECTIVE for the pooled
representation. The gradient per element is ~25/(M*d*std) where M=B*T*S
(28,672 elements for spatial layer 0). This dilutes the VICReg gradient
~20x relative to the JEPA prediction gradient. Per-dim stds at intermediate
layers are ~0.07-0.08, far belo

**Notes:** Phase 3 failure fully resolved. Two root causes (VICReg gradient dilution + pooling destruction) identified and fixed. Universal parameter hypothesis now SUPPORTED.


---
```yaml
cached_tokens: 399104
campaign: phase-4-objective-comparison
campaign_status: completed
campaign_summary: 'Phase 4 resolved: Reconstruction+pooled VICReg achieves 83.00%
  (best); JEPA refuted as best objective (F2 triggered); pooled VICReg is the dominant
  anti-collapse factor for ALL objectives including Reconstruction.'
cost_usd: 2.65005
hypothesis: 'phase-7: Phase 4 training objective comparison completed — Reconstruction+pooled
  VICReg best at 83.00%; JEPA refuted as best (F2 triggered); VICReg is the dominant
  anti-collapse factor across all objectives'
input_tokens: 3532271
iter: 7
metrics:
  best_mean_acc: 0.83
  best_objective: reconstruction+VICReg
  f1_triggered: false
  f2_triggered: true
  f3_triggered: false
  hebbian_no_vicreg_mean_acc: 0.439
  hebbian_vicreg_mean_acc: 0.4855
  jepa_no_vicreg_mean_acc: 0.535
  jepa_vicreg_mean_acc: 0.6155
  recon_no_vicreg_mean_acc: 0.4955
  recon_vicreg_mean_acc: 0.83
  sfa_no_vicreg_mean_acc: 0.25
  sfa_vicreg_mean_acc: 0.8215
  total_runs: 45
  total_runtime_sec: 2641.7
  untrained_mean_acc: 0.521
  vicreg_delta_hebbian_pp: 4.65
  vicreg_delta_jepa_pp: 8.05
  vicreg_delta_recon_pp: 33.45
  vicreg_delta_sfa_pp: 57.15
output_tokens: 57945
status: ok
```

## iter_007: phase-7: Phase 4 training objective comparison completed — Reconstruction+pooled VICReg best at 83.00%; JEPA refuted as best (F2 triggered); VICReg is the dominant anti-collapse factor across all objectives

**Analysis:** Phase 4 tested four training objectives (JEPA, SFA, Hebbian, Reconstruction) with
and without pooled VICReg on the P3-C spatiotemporal benchmark. The pre-registered
hypothesis was that JEPA + pooled VICReg would be the best objective.

H1 (JEPA+VICReg ≥ 55%) is SUPPORTED at 61.55%.
H2 (no other objective exceeds JEPA+VICReg by ≥ 3pp) is REFUTED: SFA+VICReg
(82.15%) and Recon+VICReg (83.00%) exceed

**Status:** ok

**Metrics:** `{'total_runs': 45, 'total_runtime_sec': 2641.7, 'jepa_vicreg_mean_acc': 0.6155, 'jepa_no_vicreg_mean_acc': 0.535, 'sfa_vicreg_mean_acc': 0.8215, 'sfa_no_vicreg_mean_acc': 0.25, 'hebbian_vicreg_mean_acc': 0.4855, 'hebbian_no_vicreg_mean_acc': 0.439, 'recon_vicreg_mean_acc': 0.83, 'recon_no_vicreg_mean_acc': 0.4955, 'untrained_mean_acc': 0.521, 'f1_triggered': False, 'f2_triggered': True, 'f3_triggered': False, 'best_objective': 'reconstruction+VICReg', 'best_mean_acc': 0.83, 'vicreg_delta_sfa_pp': 57.15, 'vicreg_delta_recon_pp': 33.45, 'vicreg_delta_jepa_pp': 8.05, 'vicreg_delta_hebbian_pp': 4.65}`

**Experimenter view:** Phase 4 completed all 45 experiments (4 objectives × 2 VICReg × 5 seeds + 5 untrained).
Memory fixes (sequential execution, batched evaluation, gc.collect) resolved prior crashes.

THREE MAJOR FINDINGS:

1. VICReg is the DOMINANT factor, not the training objective. Pooled VICReg adds
   +57.15pp (SFA), +33.45pp (Recon), +8.05pp (JEPA), +4.65pp (Hebbian). Without
   pooled VICReg, all objectives ex

**Notes:** Phase 4 complete. F2 triggered. Reconstruction+VICReg best at 83%. VICReg is the dominant factor across all objectives.


---
```yaml
cached_tokens: 729016
campaign: phase-5-vector-semantics
campaign_status: completed
campaign_summary: 'Phase 5 resolved: codes show high within-layer consistency (0.974)
  from shared-weight structural prior; training gain only +0.039 (F2 triggered); magnitude
  and gradient are dominant semantic axes; anchor regularization is counterproductive.'
cost_usd: 1.14172
hypothesis: 'phase-8: Vector semantics investigation complete — high within-layer
  consistency (0.974) confirms shared-weight structural prior; modest training gain
  (+0.039) triggers F2; anchoring is counterproductive (F5); magnitude and gradient
  are the two dominant semantic axes.'
input_tokens: 2057681
iter: 8
metrics:
  F1_triggered: false
  F2_triggered: true
  F3_triggered: false
  F4_triggered: false
  F5_triggered: true
  P5-A_cross_layer_consistency: 0.58
  P5-A_mean_test_acc: 0.83
  P5-A_overall_consistency: 0.714
  P5-A_std_test_acc: 0.0227
  P5-A_within_layer_consistency: 0.974
  P5-B_anchored_dim_consistency: 0.7
  P5-B_free_dim_consistency: 0.738
  P5-B_mean_test_acc: 0.82
  P5-C_mean_test_acc: 0.826
  total_experiments: 20
  total_runtime_sec: 1777
  training_gain_overall: 0.039
  untrained_cross_layer_consistency: 0.447
  untrained_mean_test_acc: 0.521
  untrained_overall_consistency: 0.675
  untrained_within_layer_consistency: 0.944
output_tokens: 95823
status: ok
```

## iter_008: phase-8: Vector semantics investigation complete — high within-layer consistency (0.974) confirms shared-weight structural prior; modest training gain (+0.039) triggers F2; anchoring is counterproductive (F5); magnitude and gradient are the two dominant semantic axes.

**Analysis:** Phase 5 investigated whether code dimensions carry consistent, interpretable
semantics across positions and layers. Three sub-agents (8.1, 8.2, 8.3) were
used. 8.1 implemented semantic_probes.py. 8.2 read reference files but ran out
of time. 8.3 implemented run_phase5.py and ran all 20 experiments.

KEY FINDING 1 — STRUCTURAL PRIOR DOMINATES: The shared-weight P3-C architecture
with tanh activatio

**Status:** ok

**Metrics:** `{'P5-A_mean_test_acc': 0.83, 'P5-A_std_test_acc': 0.0227, 'P5-B_mean_test_acc': 0.82, 'P5-C_mean_test_acc': 0.826, 'untrained_mean_test_acc': 0.521, 'P5-A_overall_consistency': 0.714, 'P5-A_within_layer_consistency': 0.974, 'P5-A_cross_layer_consistency': 0.58, 'untrained_overall_consistency': 0.675, 'untrained_within_layer_consistency': 0.944, 'untrained_cross_layer_consistency': 0.447, 'training_gain_overall': 0.039, 'P5-B_anchored_dim_consistency': 0.7, 'P5-B_free_dim_consistency': 0.738, 'F1_triggered': False, 'F2_triggered': True, 'F3_triggered': False, 'F4_triggered': False, 'F5_triggered': True, 'total_experiments': 20, 'total_runtime_sec': 1777}`

**Experimenter view:** Phase 5 completed 20 experiments (3 variants × 5 seeds + 5 untrained).

CLASSIFICATION: P5-A reproduces Phase 4 at 83.0% ± 2.27%. P5-B (81.95%)
and P5-C (82.55%) maintain accuracy within 2pp, confirming anchor and
disentanglement penalties do not destroy discriminative capacity.

WITHIN-LAYER CONSISTENCY is extremely high: P5-A = 0.974, untrained = 0.944.
Shared W_enc produces near-uniform semanti

**Notes:** Phase 5 complete. F2 and F5 triggered. High consistency is largely structural (shared weights + tanh on binary inputs), not training-induced.

