"""Modelo básico de una observación peatonal."""

from dataclasses import dataclass


@dataclass
class Observacion:
    """Representa la posición registrada de un peatón en un cuadro."""

    id_peaton: int
    frame: int
    x: float
    y: float
    z: float
