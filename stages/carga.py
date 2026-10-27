"""Etapa de carga de varios experimentos."""

from pathlib import Path

from models.experimento import Experimento
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline


class CargaExperimentos(EtapaPipeline[None, list[Experimento]]):
    """Carga una colección de experimentos desde la ruta configurada."""

    def ejecutar(
        self,
        entrada: None,
        contexto: ContextoPipeline,
    ) -> list[Experimento]:
        """Carga los experimentos indicados por la configuración."""
        raise NotImplementedError("Etapa pendiente de implementación")

    def _cargar_experimentos(self, ruta_entrada: Path) -> list[Experimento]:
        """Carga los experimentos disponibles en la ruta recibida."""
        raise NotImplementedError
