Update `src/pre_registration.md` with:
1. Under "1. Hypothesis": Clearly state the NEW Untrained baseline criterion (trained P1-B must beat untrained baseline by >= 15 percentage points) and the Sparsity criterion (P1-B code sparsity >= 50%).
2. Under "2. Falsification Criterion": Clearly add:
   - Untrained baseline criterion: The hypothesis is falsified if trained P1-B does not beat the untrained baseline by >= 15pp.
   - Sparsity criterion: The hypothesis is falsified if average code sparsity of P1-B codes is < 50%.
3. Under "3. Proposed Method" (or a new section): Clearly document the training mechanics choice: Progressive Training was chosen over Simultaneous Training because simultaneous training with gradient averaging causes representation drift (where layer l+1 reconstructs a moving target from layer l). Progressive training is architecturally cleaner and keeps intermediate layer representations stable while weights are shared and frozen.

Ensure that the rest of the pre-registration content is preserved, and the file is saved.