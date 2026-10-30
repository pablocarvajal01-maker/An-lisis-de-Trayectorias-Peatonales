"""Modelo básico de una observación peatonal"""

from dataclasses import dataclass


# frozen + slots: son ma o meno 500 mil observaciones por archivo, así que mejor que pesen poco
# y que nadie las ande modificando por ahi
@dataclass(frozen=True, slots=True)
class Observacion:
    """Posicion registrada de un peaton en un frame (coordenadas en metros)"""

    # ojo esto sale de la columna 1 del archivo "number" la columna "id" trae -1
    # para un monton de gente distinta, asi que esa no sirve para identificar a nadie
    id_peaton: int
    frame: int
    x: float
    y: float
    z: float
    # 1 = detección directa; los otros valores son puntos interpolados o editados a mano.
    flag: int = 1