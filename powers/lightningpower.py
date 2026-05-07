"""Lightning power: finger bolts, chain lightning, electric aura, screen flash."""

import cv2
import numpy as np
import math
import random
import time
from .basepower import basePower


class lightningPower(basePower):
    name  = "THUNDER STRIKE"
    color = (0, 230, 255)

    def __init__(self, w, h):
        super().__init__(w, h)
        self.cooldown_max = 0.3

    def activate(self, frame: np.ndarray, hands: list, gesture: str, charge: float) -> np.ndarray:
        if not hands:
            return frame

        hand = hands[0]
        pos  = hand.palm_center

        if gesture == "pointing":
            frame = self._finger_lightning(frame, hand)
        elif gesture == "open_palm":
            frame = self._electric_aura(frame, pos)
        elif gesture == "blast" and self.ready:
            frame = self._chain_lightning(frame, pos)
            frame = self._screen_flash(frame)
            self.trigger_cooldown()

        return frame

    def _finger_lightning(self, frame: np.ndarray, hand) -> np.ndarray:
        overlay = frame.copy()
        finger_tips = [8, 12]
        for tip_idx in finger_tips:
            tip = hand.landmarks_px[tip_idx]
            for _ in range(2):
                target = (
                    tip[0] + random.randint(-300, 300),
                    tip[1] - random.randint(50, 300),
                )
                self._bolt(overlay, tip, target, (50, 255, 255), 2)
                self._bolt(overlay, tip, target, (200, 255, 255), 1)
        return cv2.addWeighted(frame, 0.45, overlay, 0.55, 0)

    def _electric_aura(self, frame: np.ndarray, pos: tuple) -> np.ndarray:
        overlay = frame.copy()
        t = time.time()
        for i in range(8):
            angle = math.pi * 2 * i / 8 + t * 2
            r = 40 + math.sin(t * 5 + i) * 15
            x = int(pos[0] + math.cos(angle) * r)
            y = int(pos[1] + math.sin(angle) * r)
            cv2.line(overlay, pos, (x, y), (0, 255, 255), 1, cv2.LINE_AA)
        return cv2.addWeighted(frame, 0.6, overlay, 0.4, 0)

    def _chain_lightning(self, frame: np.ndarray, pos: tuple) -> np.ndarray:
        overlay = frame.copy()
        targets = [(random.randint(0, self.w), random.randint(0, self.h)) for _ in range(4)]
        current = pos
        for target in targets:
            self._bolt(overlay, current, target, (50, 255, 255), 3)
            self._bolt(overlay, current, target, (255, 255, 255), 1)
            current = target
        return cv2.addWeighted(frame, 0.4, overlay, 0.6, 0)

    def _screen_flash(self, frame: np.ndarray) -> np.ndarray:
        flash = np.full_like(frame, (50, 255, 255))
        return cv2.addWeighted(frame, 0.6, flash, 0.4, 0)

    def _bolt(self, frame, start, end, color, width):
        pts = [start]
        steps = 12
        sx, sy = start
        ex, ey = end
        for i in range(1, steps):
            t = i / steps
            mx = int(sx + (ex - sx) * t + random.randint(-30, 30))
            my = int(sy + (ey - sy) * t + random.randint(-30, 30))
            pts.append((mx, my))
        pts.append(end)
        for i in range(len(pts) - 1):
            if (0 <= pts[i][0] < self.w and 0 <= pts[i][1] < self.h and
                    0 <= pts[i+1][0] < self.w and 0 <= pts[i+1][1] < self.h):
                cv2.line(frame, pts[i], pts[i+1], color, width, cv2.LINE_AA)
