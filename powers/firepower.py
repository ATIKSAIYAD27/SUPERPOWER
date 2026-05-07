"""Fire power: flamethrower, fireball, heat distortion."""

import cv2
import numpy as np
import math
import random
import time
from .basepower import basePower


class firePower(basePower):
    name  = "FIRE STORM"
    color = (0, 80, 255)

    def __init__(self, w, h):
        super().__init__(w, h)
        self.cooldown_max = 0.8
        self._heat_phase  = 0.0

    def activate(self, frame: np.ndarray, hands: list, gesture: str, charge: float) -> np.ndarray:
        if not hands:
            return frame

        self._heat_phase += 0.08
        pos = hands[0].palm_center

        if gesture == "open_palm":
            frame = self._heat_distortion(frame, pos)
        if gesture == "blast" and self.ready:
            frame = self._fireball_shockwave(frame, pos)
            self.trigger_cooldown()

        return frame

    def _heat_distortion(self, frame: np.ndarray, pos: tuple) -> np.ndarray:
        """Ripple/warp effect simulating heat haze."""
        h, w = frame.shape[:2]
        result = frame.copy()
        cx, cy = pos
        radius = 120

        # Displacement map using sinusoidal noise
        for y in range(max(0, cy - radius), min(h, cy + radius)):
            for x in range(max(0, cx - radius), min(w, cx + radius)):
                dist = math.sqrt((x - cx)**2 + (y - cy)**2)
                if dist < radius:
                    strength = (1 - dist / radius) * 6
                    nx = int(x + math.sin(y * 0.1 + self._heat_phase) * strength)
                    ny = int(y + math.cos(x * 0.1 + self._heat_phase) * strength)
                    nx = max(0, min(w - 1, nx))
                    ny = max(0, min(h - 1, ny))
                    result[y, x] = frame[ny, nx]
        return result

    def _fireball_shockwave(self, frame: np.ndarray, pos: tuple) -> np.ndarray:
        overlay = frame.copy()
        t = time.time()
        for r in range(5, 80, 8):
            alpha = max(0, 1 - r / 80)
            cv2.circle(overlay, pos, r, (int(30*alpha), int(100*alpha), int(255*alpha)), 3)
        return cv2.addWeighted(frame, 0.5, overlay, 0.5, 0)
