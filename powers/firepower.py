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
        cx, cy = pos
        radius = 120

        # Define region of interest (ROI) to apply remap
        y1, y2 = max(0, cy - radius), min(h, cy + radius)
        x1, x2 = max(0, cx - radius), min(w, cx + radius)
        if y1 >= y2 or x1 >= x2: return frame
        
        region = frame[y1:y2, x1:x2].copy()
        rh, rw = region.shape[:2]
        
        # Fast numpy meshgrid instead of python loops
        xs = np.arange(rw, dtype=np.float32)
        ys = np.arange(rh, dtype=np.float32)
        xg, yg = np.meshgrid(xs, ys)
        
        dx = xg - (cx - x1)
        dy = yg - (cy - y1)
        dist = np.sqrt(dx**2 + dy**2) + 1e-6
        
        # Apply heat distortion math
        mask = (dist < radius).astype(np.float32)
        strength = (1 - dist / radius) * 6 * mask
        
        map_x = (xg + np.sin(yg * 0.1 + self._heat_phase) * strength).astype(np.float32)
        map_y = (yg + np.cos(xg * 0.1 + self._heat_phase) * strength).astype(np.float32)
        
        warped = cv2.remap(region, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        
        # Blend the warped region smoothly into the frame
        frame[y1:y2, x1:x2] = warped
        return frame

    def _fireball_shockwave(self, frame: np.ndarray, pos: tuple) -> np.ndarray:
        overlay = frame.copy()
        t = time.time()
        for r in range(5, 80, 8):
            alpha = max(0, 1 - r / 80)
            cv2.circle(overlay, pos, r, (int(30*alpha), int(100*alpha), int(255*alpha)), 3, cv2.LINE_AA)
        return cv2.addWeighted(frame, 0.5, overlay, 0.5, 0)
