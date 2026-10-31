"""Entidad que agrupa los datos y resultados de un experimento."""

from dataclasses import dataclass, field

from .observacion import Observacion
from .trayectoria import Trayectoria


@dataclass
class Experimento:
    """Representa un conjunto de observaciones y sus análisis."""

    nombre: str
    observaciones: list[Observacion] = field(default_factory=list)
    trayectorias: list[Trayectoria] = field(default_factory=list)
    resultados_individuales: dict[int, dict[str, float]] = field(default_factory=dict)
    resultados_colectivos: dict[str, float] = field(default_factory=dict)
    # fps que declara el archivo, None si no dice nada; ahi se usa el de --fps
    fps: float | None = None

    def fps_efectivo(self, fps_por_defecto: float) -> float:
        """fps propio del experimento si lo trae, si no el que viene por defecto"""
        return self.fps if self.fps is not None else fps_por_defecto