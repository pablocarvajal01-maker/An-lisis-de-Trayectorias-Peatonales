"""Punto de entrada"""

import argparse
from pathlib import Path
from typing import Sequence

from pipeline.contexto import ContextoPipeline, FPS_EXPERIMENTOS
from pipeline.pipeline import Pipeline
from stages import (
    AnalisisEspacial,
    AnalisisIndividual,
    CargaExperimentos,
    ComparacionExperimentos,
    ExportacionResultados,
    PreparacionTrayectorias,
    ValidacionExperimentos
)


def crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pipeline inicial: Análisis de Trayectorias Peatonales"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("./data"),
        help="Archivo o directorio de entrada (por defecto: ./data)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("./results"),
        help="Directorio de salida (por defecto: ./results)",
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=FPS_EXPERIMENTOS,
        help=f"Frecuencia de muestreo de los experimentos, en cuadros por segundo (por defecto: {FPS_EXPERIMENTOS:g})",
    )
    return parser


def main(argumentos: Sequence[str] | None = None) -> int:
    """Configura y ejecuta las etapas del pipeline"""
    configuracion = crear_parser().parse_args(argumentos)
    contexto = ContextoPipeline(
        ruta_entrada=configuracion.input,
        ruta_salida=configuracion.output,
        fps=configuracion.fps,
    )
    etapas = [
        CargaExperimentos(),
        ValidacionExperimentos(),
        PreparacionTrayectorias(),
        AnalisisIndividual(),
        AnalisisEspacial(),
        ComparacionExperimentos(),
        ExportacionResultados(),
    ]
    pipeline = Pipeline(etapas)

    print("Configuración seleccionada:")
    print(f"  Entrada: {contexto.ruta_entrada}")
    print(f"  Salida: {contexto.ruta_salida}")
    print(f"  Frecuencia (fps): {contexto.fps:g}")

    return 0 if pipeline.ejecutar(contexto) else 1


if __name__ == "__main__":
    raise SystemExit(main())