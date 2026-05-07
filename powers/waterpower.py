"""Water power: ripple distortion, water splash, tsunami blast."""

import cv2
import numpy as np
import math
from .basepower import basePower

class waterPower(basePower):
    name  = "HYDRO WAVE"
    color = (255, 160, 0) # BGR for Orange-ish Blue tint or Deep Blue

    def __init__(self, w, h):
        super().__init__(w, h)
        self.cooldown_max = 0.7

    def activate(self, frame: np.ndarray, hands: list, gesture: str, charge: float) -> np.ndarray:
        # The visual effects are primarily handled by EffectsEngine.compose
        # based on the gesture and power name.
        return frame
