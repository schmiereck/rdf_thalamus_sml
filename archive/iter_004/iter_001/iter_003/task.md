Please update `src/pre_registration.md` to ensure the Falsification Criterion section matches the user specifications exactly.

Specifically:
- Locate the F0 entry under `## 2. Falsification Criterion` in `src/pre_registration.md`.
- Replace it (or add it as the very first criterion) with:
`F0 (Zero-Shot Transfer JEPA Loss): If Loss_spatial_trained / Loss_untrained >= 0.85 on temporal JEPA loss, the spatial -> temporal transfer has FAILED. This is the most rigorous test of whether spatially-trained weights encode general local-pattern structure vs. axis-specific structure.`
- Ensure F1, F2, F3 are preserved in order after F0.

Verify the file's content after writing to make sure it is correct and formatted beautifully.