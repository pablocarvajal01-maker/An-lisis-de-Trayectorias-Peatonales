"""Resultados de los análisis realizados sobre varios experimentos."""

from dataclasses import dataclass

from .experimento import Experimento


@dataclass
class ResultadoAnalisis:
    """Conserva los experimentos y los resultados de su comparación."""

    experimentos: list[Experimento]
    comparacion: dict[str, float]
