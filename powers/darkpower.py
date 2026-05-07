"""Dark Matter power: gravity pull, void explosion, space distortion."""

import cv2
import numpy as np
from .basepower import basePower

class darkPower(basePower):
    name  = "DARK MATTER"
    color = (180, 0, 255)

    def __init__(self, w, h):
        super().__init__(w, h)
        self.cooldown_max = 1.0

    def activate(self, frame: np.ndarray, hands: list, gesture: str, charge: float) -> np.ndarray:
        # The visual effects are primarily handled by EffectsEngine.compose
        return frame
