## Task: Run the Phase 0 Full Experiment

Execute the full Phase 0 experiment by running `src/run_phase0.py`.

Steps:
1. First, verify all encoder files are importable by running a quick check:
   ```
   cd /project/root && python -c "import sys; sys.path.insert(0,'src'); from encoders import ENCODER_REGISTRY; print('Encoders:', list(ENCODER_REGISTRY.keys()))"
   ```

2. Run the full experiment:
   ```
   cd /project/root && python src/run_phase0.py
   ```
   
   This should run all 5 encoders × 5 seeds = 25 runs and generate:
   - `phase_0/results.csv` 
   - `phase_0/REPORT.md`

3. If any encoder crashes, debug and fix the issue. Common issues:
   - Import errors (path issues)
   - NaN in similarity computation (handle gracefully)
   - Numerical overflow in training

4. After the experiment completes, read and display:
   - `phase_0/results.csv` (the full CSV)
   - `phase_0/REPORT.md` (the generated report)

5. Verify the report correctly evaluates the pre-registration criteria:
   - P0-A is exempt from rho >= 0.6
   - P0-B through P0-E should each show rho values
   - Local methods vs P0-D baseline gap is calculated

IMPORTANT: The working directory for running Python must be the project root (where src/ is a subdirectory). The script uses `sys.path.insert(0, os.path.join(os.path.dirname(__file__)))` which adds `src/` to the path.

If there are any issues with the experiment runner, fix them in `src/run_phase0.py` and re-run.
