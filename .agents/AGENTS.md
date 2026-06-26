# Workspace Rules for rdf_thalamus_sml

## Headless Comparison Runs

When making code modifications, testing adjustments, or running self-tests in this project, you MUST use headless comparison runs to verify impacts and gather metrics.

Refer to the custom skill [run-comparison-runs](file:///C:/Users/thomas/Projekte/rdf_thalamus_sml/.agents/skills/run_comparison_runs/SKILL.md) for full instructions, key environment variables, callback hooks, and python script skeletons.

### Quick Reference

- **Run headless default script**:
  ```powershell
  $env:ACT21_HEADLESS="1"
  .venv/Scripts/python.exe src/pc/pc_act21.py
  ```
- **Filter output with PowerShell**:
  ```powershell
  .venv/Scripts/python.exe src/pc/pc_act21.py 2>&1 | Select-String -Pattern "delivered|recovery-DAgger|SAME FIXED"
  ```
- **Measure custom metrics**:
  Write temporary probe scripts (e.g., `src/pc/_probe.py`) using `macro_log_fn` or `episode_end_fn` hooks inside `run_combined`. Ensure they are cleaned up and not committed to git.
