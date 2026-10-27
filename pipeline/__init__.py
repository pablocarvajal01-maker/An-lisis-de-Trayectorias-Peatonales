"""Infraestructura para coordinar etapas de procesamiento."""

from .contexto import ContextoPipeline
from .etapa import EtapaPipeline
from .pipeline import Pipeline

__all__ = ["ContextoPipeline", "EtapaPipeline", "Pipeline"]
