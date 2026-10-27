"""Clase base para las etapas del pipeline."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from .contexto import ContextoPipeline

Entrada = TypeVar("Entrada")
Salida = TypeVar("Salida")


class EtapaPipeline(ABC, Generic[Entrada, Salida]):
    """Interfaz genérica para etapas que transforman una entrada en una salida."""

    @abstractmethod
    def ejecutar(self, entrada: Entrada, contexto: ContextoPipeline) -> Salida:
        """Procesa una entrada de dominio usando la configuración de ejecución."""
        pass
