"""Etapa de análisis espacial, densidad y flujo."""

from models.experimento import Experimento
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline


class AnalisisEspacial(EtapaPipeline[list[Experimento], list[Experimento]]):
    """Agrupa el análisis por zonas y los cálculos de densidad y flujo."""

    def ejecutar(
        self,
        experimentos: list[Experimento],
        contexto: ContextoPipeline,
    ) -> list[Experimento]:
        """Analiza las zonas, la densidad y el flujo de cada experimento."""
        raise NotImplementedError("Etapa pendiente de implementación")

    def _analizar_zonas(self, experimento: Experimento) -> dict[str, float]:
        pass

    def _calcular_densidad(self, experimento: Experimento) -> dict[str, float]:
        pass

    def _calcular_flujo(
        self,
        experimento: Experimento,
        fps: float | None,
    ) -> dict[str, float]:
        pass