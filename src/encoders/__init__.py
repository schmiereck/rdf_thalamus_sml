ENCODER_REGISTRY = {}


def register_encoder(encoder_id, encoder_class):
    ENCODER_REGISTRY[encoder_id] = encoder_class


def get_encoder(encoder_id):
    return ENCODER_REGISTRY.get(encoder_id)


# ---------------------------------------------------------------------------
# Register Phase 0 encoders
# ---------------------------------------------------------------------------

from .lookup_table import LookupTableEncoder
from .spatial_pooler import SpatialPoolerEncoder
from .som import SOMEncoder

register_encoder("p0-a", LookupTableEncoder)
register_encoder("p0-b", SpatialPoolerEncoder)
register_encoder("p0-c", SOMEncoder)
