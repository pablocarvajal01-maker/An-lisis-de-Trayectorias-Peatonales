"""Etapa de exportación de resultados."""

from pathlib import Path

from models.resultado_analisis import ResultadoAnalisis
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline


class ExportacionResultados(EtapaPipeline[ResultadoAnalisis, None]):
    """Exporta los resultados de los experimentos y su comparación."""

    def ejecutar(
        self,
        resultados: ResultadoAnalisis,
        contexto: ContextoPipeline,
    ) -> None:
        """Guarda los resultados en la ruta de salida configurada."""
        raise NotImplementedError("Etapa pendiente de implementación")

    def _exportar(self, resultados: ResultadoAnalisis, ruta_salida: Path) -> None:
        """Exporta los resultados a la ruta indicada."""
        raise NotImplementedError
