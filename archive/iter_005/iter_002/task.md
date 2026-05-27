
# Diagnose Phase 3 Training Failure

The Phase 3 spatiotemporal experiments have a critical bug: trained encoders perform WORSE than untrained baselines.

## Results from seed=42:
- P3-A: test_acc=28.25% (chance=25% for 4-class)
- P3-B: test_acc=29.13%
- P3-C: test_acc=34.13%
- Untrained: test_acc=49.5%

The Untrained baseline outperforms all trained variants. This indicates the training loop is corrupting the representations.

## Your Task

1. Read `src/run_phase3.py`, `src/spatiotemporal_encoder.py`, and `src/training_objectives.py`
2. Identify bugs in the backward pass and training loop. Specifically check:
   a. Is the backward pass in spatiotemporal_encoder.py correct? The gradient accumulation and scattering look suspicious.
   b. Is the gradient from average pooling being added correctly?
   c. In the training loop, are the Adam optimizers updating the correct parameters?
   d. Are JEPA code gradients being reshaped correctly between the JEPA loss and the encoder?
   e. Is there a sign error or scaling issue?
   f. For P3-C, are the combined gradients correct?
3. Compare the backward logic with the working Phase 1 (src/run_phase1_v2.py) and Phase 2 (src/run_phase2.py) implementations.
4. Write a detailed diagnostic report identifying ALL bugs found.

## Key Files
- `src/spatiotemporal_encoder.py` — backward() method
- `src/run_phase3.py` — train_jepa_epoch() and run_single_experiment()
- `src/training_objectives.py` — JEPALoss class (working in Phase 1 and 2)
- `src/hierarchical_encoder.py` — working backward_from_code_grads() from Phase 1
- `src/temporal_encoder.py` — working compute_gradients() from Phase 2

Focus on finding concrete bugs — sign errors, wrong shape handling, incorrect gradient flow, missing gradient contributions, or incorrect parameter updates.

DO NOT attempt to fix the code — just identify and document the bugs clearly.
