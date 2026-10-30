"""Etapa de preparación de observaciones y trayectorias."""

from models.experimento import Experimento
from models.observacion import Observacion
from models.trayectoria import Trayectoria
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline


class PreparacionTrayectorias(EtapaPipeline[list[Experimento], list[Experimento]]):
    """Agrupa validación, organización y reconstrucción de trayectorias."""

    def ejecutar(
        self,
        experimentos: list[Experimento],
        contexto: ContextoPipeline,
    ) -> list[Experimento]:
        """Prepara las observaciones y trayectorias de cada experimento."""
        for exp in experimentos:
            obs_validadas = self._validar_observaciones(exp.observaciones)
            obs_organizadas = self._organizar_observaciones(obs_validadas)
            exp.trayectorias = self._reconstruir_trayectorias(obs_organizadas)
            print(f"  {exp.nombre}: {len(exp.trayectorias)} trayectorias reconstruidas.")
        return experimentos

    def _validar_observaciones(
        self,
        observaciones: list[Observacion],
    ) -> list[Observacion]:
        """Valida y retorna las observaciones de un experimento."""
        # Filtra observaciones asegurando consistencia básica
        return [
            obs for obs in observaciones 
            if obs.id_peaton is not None and obs.frame >= 0
        ]

    def _organizar_observaciones(
        self,
        observaciones: list[Observacion],
    ) -> dict[int, list[Observacion]]:
        """Organiza las observaciones por identificador de peatón y las ordena temporalmente."""
        por_peaton: dict[int, list[Observacion]] = {}
        for obs in observaciones:
            por_peaton.setdefault(obs.id_peaton, []).append(obs)
        
        # Ordenar estrictamente por frame cada lista de observaciones
        for id_peaton in por_peaton:
            por_peaton[id_peaton].sort(key=lambda o: o.frame)
            
        return por_peaton

    def _reconstruir_trayectorias(
        self,
        observaciones_organizadas: dict[int, list[Observacion]],
    ) -> list[Trayectoria]:
        """Construye trayectorias desde las observaciones organizadas."""
        trayectorias = []
        for id_peaton, obs_list in observaciones_organizadas.items():
            # Opcional: exigir al menos 2 observaciones para formar una trayectoria válida
            if len(obs_list) >= 2:
                trayectorias.append(
                    Trayectoria(id_peaton=id_peaton, observaciones=obs_list)
                )
        return trayectorias