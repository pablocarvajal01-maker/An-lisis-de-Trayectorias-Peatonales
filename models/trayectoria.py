"""Modelo básico de una trayectoria peatonal."""

import math
from dataclasses import dataclass, field
from itertools import pairwise

from .observacion import Observacion


@dataclass
class Trayectoria:
    """Observaciones de un peatón y los cálculos que salen de ellas

    """

    id_peaton: int
    observaciones: list[Observacion] = field(default_factory=list)

    @property
    def posicion_inicial(self) -> tuple[float, float]:
        """Posición (x, y) de la primera observación."""
        primera = self.observaciones[0]
        return (primera.x, primera.y)

    @property
    def posicion_final(self) -> tuple[float, float]:
        """Posición (x, y) de la última observación."""
        ultima = self.observaciones[-1]
        return (ultima.x, ultima.y)

    def distancias_tramos(self) -> list[float]:
        """Distancia entre cada par de observaciones consecutivas [m].

        d_i = sqrt((x_{i+1} - x_i)^2 + (y_{i+1} - y_i)^2)
        """
        return [
            math.hypot(b.x - a.x, b.y - a.y)
            for a, b in pairwise(self.observaciones)
        ]

    def velocidades_tramos(self, fps: float) -> list[float]:
        """Velocidad entre cada par de observaciones consecutivas [m/s].

        v_i = d_i / dt_i, con dt_i = (frame_{i+1} - frame_i) / fps
        """
        self._validar_fps(fps)
        velocidades = []
        for a, b in pairwise(self.observaciones):
            delta_frames = b.frame - a.frame
            # si dt es 0 o negativo se cae todo (división por cero), así que mejor
            # avisar fuerte y claro que callarse y cagarse
            if delta_frames <= 0:
                raise ValueError(
                    f"Peatón {self.id_peaton}: frames no crecientes "
                    f"({a.frame} -> {b.frame})."
                )
            distancia = math.hypot(b.x - a.x, b.y - a.y)
            velocidades.append(distancia / (delta_frames / fps))
        return velocidades

    def calcular_distancia_total(self) -> float:
        """Calcula la distancia total recorrida por el peatón [m]."""
        # fsum suma más "justo" que sum cuando son miles de numeritos chicos.
        return math.fsum(self.distancias_tramos())

    def calcular_desplazamiento(self) -> float:
        """Calcula el desplazamiento entre el inicio y el final [m]."""
        if len(self.observaciones) < 2:
            return 0.0
        (x0, y0), (x1, y1) = self.posicion_inicial, self.posicion_final
        return math.hypot(x1 - x0, y1 - y0)

    def calcular_tiempo_total(self, fps: float) -> float:
        """Tiempo entre la primera y la última observación [s]."""
        self._validar_fps(fps)
        if len(self.observaciones) < 2:
            return 0.0
        return (self.observaciones[-1].frame - self.observaciones[0].frame) / fps

    def calcular_velocidad_media(self, fps: float) -> float:
        """Calcula la velocidad media usando la frecuencia del experimento [m/s]."""
        tiempo = self.calcular_tiempo_total(fps)
        return self.calcular_distancia_total() / tiempo if tiempo > 0 else 0.0

    def calcular_velocidad_maxima(self, fps: float) -> float:
        """Velocidad máxima entre observaciones consecutivas [m/s]."""
        # esta es la cruda frame a frame, y el ruido del tracking la infla un poco
        return max(self.velocidades_tramos(fps), default=0.0)

    def calcular_eficiencia(self) -> float | None:
        """E = D / Dr (desplazamiento / distancia recorrida).

        Cerca de 1 = camino casi directo. None si el peatón no se movió (Dr = 0),
        porque ahí la división no tiene sentido.
        """
        recorrida = self.calcular_distancia_total()
        if recorrida == 0:
            return None
        return self.calcular_desplazamiento() / recorrida

    @staticmethod
    def _validar_fps(fps: float) -> None:
        if fps is None or fps <= 0:
            raise ValueError(f"fps debe ser un número positivo, llegó: {fps!r}")