## Task: Generate the Phase 0 Report

Run the report generation script that already exists at `_gen_report.py`:

```bash
cd /project/root && python _gen_report.py
```

If that fails, try running the full experiment runner (which will re-run experiments but also generate the report):

```bash
cd /project/root && python src/run_phase0.py
```

After the report is generated, read and display the contents of `phase_0/REPORT.md`.
