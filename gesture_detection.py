"""
gesture_detection.py v2.0
High-precision hand tracking and gesture recognition using MediaPipe.
Supports expanded power set, improved swipe detection, and gesture history.
"""

import cv2
import mediapipe as mp
import numpy as np
import time
from dataclasses import dataclass, field
from typing import Optional, List, Tuple
from collections import deque


# ─────────────────────────────────────────────
#  Data Structures
# ─────────────────────────────────────────────

@dataclass
class HandData:
    landmarks: list          # 21 (x,y,z) tuples normalised [0-1]
    landmarks_px: list       # pixel coords
    handedness: str          # "Left" | "Right"
    confidence: float
    wrist: tuple             # (x, y) pixel
    palm_center: tuple       # (x, y) pixel
    fingers_up: list         # [thumb, index, middle, ring, pinky]
    is_open: bool
    is_fist: bool
    is_pointing: bool
    is_pinching: bool
    pinch_distance: float


@dataclass
class GestureState:
    gesture: str = "none"
    power: str = "fire"
    charging: bool = False
    charge_level: float = 0.0
    charge_start: float = 0.0
    swipe_active: bool = False
    swipe_direction: str = ""
    swipe_cooldown: float = 0.0
    both_hands_active: bool = False
    ultimate_ready: bool = False
    combo_count: int = 0
    # tracking history for swipe detection
    wrist_history: deque = field(default_factory=lambda: deque(maxlen=20))


# ─────────────────────────────────────────────
#  Gesture Detector
# ─────────────────────────────────────────────

