"""Etapa de análisis individual de los experimentos."""

from models.experimento import Experimento
from models.trayectoria import Trayectoria
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline


class AnalisisIndividual(EtapaPipeline[list[Experimento], list[Experimento]]):
    """Coordina el análisis de múltiples trayectorias y reúne sus indicadores."""

    def ejecutar(
        self,
        experimentos: list[Experimento],
        contexto: ContextoPipeline,
    ) -> list[Experimento]:
        """Analiza las trayectorias de cada experimento."""
        raise NotImplementedError("Etapa pendiente de implementación")

    def _calcular_indicadores(
        self,
        trayectoria: Trayectoria,
        fps: float | None,
    ) -> dict[str, float]:
        """Calcula los indicadores individuales de una trayectoria."""
        raise NotImplementedError

    def _detectar_detenciones(
        self,
        trayectoria: Trayectoria,
        fps: float | None,
    ) -> list[tuple[int, int]]:
        """Identifica intervalos de detención de una trayectoria."""
        raise NotImplementedError
