"""Telekinesis power: pinch to grab, move virtual objects, force push shockwave."""

import cv2
import numpy as np
import math
import random
import time
from typing import Optional
from .basepower import basePower


class telekinesisePower(basePower):
    name  = "TELEKINESIS"
    color = (220, 50, 200)

    def __init__(self, w, h):
        super().__init__(w, h)
        self.cooldown_max = 0.6
        # Virtual objects floating on screen
        self._objects: list[dict] = self._init_objects(w, h)
        self._grabbed: Optional[int] = None

    @staticmethod
    def _init_objects(w, h) -> list:
        shapes = ["circle", "rect", "triangle"]
        cols   = [(0,80,255),(255,80,50),(50,255,180),(200,50,255)]
        objs   = []
        for i in range(5):
            objs.append(dict(
                x=random.randint(100, w-100),
                y=random.randint(100, h-100),
                vx=random.uniform(-1, 1),
                vy=random.uniform(-1, 1),
                size=random.randint(18, 38),
                shape=random.choice(shapes),
                color=random.choice(cols),
                grabbed=False,
            ))
        return objs

    def activate(self, frame: np.ndarray, hands: list, gesture: str, charge: float) -> np.ndarray:
        if not hands:
            self._update_objects(frame)
            frame = self._draw_objects(frame)
            return frame

        hand = hands[0]
        pos  = hand.palm_center

        # Grab nearest object when pinching
        if hand.is_pinching:
            self._try_grab(pos)
        else:
            self._release()

        if self._grabbed is not None:
            obj = self._objects[self._grabbed]
            obj["x"] = pos[0]
            obj["y"] = pos[1]

        if gesture == "blast" and self.ready:
            frame = self._force_push(frame, pos)
            self.trigger_cooldown()

        self._update_objects(frame)
        frame = self._draw_objects(frame)
        frame = self._draw_grab_field(frame, pos, hand.is_pinching)
        return frame

    def _try_grab(self, pos: tuple):
        if self._grabbed is not None:
            return
        best_i, best_d = -1, 80
        for i, obj in enumerate(self._objects):
            d = math.hypot(obj["x"] - pos[0], obj["y"] - pos[1])
            if d < best_d:
                best_d, best_i = d, i
        if best_i >= 0:
            self._grabbed = best_i
            self._objects[best_i]["grabbed"] = True

    def _release(self):
        if self._grabbed is not None:
            self._objects[self._grabbed]["grabbed"] = False
            self._grabbed = None

    def _update_objects(self, frame):
        h, w = frame.shape[:2]
        for obj in self._objects:
            if obj["grabbed"]:
                continue
            obj["x"] += obj["vx"]
            obj["y"] += obj["vy"]
            if obj["x"] < 20 or obj["x"] > w-20:
                obj["vx"] *= -1
            if obj["y"] < 20 or obj["y"] > h-20:
                obj["vy"] *= -1

    def _draw_objects(self, frame: np.ndarray) -> np.ndarray:
        for obj in self._objects:
            x, y, sz = int(obj["x"]), int(obj["y"]), obj["size"]
            col = obj["color"]
            glow_col = tuple(min(255, int(c * 1.5)) for c in col)

            if obj["grabbed"]:
                col = (255, 150, 255)
                # Glow ring when grabbed
                cv2.circle(frame, (x, y), sz + 12, (200, 50, 255), 2)

            if obj["shape"] == "circle":
                cv2.circle(frame, (x, y), sz, col, -1)
                cv2.circle(frame, (x, y), sz, glow_col, 2)
            elif obj["shape"] == "rect":
                cv2.rectangle(frame, (x-sz, y-sz), (x+sz, y+sz), col, -1)
                cv2.rectangle(frame, (x-sz, y-sz), (x+sz, y+sz), glow_col, 2)
            elif obj["shape"] == "triangle":
                pts = np.array([
                    [x, y - sz], [x - sz, y + sz], [x + sz, y + sz]
                ], dtype=np.int32)
                cv2.fillPoly(frame, [pts], col)
                cv2.polylines(frame, [pts], True, glow_col, 2)
        return frame

    def _draw_grab_field(self, frame: np.ndarray, pos: tuple, pinching: bool) -> np.ndarray:
        if not pinching:
            return frame
        overlay = frame.copy()
        t = time.time()
        r = int(60 + math.sin(t * 6) * 10)
        cv2.circle(overlay, pos, r, (200, 50, 255), 2)
        cv2.circle(overlay, pos, r // 2, (255, 150, 255), 1)
        return cv2.addWeighted(frame, 0.65, overlay, 0.35, 0)

    def _force_push(self, frame: np.ndarray, pos: tuple) -> np.ndarray:
        # Launch all objects away with a professional easing
        for obj in self._objects:
            dx = obj["x"] - pos[0]
            dy = obj["y"] - pos[1]
            d = math.hypot(dx, dy)
            if d < 300: # Range of psychic wave
                force = (1 - d/300) * 15
                obj["vx"] += (dx / (d+1)) * force
                obj["vy"] += (dy / (d+1)) * force
        return frame


