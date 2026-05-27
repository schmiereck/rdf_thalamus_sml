Please modify `src/training_objectives.py` and `src/test_objectives.py` so that `ContrastiveLoss` uses a 2-layer projection head MLP as follows:
- Input size: `10 * d` (e.g. 80 for $d=8$, 160 for $d=16$).
- Hidden size: `5 * d` (e.g. 40 for $d=8$, 80 for $d=16$).
- Output size: `int(2.5 * d)` (e.g. 20 for $d=8$, 40 for $d=16$).
- The MLP layers should be: `W1` of shape `(10 * d, 5 * d)`, `b1` of shape `(5 * d,)`, `W2` of shape `(5 * d, int(2.5 * d))`, and `b2` of shape `(int(2.5 * d),)`.
- Updates `test_contrastive` in `src/test_objectives.py` to pass representations `z1, z2` of shape `(B, 10 * d)` (or `(B, 10 * enc.d_out)` from encoder).
- Run `src/test_objectives.py` to verify all checks pass perfectly.

Use the `write_file` tool to directly modify the files and verify they pass. Thank you!