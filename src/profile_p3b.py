import sys, time
sys.path.insert(0, 'src')
import numpy as np
from spatiotemporal_dataset import generate_spatiotemporal_dataset
from spatiotemporal_encoder import SpatiotemporalEncoder
from training_objectives import JEPALoss, _Adam
from run_phase3 import create_jepa_losses, train_jepa_epoch

print('Profiling: P3-B, 30 epochs, 200 train/class, batch=64')
t0 = time.time()
rng = np.random.default_rng(42)
ds = generate_spatiotemporal_dataset(n_train_per_class=200, n_test_per_class=100, noise_flip_prob=0.10, seed=42)
train_grid = ds['train_grid']
print(f'Dataset: {train_grid.shape}')

encoder = SpatiotemporalEncoder(variant='P3-B', d=16, d_out=16, seed=42)
spatial_jepas = create_jepa_losses(encoder.n_spatial_layers, 16, lr=1e-3)
temporal_jepas = create_jepa_losses(encoder.n_temporal_layers, 16, lr=1e-3)

adam_spatial = _Adam({'W_enc': encoder.master_spatial.W_enc, 'b_enc': encoder.master_spatial.b_enc, 'W_dec': encoder.master_spatial.W_dec, 'b_dec': encoder.master_spatial.b_dec}, lr=1e-3)
adam_temporal = _Adam({'W_enc': encoder.master_temporal.W_enc, 'b_enc': encoder.master_temporal.b_enc, 'W_dec': encoder.master_temporal.W_dec, 'b_dec': encoder.master_temporal.b_dec}, lr=1e-3)

for epoch in range(30):
    metrics = train_jepa_epoch(encoder, spatial_jepas, temporal_jepas, train_grid, 64, rng, alpha=0.5, adam_spatial=adam_spatial, adam_temporal=adam_temporal, adam_embedding=None)
    if epoch % 5 == 0 or epoch == 29:
        print(f'  Epoch {epoch}: spatial={metrics["spatial_loss"]:.4f}, temporal={metrics["temporal_loss"]:.4f}')

t1 = time.time()
print(f'Training time: {t1-t0:.1f}s')
