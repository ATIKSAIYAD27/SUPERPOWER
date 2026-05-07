"""Base class for all superhero powers."""

from abc import ABC, abstractmethod
import numpy as np


class basePower(ABC):
    def __init__(self, width: int, height: int):
        self.w = width
        self.h = height
        self.cooldown = 0.0
        self.cooldown_max = 1.0
        self.active = False

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def color(self) -> tuple: ...

    @abstractmethod
    def activate(self, frame: np.ndarray, hands: list, gesture: str, charge: float) -> np.ndarray: ...

    def tick(self, dt: float):
        """Called every frame. Reduces cooldown."""
        self.cooldown = max(0.0, self.cooldown - dt)

    def trigger_cooldown(self):
        self.cooldown = self.cooldown_max

    @property
    def ready(self) -> bool:
        return self.cooldown <= 0.0
