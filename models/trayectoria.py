"""Modelo básico de una trayectoria peatonal."""

from dataclasses import dataclass, field

from .observacion import Observacion


@dataclass
class Trayectoria:
    """Representa las observaciones y cálculos propios de un peatón."""

    id_peaton: int
    observaciones: list[Observacion] = field(default_factory=list)

    def calcular_distancia_total(self) -> float:
        """Calcula la distancia total recorrida por el peatón."""
        raise NotImplementedError

    def calcular_desplazamiento(self) -> float:
        """Calcula el desplazamiento entre el inicio y el final."""
        raise NotImplementedError

    def calcular_velocidad_media(self, fps: float) -> float:
        """Calcula la velocidad media usando la frecuencia del experimento."""
        raise NotImplementedError
