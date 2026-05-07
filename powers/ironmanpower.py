"""Iron Man power: repulsor beam, arc reactor glow, target lock, HUD readouts."""

import cv2
import numpy as np
import math
import time
from .basepower import basePower


class ironManPower(basePower):
    name  = "IRON MAN"
    color = (0, 220, 80)

    def __init__(self, w, h):
        super().__init__(w, h)
        self.cooldown_max = 0.5
        self._lock_targets: list = []

    def activate(self, frame: np.ndarray, hands: list, gesture: str, charge: float) -> np.ndarray:
        if not hands:
            return frame

        hand = hands[0]
        pos  = hand.palm_center

        if gesture == "open_palm":
            frame = self._arc_reactor(frame, pos)
            if charge > 0.3:
                frame = self._repulsor_beam(frame, pos, charge)

        if gesture == "pointing":
            frame = self._target_lock(frame, hand)

        if gesture == "blast" and self.ready:
            frame = self._full_blast(frame, pos)
            self.trigger_cooldown()

        return frame

    def _arc_reactor(self, frame: np.ndarray, pos: tuple) -> np.ndarray:
        overlay = frame.copy()
        t = time.time()
        col = (0, 220, 80)
        # Outer rings
        for i in range(4):
            r = 15 + i * 10
            alpha = 1.0 - i * 0.2
            c = tuple(int(ch * alpha) for ch in col)
            cv2.circle(overlay, pos, r, c, 2 if i > 0 else -1, cv2.LINE_AA)
        # Rotating inner element
        for i in range(6):
            angle = math.pi * 2 * i / 6 + t * 3
            x = int(pos[0] + math.cos(angle) * 12)
            y = int(pos[1] + math.sin(angle) * 12)
            cv2.circle(overlay, (x, y), 3, (0, 255, 120), -1, cv2.LINE_AA)
        return cv2.addWeighted(frame, 0.55, overlay, 0.45, 0)

    def _repulsor_beam(self, frame: np.ndarray, pos: tuple, charge: float) -> np.ndarray:
        overlay = frame.copy()
        col = (0, 255, 80)
        # Beam upward from palm
        beam_end = (pos[0], max(0, pos[1] - int(200 + charge * 200)))
        for bw, alpha in [(24, 0.1), (14, 0.25), (8, 0.5), (4, 0.8), (2, 1.0)]:
            c = tuple(int(ch * alpha) for ch in col)
            cv2.line(overlay, pos, beam_end, c, bw, cv2.LINE_AA)
        # Impact glow at end
        cv2.circle(overlay, beam_end, int(15 + charge * 10), (100, 255, 180), -1, cv2.LINE_AA)
        return cv2.addWeighted(frame, 0.5, overlay, 0.5, 0)

    def _target_lock(self, frame: np.ndarray, hand) -> np.ndarray:
        overlay = frame.copy()
        col = (0, 220, 80)
        tip = hand.landmarks_px[8]
        size = 35
        cv2.rectangle(overlay, (tip[0]-size, tip[1]-size), (tip[0]+size, tip[1]+size), col, 1, cv2.LINE_AA)
        # Corner accents
        for dx, dy in [(-1,-1),(1,-1),(-1,1),(1,1)]:
            cv2.line(overlay, (tip[0]+dx*size, tip[1]+dy*size),
                     (tip[0]+dx*(size-10), tip[1]+dy*size), col, 2, cv2.LINE_AA)
            cv2.line(overlay, (tip[0]+dx*size, tip[1]+dy*size),
                     (tip[0]+dx*size, tip[1]+dy*(size-10)), col, 2, cv2.LINE_AA)
        cv2.putText(overlay, "LOCK", (tip[0]-size, tip[1]-size-6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, col, 1, cv2.LINE_AA)
        return cv2.addWeighted(frame, 0.6, overlay, 0.4, 0)

    def _full_blast(self, frame: np.ndarray, pos: tuple) -> np.ndarray:
        overlay = frame.copy()
        col = (0, 255, 80)
        for r in range(10, 200, 20):
            alpha = max(0, 1 - r / 200)
            c = tuple(int(ch * alpha) for ch in col)
            cv2.circle(overlay, pos, r, c, 3, cv2.LINE_AA)
        return cv2.addWeighted(frame, 0.4, overlay, 0.6, 0)
