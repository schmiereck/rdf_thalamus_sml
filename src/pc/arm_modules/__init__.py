"""arm_modules — the pluggable PCModule-style architecture for the MuJoCo arm agent.

Restores the 1D module separation (VisualCortex / BodyModel / Planner / Motor) as
self-contained `ArmModule`s with declared, typed ports, wired together by an `ArmAgent`.
Concrete module wrappers are added alongside `base` as they are implemented.
"""
from .base import Port, ArmModule, ArmAgent
from .visual_cortex import VisualCortexModule
from .body_model import BodyModelModule

__all__ = ["Port", "ArmModule", "ArmAgent", "VisualCortexModule", "BodyModelModule"]
