"""
effects_engine.py v4.0 — AAA-QUALITY CINEMATIC ENGINE
Next-gen rendering pipeline: Post-processing, Volumetric Energy, and Time Scaling.
"""

import cv2
import numpy as np
import time
import random
import math

class EffectsEngine:
    MAX_PARTICLES = 1200 # AAA-tier density

    def __init__(self, width, height):
        self.w = width
        self.h = height
        # [x, y, vx, vy, life, decay, size, color, gravity, turbulence, kind]
        self.particles = [] 
        self._shake = 0.0
        self._flash_alpha = 0.0
        self._flash_color = (0, 0, 0)
        self._last_t = time.time()
        self._time_scale = 1.0 # For Slow-Motion
        
        # Shader Buffers
        self.bloom_buffer = np.zeros((height, width, 3), dtype=np.uint8)
        self.fx_layer = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Pre-calculated LUT for chromatic aberration
        self.ca_offset = 3 # pixels

    def compose(self, frame, hands, state):
        now = time.time()
        # Apply Time Scaling (Slow-Mo)
        dt = (now - self._last_t) * self._time_scale
        dt = min(dt, 0.05)
        self._last_t = now

        # Reset Layer
        self.fx_layer[:] = 0

        # 1. AAA Signature Spawners
        pos = hands[0].palm_center if hands else None
        if pos:
            pwr = state.power
            gst = state.gesture
            chg = state.charge_level
            
            # Slow-mo during Ultimate
            if gst == "ultimate": self._time_scale = 0.3
            else: self._time_scale = 1.0

            if gst == "open_palm":
                if pwr == "fire":      self._spawn_dragon_flame(pos, chg)
                elif pwr == "ice":     self._spawn_blizzard_crystals(pos, chg)
                elif pwr == "lightning":self._spawn_arc_sparks(pos, chg)
                elif pwr == "ironman":  self._spawn_photon_beam(pos, chg)
                elif pwr == "water":    self._spawn_hydro_vortex(pos, chg)
                elif pwr == "dark":     self._spawn_singularity_dust(pos, chg)
                elif pwr == "telekinesis": self._spawn_psionic_rings(pos, chg)
            
            elif gst == "blast":
                self._spawn_supernova(pos, pwr)

        # 2. Update Physics
        self._update(dt)

        # 3. Spatial Distortion (Cinematic Lensing)
        if pos and state.gesture == "open_palm":
            if pwr == "water": frame = self._cinematic_remap(frame, pos, 150, "ripple", chg)
            elif pwr == "dark": frame = self._cinematic_remap(frame, pos, 200, "gravity", chg)
            elif pwr == "fire": frame = self._cinematic_remap(frame, pos, 120, "heat", chg)

        # 4. AAA Rendering & Post-Processing
        frame = self._render_volumetric(frame)
        frame = self._apply_bloom(frame)
        frame = self._apply_chromatic_aberration(frame)
        
        # 5. Global FX
        if self._flash_alpha > 0.01:
            cv2.addWeighted(frame, 1-self._flash_alpha, np.full_like(frame, self._flash_color), self._flash_alpha, 0, frame)
            self._flash_alpha *= 0.8
            
        return self._apply_shake(frame)

    # ── AAA Signature Spawners ───────────────────────────────────────

    def _spawn_dragon_flame(self, pos, charge):
        for _ in range(int(10 + charge*20)):
            a = -1.57 + random.uniform(-0.5, 0.5)
            sp = random.uniform(4, 10)
            self._add(pos[0], pos[1], math.cos(a)*sp, math.sin(a)*sp, 1.2, 0.03, 15, (0, 100, 255), -0.3, 0.5, 0)

    def _spawn_blizzard_crystals(self, pos, charge):
        for _ in range(int(8 + charge*15)):
            self._add(random.randint(0, self.w), 0, random.uniform(-3, 3), random.uniform(5, 12), 2.0, 0.02, 8, (255, 230, 200), 0.1, 1.5, 2)

    def _spawn_arc_sparks(self, pos, charge):
        for _ in range(int(5 + charge*10)):
            a = random.uniform(0, 6.28)
            sp = random.uniform(8, 20)
            self._add(pos[0], pos[1], math.cos(a)*sp, math.sin(a)*sp, 0.5, 0.12, 3, (0, 255, 255), 0.2, 3.0, 1)

    def _spawn_photon_beam(self, pos, charge):
        # Beam core particles
        for _ in range(int(15 + charge*30)):
            self._add(pos[0]+random.randint(-10,10), pos[1], 0, -25, 0.4, 0.1, 12, (200, 255, 100), 0, 0.1, 1)

    def _spawn_hydro_vortex(self, pos, charge):
        for _ in range(int(8 + charge*12)):
            a = random.uniform(0, 6.28); r = 40 + charge*50
            px = pos[0] + math.cos(a)*r; py = pos[1] + math.sin(a)*r
            self._add(px, py, (pos[0]-px)*0.15, (pos[1]-py)*0.15, 1.2, 0.04, 12, (255, 180, 50), 0.5, 0.2, 3)

    def _spawn_singularity_dust(self, pos, charge):
        # Dark energy particles swirling inward
        for _ in range(12):
            a = random.uniform(0, 6.28); r = 100 + charge*80
            px = pos[0] + math.cos(a)*r; py = pos[1] + math.sin(a)*r
            # Spiral velocity
            vx = (pos[0]-px)*0.1 + math.cos(a+1.5)*5
            vy = (pos[1]-py)*0.1 + math.sin(a+1.5)*5
            self._add(px, py, vx, vy, 1.5, 0.03, 6, (180, 0, 255), 0, 0.5, 0)

    def _spawn_psionic_rings(self, pos, charge):
        self._add(pos[0], pos[1], 0, 0, 1.0, 0.025, 5, (255, 50, 220), 0, 0, 4)

    def _spawn_supernova(self, pos, pwr):
        self._shake = 30.0
        self._flash_alpha = 0.6
        col = self._get_col(pwr)
        self._flash_color = col
        for _ in range(200):
            a = random.uniform(0, 6.28); sp = random.uniform(8, 30)
            self._add(pos[0], pos[1], math.cos(a)*sp, math.sin(a)*sp, 1.5, 0.02, 18, col, 0.2, 0, 0)

    def _get_col(self, p):
        return {"fire":(0,100,255), "ice":(255,255,200), "lightning":(0,255,255), 
                "ironman":(0,255,100), "water":(255,150,50), "dark":(200,0,255)}.get(p, (255,255,255))

    # ── Rendering Pipeline ───────────────────────────────────────────

    def _add(self, x, y, vx, vy, life, decay, size, color, gravity, turb, kind):
        if len(self.particles) < self.MAX_PARTICLES:
            self.particles.append([x, y, vx, vy, life, decay, size, color, gravity, turb, kind])

    def _update(self, dt):
        keep = []
        for p in self.particles:
            p[4] -= p[5] # life
            if p[4] <= 0: continue
            if p[9] > 0: p[2] += random.uniform(-p[9], p[9]); p[3] += random.uniform(-p[9], p[9])
            p[0] += p[2]; p[1] += p[3]; p[3] += p[8]
            if 0 <= p[0] < self.w and 0 <= p[1] < self.h: keep.append(p)
        self.particles = keep

    def _render_volumetric(self, frame):
        if not self.particles: return frame
        # Draw all particles to fx_layer
        for p in self.particles:
            x, y, life, sz, col, kind = int(p[0]), int(p[1]), p[4], int(p[6]*p[4]), p[7], p[10]
            c = tuple(int(ch * life) for ch in col)
            if kind == 0: # Volumetric Sphere
                cv2.circle(self.fx_layer, (x, y), sz, c, -1, cv2.LINE_AA)
                if life > 0.7: cv2.circle(self.fx_layer, (x, y), sz+4, c, 1, cv2.LINE_AA)
            elif kind == 1: # Energy Bolt
                vx, vy = int(p[2]*1.5), int(p[3]*1.5)
                cv2.line(self.fx_layer, (x, y), (x-vx, y-vy), c, 3, cv2.LINE_AA)
                cv2.line(self.fx_layer, (x, y), (x-vx, y-vy), (255,255,255), 1, cv2.LINE_AA)
            elif kind == 2: # Crystal
                s2 = sz // 2
                cv2.line(self.fx_layer, (x-s2, y), (x+s2, y), c, 2, cv2.LINE_AA)
                cv2.line(self.fx_layer, (x, y-s2), (x, y+s2), c, 2, cv2.LINE_AA)
            elif kind == 3: # Hydro Blob
                cv2.circle(self.fx_layer, (x, y), sz, c, -1, cv2.LINE_AA)
                cv2.circle(self.fx_layer, (x, y), sz-2, (255,255,255), 1, cv2.LINE_AA)
            elif kind == 4: # Psionic Ring
                r = int((1-life)*120)
                cv2.circle(self.fx_layer, (x, y), r, c, 2, cv2.LINE_AA)
                cv2.circle(self.fx_layer, (x, y), r-10, c, 1, cv2.LINE_AA)
        
        # Blend FX layer
        return cv2.addWeighted(frame, 1.0, self.fx_layer, 0.95, 0)

    # ── AAA Shaders (Post-Processing) ───────────────────────────────

    def _apply_bloom(self, frame):
        # Extract bright areas
        bloom = cv2.resize(self.fx_layer, (0, 0), fx=0.25, fy=0.25)
        bloom = cv2.GaussianBlur(bloom, (15, 15), 0)
        bloom = cv2.resize(bloom, (self.w, self.h))
        return cv2.addWeighted(frame, 1.0, bloom, 0.5, 0)

    def _apply_chromatic_aberration(self, frame):
        # Split channels and offset
        b, g, r = cv2.split(frame)
        # Shift Blue and Red slightly
        b = np.roll(b, self.ca_offset, axis=1)
        r = np.roll(r, -self.ca_offset, axis=1)
        return cv2.merge([b, g, r])

    def _cinematic_remap(self, frame, pos, r, mode, charge):
        h, w = frame.shape[:2]
        y1, y2 = max(0, pos[1]-r), min(h, pos[1]+r)
        x1, x2 = max(0, pos[0]-r), min(w, pos[0]+r)
        region = frame[y1:y2, x1:x2].copy()
        rh, rw = region.shape[:2]
        xs = np.arange(rw, dtype=np.float32); ys = np.arange(rh, dtype=np.float32)
        xg, yg = np.meshgrid(xs, ys)
        dx = xg - (pos[0]-x1); dy = yg - (pos[1]-y1)
        dist = np.sqrt(dx**2 + dy**2) + 1e-6
        
        if mode == "ripple": strength = 20 * np.exp(-dist/60)
        elif mode == "gravity": strength = -60 * (1/(dist/50 + 1))
        else: strength = 6 * np.sin(dist*0.1 - time.time()*12)
        
        if mode == "ripple":
            map_x = (xg + np.sin(dist*0.12 - time.time()*15)*strength).astype(np.float32)
            map_y = (yg + np.cos(dist*0.12 - time.time()*15)*strength).astype(np.float32)
        else:
            map_x = (xg + dx/dist*strength).astype(np.float32)
            map_y = (yg + dy/dist*strength).astype(np.float32)
            
        frame[y1:y2, x1:x2] = cv2.remap(region, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        return frame

    def _apply_shake(self, frame):
        if self._shake < 0.5: return frame
        dx, dy = int(random.uniform(-self._shake, self._shake)), int(random.uniform(-self._shake, self._shake))
        M = np.float32([[1,0,dx],[0,1,dy]])
        frame = cv2.warpAffine(frame, M, (self.w, self.h))
        self._shake *= 0.85
        return frame
