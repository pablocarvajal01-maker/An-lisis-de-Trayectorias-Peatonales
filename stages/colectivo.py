"""Etapa de comparación de experimentos."""

from models.experimento import Experimento
from models.resultado_analisis import ResultadoAnalisis
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline


class ComparacionExperimentos(
    EtapaPipeline[list[Experimento], ResultadoAnalisis]
):
    """Compara resultados de varios experimentos."""

    def ejecutar(
        self,
        experimentos: list[Experimento],
        contexto: ContextoPipeline,
    ) -> ResultadoAnalisis:
        """Retorna los experimentos junto con sus resultados comparativos."""
        raise NotImplementedError("Etapa pendiente de implementación")

    def _comparar(self, experimentos: list[Experimento]) -> dict[str, float]:
        pass