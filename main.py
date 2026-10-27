"""Punto de entrada"""

import argparse
from pathlib import Path
from typing import Sequence

from pipeline.contexto import ContextoPipeline
from pipeline.pipeline import Pipeline
from stages import (

    AnalisisIndividual,
    CargaExperimentos,

    ExportacionResultados,
    PreparacionTrayectorias,
)


def crear_parser() -> argparse.ArgumentParser:
    """Crea el analizador de argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Pipeline inicial: Análisis de Trayectorias Peatonales."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("./data"),
        help="Archivo o directorio de entrada (por defecto: ./data).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("./results"),
        help="Directorio de salida (por defecto: ./results).",
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=None,
        help="Frecuencia de muestreo del experimento, en cuadros por segundo.",
    )
    return parser


def main(argumentos: Sequence[str] | None = None) -> int:
    """Configura y ejecuta las etapas del pipeline."""
    configuracion = crear_parser().parse_args(argumentos)
    contexto = ContextoPipeline(
        ruta_entrada=configuracion.input,
        ruta_salida=configuracion.output,
        fps=configuracion.fps,
    )
    etapas = [
        CargaExperimentos(),
        PreparacionTrayectorias(),
        AnalisisIndividual(),
        #...
        ExportacionResultados(),
    ]
    pipeline = Pipeline(etapas)

    print("Configuración seleccionada:")
    print(f"  Entrada: {contexto.ruta_entrada}")
    print(f"  Salida: {contexto.ruta_salida}")
    frecuencia = str(contexto.fps) if contexto.fps is not None else "no especificada"
    print(f"  Frecuencia (fps): {frecuencia}")

    return 0 if pipeline.ejecutar(contexto) else 1


if __name__ == "__main__":
    raise SystemExit(main())