class GestureDetector:
    POWER_CYCLE = ["fire", "ice", "lightning", "ironman", "telekinesis", "water", "dark"]

    # Finger tip + pip landmark indices
    FINGER_TIPS = [4, 8, 12, 16, 20]
    FINGER_PIPS = [3, 6, 10, 14, 18]

    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.6,
        )
        self.state = GestureState()
        self._last_swipe_time = 0.0
        self._power_switch_cooldown = 0.0
        # per-hand swipe history
        self._hand_histories: dict[str, deque] = {
            "Right": deque(maxlen=15),
            "Left":  deque(maxlen=15),
        }

    # ── Public API ──────────────────────────────

    def process(self, frame: np.ndarray) -> tuple[list[HandData], GestureState]:
        """Run a full pipeline step. Returns hand data list + updated gesture state."""
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        hands: list[HandData] = []
        if results.multi_hand_landmarks:
            for lm, handedness in zip(
                results.multi_hand_landmarks,
                results.multi_handedness,
            ):
                hand = self._parse_hand(lm, handedness, w, h)
                hands.append(hand)

        self._update_state(hands)
        return hands, self.state

    def draw_landmarks(self, frame: np.ndarray, hands: list[HandData]) -> np.ndarray:
        """Draw subtle landmark overlay with futuristic styling."""
        for hand in hands:
            color = {
                "fire":       (30,  80,  255),
                "ice":        (255, 200, 60),
                "lightning":  (0,   220, 255),
                "ironman":    (0,   180, 255),
                "telekinesis":(180, 0,   255),
                "water":      (255, 160, 0),
                "dark":       (180, 0, 255),
            }.get(self.state.power, (0, 255, 120))

            # Draw connections (skeleton)
            mp_drawing = mp.solutions.drawing_utils
            mp_drawing_styles = mp.solutions.drawing_styles
            
            # Custom skeleton drawing
            connections = mp.solutions.hands.HAND_CONNECTIONS
            for connection in connections:
                start_idx = connection[0]
                end_idx = connection[1]
                pt1 = hand.landmarks_px[start_idx]
                pt2 = hand.landmarks_px[end_idx]
                cv2.line(frame, pt1, pt2, color, 1, cv2.LINE_AA)

            # Draw landmarks
            for px, py in hand.landmarks_px:
                cv2.circle(frame, (px, py), 2, (255, 255, 255), -1)
                cv2.circle(frame, (px, py), 4, color, 1, cv2.LINE_AA)
            
            # Draw palm center with a pulsing effect
            pulse = int(5 * np.sin(time.time() * 10)) + 8
            cv2.circle(frame, hand.palm_center, pulse, color, 1, cv2.LINE_AA)
            cv2.circle(frame, hand.palm_center, 3, color, -1)
            
        return frame

    # ── Internal helpers ─────────────────────────

    def _parse_hand(self, lm_result, handedness_result, w, h) -> HandData:
        lms_norm = [(pt.x, pt.y, pt.z) for pt in lm_result.landmark]
        lms_px   = [(int(pt.x * w), int(pt.y * h)) for pt in lm_result.landmark]
        side     = handedness_result.classification[0].label
        conf     = handedness_result.classification[0].score

        wrist       = lms_px[0]
        # Weighted palm center (more stable)
        palm_indices = [0, 1, 5, 9, 13, 17]
        palm_center = (
            int(np.mean([lms_px[i][0] for i in palm_indices])),
            int(np.mean([lms_px[i][1] for i in palm_indices])),
        )

        fingers_up  = self._fingers_extended(lms_norm, side)
        is_open     = sum(fingers_up) >= 4
        is_fist     = sum(fingers_up) == 0
        is_pointing = fingers_up[1] and sum(fingers_up) == 1

        # pinch = thumb tip close to index tip
        thumb_tip = np.array(lms_px[4])
        index_tip = np.array(lms_px[8])
        pinch_dist = float(np.linalg.norm(thumb_tip - index_tip))
        is_pinching = pinch_dist < 40

        return HandData(
            landmarks=lms_norm,
            landmarks_px=lms_px,
            handedness=side,
            confidence=conf,
            wrist=wrist,
            palm_center=palm_center,
            fingers_up=fingers_up,
            is_open=is_open,
            is_fist=is_fist,
            is_pointing=is_pointing,
            is_pinching=is_pinching,
            pinch_distance=pinch_dist,
        )

    def _fingers_extended(self, lms, side: str) -> list:
        """Returns [thumb, index, middle, ring, pinky] booleans."""
        tips = self.FINGER_TIPS
        pips = self.FINGER_PIPS
        extended = []

        # Thumb: compare x-axis (flipped for left hand)
        # Using a more robust thumb detection based on distance from palm
        if side == "Right":
            extended.append(lms[tips[0]][0] < lms[pips[0]][0])
        else:
            extended.append(lms[tips[0]][0] > lms[pips[0]][0])

        # Other fingers: tip y < pip y (tip above pip = extended)
        for i in range(1, 5):
            extended.append(lms[tips[i]][1] < lms[pips[i]][1])

        return extended

    def _update_state(self, hands: list[HandData]):
        now = time.time()
        s = self.state

        if not hands:
            s.gesture = "none"
            s.charging = False
            s.charge_level = 0.0
            s.both_hands_active = False
            return

        # ── Multi-hand logic ──
        right = next((h for h in hands if h.handedness == "Right"), None)
        left  = next((h for h in hands if h.handedness == "Left"),  None)

        s.both_hands_active = len(hands) == 2
        if s.both_hands_active and right and left:
            if right.is_open and left.is_open:
                s.gesture = "ultimate"
                s.ultimate_ready = True
            else:
                s.ultimate_ready = False

        # Single hand gesture detection (primary hand)
        primary = right or left
        if primary and not (s.both_hands_active and s.gesture == "ultimate"):
            self._detect_single_gestures(primary, now)

        # Update swipe histories
        for hand in hands:
            self._hand_histories[hand.handedness].append(hand.wrist)

        # Combo Tracking
        if s.gesture != "none" and s.gesture != "charging":
            if not hasattr(self, '_combo_start_time'):
                self._combo_start_time = now
                self._combo_count = 0
            
            # If same gesture sustained or switching rapidly
            if now - self._combo_start_time > 0.5: # 0.5s of action = +1 combo
                self._combo_count += 1
                self._combo_start_time = now
        else:
            if hasattr(self, '_combo_start_time') and now - self._combo_start_time > 1.5:
                self._combo_count = 0

        # Swipe detection
        self._detect_swipe(now)
        s.combo_count = getattr(self, '_combo_count', 0)

        # Charging mechanic
        if primary and primary.is_fist and not s.swipe_active:
            if not s.charging:
                s.charging = True
                s.charge_start = now
            s.charge_level = min(1.0, (now - s.charge_start) / 2.5)
            s.gesture = "charging"
        else:
            if s.charging and s.charge_level > 0.8:
                s.gesture = "blast"
            s.charging = False
            s.charge_level = max(0.0, s.charge_level - 0.05)

    def _detect_single_gestures(self, hand: HandData, now: float):
        s = self.state
        up = hand.fingers_up # [thumb, index, middle, ring, pinky]
        
        # 1. Power Selection via Signs (God-tier Logic)
        if up == [True, False, False, False, False]: # Thumb only
            s.power = "fire"
        elif up == [False, True, True, False, False]: # Peace / V
            s.power = "ice"
        elif up == [False, True, False, False, True]: # Rock
            s.power = "lightning"
        elif up == [True, True, False, False, True]: # Spider-man / Iron Man
            s.power = "ironman"
        elif up == [False, False, False, False, True]: # Pinky
            s.power = "water"
        elif up == [False, True, True, True, True]: # 4 fingers (No thumb)
            s.power = "dark"
            
        # 2. Action Gestures
        if hand.is_open and not s.charging:
            s.gesture = "open_palm"
        elif hand.is_pointing:
            s.gesture = "pointing"
        elif hand.is_pinching:
            s.gesture = "pinching"
            s.power = "telekinesis" # Auto-select TK on pinch
        elif hand.is_fist:
            if not s.charging:
                s.gesture = "fist"

    def _detect_swipe(self, now: float):
        s = self.state
        COOLDOWN = 0.6 # Faster cooldown for premium feel
        if now - self._last_swipe_time < COOLDOWN:
            s.swipe_active = False
            return

        for side, history in self._hand_histories.items():
            if len(history) < 10:
                continue
            pts = list(history)
            dx = pts[-1][0] - pts[0][0]
            dy = pts[-1][1] - pts[0][1]
            speed = (dx**2 + dy**2) ** 0.5
            
            # Faster movement required for swipe
            if speed < 100:
                continue
                
            if abs(dx) > abs(dy):
                direction = "right" if dx > 0 else "left"
                if abs(dx) > 120:
                    idx = self.POWER_CYCLE.index(s.power)
                    if direction == "right":
                        s.power = self.POWER_CYCLE[(idx + 1) % len(self.POWER_CYCLE)]
                    else:
                        s.power = self.POWER_CYCLE[(idx - 1) % len(self.POWER_CYCLE)]
                    self._last_swipe_time = now
                    s.swipe_active = True
                    s.swipe_direction = direction
                    history.clear()
                    break
