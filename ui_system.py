"""
ui_system.py v4.0 — AAA JARVIS COMMAND CENTER
Next-gen holographic interface: Oscillating widgets, digital noise, XP system, and smooth transitions.
"""

import cv2
import numpy as np
import time
import math
from collections import deque

class UISystem:
    def __init__(self, width, height):
        self.w = width
        self.h = height
        self._start_time = time.time()
        self._fps_history = deque(maxlen=30)
        self._gesture_history = deque(maxlen=8)
        self._last_gesture = "NONE"
        self._voice_text = "NEXUS OS v4.0 ONLINE. NEURAL LINK SYNCED."
        self._voice_time = time.time()
        
        # AAA Game States
        self.xp = 0
        self.level = 1
        self.stamina = 1.0
        self._show_help = False
        self._boot_anim = 0.0 # 0.0 to 1.0
        
        # Digital Noise Pre-calc
        self.vignette = self._create_vignette()

    def _create_vignette(self):
        h, w = self.h, self.w
        mask = np.zeros((h, w), dtype=np.float32)
        cv2.circle(mask, (w//2, h//2), int(max(w,h)*0.85), 1.0, -1)
        mask = cv2.GaussianBlur(mask, (121, 121), 0)
        return np.stack((mask,)*3, axis=-1)

    def draw(self, frame, power, gesture, charge, both_hands, hands, fps, 
             particle_count=0, render_ms=0.0):
        
        now = time.time()
        t = now - self._start_time
        col = self._get_col(power)
        
        # 0. Cinematic Base
        frame = (frame * self.vignette).astype(np.uint8)
        if random.random() > 0.98: # Digital Glitch
            frame = self._apply_glitch(frame)

        # 1. AAA Top Dashboard (Holographic Oscillating Widget)
        self._draw_holographic_top(frame, t, col, fps, render_ms)
        
        # 2. XP & Stamina Progression
        self._draw_progression(frame, col, charge)
        
        # 3. Floating Power Wheel (Right Side)
        self._draw_power_wheel(frame, t, power, col)
        
        # 4. Gesture History (Holographic Scrolling)
        self._draw_gesture_log(frame, col)

        # 5. Advanced AR Targeting
        if hands:
            for hand in hands:
                self._draw_expert_targeting(frame, hand, col, t)
                if gesture and gesture != "none":
                    self.xp += 1 # Progress
                    if self.xp > 500: self.xp = 0; self.level += 1
        else:
            self._draw_scanning_overlay(frame, t, col)

        # 6. AI Voice Command
        self._draw_voice_feedback(frame, t)

        if self._show_help: self._draw_aaa_manual(frame)
        
        return frame

    def _draw_holographic_top(self, frame, t, col, fps, ms):
        # Top-left status
        y_off = int(math.sin(t*2)*5)
        self._glass_box(frame, 20, 20+y_off, 240, 100+y_off, col)
        cv2.putText(frame, "NEXUS COMMAND", (35, 50+y_off), cv2.FONT_HERSHEY_DUPLEX, 0.5, col, 1, cv2.LINE_AA)
        cv2.putText(frame, f"OS v4.0 | Lvl {self.level}", (35, 75+y_off), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200,200,200), 1, cv2.LINE_AA)
        
        # Top-right telemetry
        self._glass_box(frame, self.w-180, 20, self.w-20, 80, (40,40,40))
        cv2.putText(frame, f"FPS: {int(fps)}", (self.w-165, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.4, col, 1, cv2.LINE_AA)
        cv2.putText(frame, f"LATENCY: {ms:.1f}ms", (self.w-165, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (150,150,150), 1, cv2.LINE_AA)

    def _draw_progression(self, frame, col, charge):
        # Bottom XP Bar
        bx, by, bw, bh = self.w//2-300, self.h-40, 600, 8
        cv2.rectangle(frame, (bx, by), (bx+bw, by+bh), (20,20,20), -1)
        xp_w = int(bw * (self.xp/500))
        cv2.rectangle(frame, (bx, by), (bx+xp_w, by+bh), (0,255,255), -1)
        cv2.putText(frame, f"XP PROGRESS", (bx, by-10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (150,150,150), 1, cv2.LINE_AA)
        
        # Stamina / Charge
        self._glass_box(frame, self.w//2-100, self.h-100, self.w//2+100, self.h-60, col)
        fill = int(180 * charge)
        cv2.rectangle(frame, (self.w//2-90, self.h-85), (self.w//2-90+fill, self.h-75), col, -1)
        cv2.putText(frame, "ENERGY SYNC", (self.w//2-40, self.h-105), cv2.FONT_HERSHEY_SIMPLEX, 0.35, col, 1, cv2.LINE_AA)

    def _draw_power_wheel(self, frame, t, active_power, col):
        cx, cy = self.w-80, self.h//2
        powers = ["fire", "ice", "lightning", "ironman", "telekinesis", "water", "dark"]
        for i, p in enumerate(powers):
            angle = t + i * (6.28/len(powers))
            px = int(cx + math.cos(angle)*60)
            py = int(cy + math.sin(angle)*60)
            p_col = self._get_col(p)
            if p == active_power:
                cv2.circle(frame, (px, py), 12, p_col, -1, cv2.LINE_AA)
                cv2.circle(frame, (px, py), 18, p_col, 1, cv2.LINE_AA)
            else:
                cv2.circle(frame, (px, py), 6, p_col, 1, cv2.LINE_AA)

    def _draw_gesture_log(self, frame, col):
        x, y0 = self.w-220, self.h-250
        self._glass_box(frame, x-10, y0-30, self.w-20, self.h-120, (30,30,30))
        cv2.putText(frame, "PROTOCOL LOG", (x, y0-10), cv2.FONT_HERSHEY_DUPLEX, 0.4, col, 1, cv2.LINE_AA)
        for i, (g, ts) in enumerate(list(self._gesture_history)[:6]):
            alpha = max(0, 1.0 - (time.time()-ts)/4.0)
            c = tuple(int(ch*alpha) for ch in (255,255,255))
            cv2.putText(frame, f"> {g}", (x, y0+25+i*25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, c, 1, cv2.LINE_AA)

    def _draw_expert_targeting(self, frame, hand, col, t):
        px, py = hand.palm_center
        # Professional Brackets
        s = 50 + int(math.sin(t*10)*5)
        for dx, dy in [(-1,-1), (1,-1), (-1,1), (1,1)]:
            cx, cy = px + dx*s, py + dy*s
            cv2.line(frame, (cx, cy), (cx-dx*20, cy), col, 2, cv2.LINE_AA)
            cv2.line(frame, (cx, cy), (cx, cy-dy*20), col, 2, cv2.LINE_AA)
        # Digital Skeleton
        for start, end in [(0,5), (5,9), (9,13), (13,17), (0,17)]:
            pt1, pt2 = hand.landmarks_px[start], hand.landmarks_px[end]
            cv2.line(frame, pt1, pt2, col, 1, cv2.LINE_AA)
        cv2.putText(frame, f"LOCKED: {int(hand.confidence*100)}%", (px+s+10, py), cv2.FONT_HERSHEY_SIMPLEX, 0.35, col, 1, cv2.LINE_AA)

    def _draw_scanning_overlay(self, frame, t, col):
        sy = int(self.h//2 + math.sin(t*3)*(self.h//2-100))
        cv2.line(frame, (100, sy), (self.w-100, sy), col, 1, cv2.LINE_AA)
        cv2.putText(frame, "SEARCHING FOR BIOMETRIC LINK...", (self.w//2-120, sy-15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, col, 1, cv2.LINE_AA)

    def _draw_voice_feedback(self, frame, t):
        if time.time() - self._voice_time < 3.0:
            sz = cv2.getTextSize(self._voice_text, cv2.FONT_HERSHEY_DUPLEX, 0.6, 1)[0]
            # Outer glow
            cv2.putText(frame, self._voice_text, (self.w//2 - sz[0]//2, self.h-140), cv2.FONT_HERSHEY_DUPLEX, 0.6, (0, 100, 100), 3, cv2.LINE_AA)
            cv2.putText(frame, self._voice_text, (self.w//2 - sz[0]//2, self.h-140), cv2.FONT_HERSHEY_DUPLEX, 0.6, (0, 255, 255), 1, cv2.LINE_AA)

    def _glass_box(self, frame, x1, y1, x2, y2, color, alpha=0.4):
        overlay = frame[y1:y2, x1:x2].copy()
        box = np.full_like(overlay, (20,20,20))
        res = cv2.addWeighted(overlay, 1-alpha, box, alpha, 0)
        frame[y1:y2, x1:x2] = res
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 1, cv2.LINE_AA)

    def _apply_glitch(self, frame):
        h, w = frame.shape[:2]
        y = random.randint(0, h-20)
        frame[y:y+10, :] = np.roll(frame[y:y+10, :], random.randint(-20, 20), axis=1)
        return frame

    def _get_col(self, p):
        return {"fire":(30, 80, 255), "ice":(255, 200, 60), "lightning":(0, 230, 255),
                "ironman":(0, 220, 80), "telekinesis":(220, 50, 200),
                "water":(255, 160, 0), "dark":(180, 0, 255)}.get(p, (255,255,255))

    def notify_power_switch(self, p):
        self._voice_text = f"LINKED: {p.upper()} PROTOCOL."
        self._voice_time = time.time()
    
    def log_gesture(self, g, p):
        if g != self._last_gesture and g not in ("none", "charging"):
            self._last_gesture = g
            self._gesture_history.appendleft((g.upper(), time.time()))
            moves = {"fire": "FLAME VORTEX", "ice": "BLIZZARD", "lightning": "THUNDERBOLT", 
                     "ironman": "HYPER BEAM", "telekinesis": "PSYCHIC", "water": "HYDRO PUMP", "dark": "SHADOW BALL"}
            self._voice_text = f"USE {moves.get(p, 'SPECIAL MOVE')}!"
            self._voice_time = time.time()

    def toggle_help(self): self._show_help = not self._show_help
    
    def _draw_aaa_manual(self, frame):
        overlay = frame.copy()
        cv2.rectangle(overlay, (self.w//2-250, self.h//2-200), (self.w//2+250, self.h//2+200), (0,0,0), -1)
        cv2.addWeighted(frame, 0.1, overlay, 0.9, 0, frame)
        cv2.putText(frame, "NEXUS OS v4.0 - NEURAL MANUAL", (self.w//2-180, self.h//2-160), cv2.FONT_HERSHEY_DUPLEX, 0.7, (0,255,255), 1, cv2.LINE_AA)
        hints = [
            "THUMB UP   -> IGNITE FIRE", "PEACE (V)  -> CRYO FREEZE", "ROCK ON    -> ARC LIGHTNING",
            "SPIDER-MAN -> PHOTON BEAM", "PINKY UP   -> HYDRO PUMP", "4-FINGERS  -> SHADOW BALL",
            "PINCH      -> PSYCHIC GRAB", "BOTH PALMS -> ULTIMATE FINISHER", "FIST HOLD  -> QUANTUM CHARGE"
        ]
        for i, h in enumerate(hints):
            cv2.putText(frame, f"SYNC {i+1}: {h}", (self.w//2-220, self.h//2-100 + i*30), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200,200,200), 1, cv2.LINE_AA)
