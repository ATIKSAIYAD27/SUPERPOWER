"""Ice power: freeze beam, frost spread, ice crystal HUD."""

import cv2
import numpy as np
import math
import time
import random
from .basepower import basePower


class icePower(basePower):
    name  = "CRYO FREEZE"
    color = (255, 200, 60)

    def __init__(self, w, h):
        super().__init__(w, h)
        self.cooldown_max = 1.2
        self._frost_level = 0.0
        self._crystal_pts: list = []

    def activate(self, frame: np.ndarray, hands: list, gesture: str, charge: float) -> np.ndarray:
        if not hands:
            self._frost_level = max(0.0, self._frost_level - 0.02)
            return frame

        pos = hands[0].palm_center

        if gesture == "open_palm":
            self._frost_level = min(1.0, self._frost_level + 0.015)
            frame = self._apply_frost(frame)
            frame = self._draw_crystals(frame, pos)

        if gesture == "blast" and self.ready:
            frame = self._freeze_burst(frame, pos)
            self.trigger_cooldown()

        return frame

    def _apply_frost(self, frame: np.ndarray) -> np.ndarray:
        if self._frost_level < 0.05:
            return frame
        h, w = frame.shape[:2]
        # Desaturate slightly and add blue tint
        blue_layer = np.zeros_like(frame)
        blue_layer[:, :, 0] = 180   # B channel
        blue_layer[:, :, 2] = 20    # R channel (reduce)
        frost_frame = cv2.addWeighted(frame, 1.0, blue_layer, self._frost_level * 0.2, 0)

        # Vignette edges as ice
        mask = np.zeros((h, w), dtype=np.float32)
        cv2.circle(mask, (w//2, h//2), int(min(w,h)*0.45), 1.0, -1)
        mask = cv2.GaussianBlur(mask, (81, 81), 0)
        inv_mask = (1 - mask) * self._frost_level * 0.4
        white = np.full_like(frame, (220, 240, 255))
        for c in range(3):
            frost_frame[:, :, c] = np.clip(
                frost_frame[:, :, c] * (1 - inv_mask) + white[:, :, c] * inv_mask, 0, 255
            ).astype(np.uint8)
        return frost_frame

    def _draw_crystals(self, frame: np.ndarray, pos: tuple) -> np.ndarray:
        overlay = frame.copy()
        t = time.time()
        for i in range(6):
            angle = math.pi * 2 * i / 6 + t * 0.5
            length = 30 + math.sin(t * 3 + i) * 10
            x2 = int(pos[0] + math.cos(angle) * length)
            y2 = int(pos[1] + math.sin(angle) * length)
            cv2.line(overlay, pos, (x2, y2), (255, 240, 200), 2)
            # crystal tip
            cv2.circle(overlay, (x2, y2), 4, (255, 255, 255), -1)
        return cv2.addWeighted(frame, 0.6, overlay, 0.4, 0)

    def _freeze_burst(self, frame: np.ndarray, pos: tuple) -> np.ndarray:
        overlay = frame.copy()
        for r in range(10, 150, 15):
            for i in range(8):
                angle = math.pi * 2 * i / 8
                x = int(pos[0] + math.cos(angle) * r)
                y = int(pos[1] + math.sin(angle) * r)
                cv2.line(overlay, pos, (x, y), (255, 230, 150), 2)
        return cv2.addWeighted(frame, 0.5, overlay, 0.5, 0)
