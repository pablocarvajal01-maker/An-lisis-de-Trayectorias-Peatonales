"""Configuración de una ejecución del pipeline."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ContextoPipeline:
    """Contiene únicamente las opciones de ejecución del programa."""

    ruta_entrada: Path
    ruta_salida: Path
    fps: float | None = None
