"""Etapa de validación y filtrado de observaciones y trayectorias."""

from models.experimento import Experimento
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline


class ValidacionExperimentos(EtapaPipeline[list[Experimento], list[Experimento]]):
    """Valida y filtra observaciones inconsistentes en cada experimento."""

    def __init__(self, solo_flag_1: bool = False, min_observaciones: int = 2) -> None:
        self.solo_flag_1 = solo_flag_1
        self.min_observaciones = min_observaciones

    def ejecutar(
        self,
        experimentos: list[Experimento],
        contexto: ContextoPipeline,
    ) -> list[Experimento]:
        """Aplica las validaciones sobre cada experimento cargado."""
        experimentos_validados = []
        for exp in experimentos:
            exp_validado = self._validar_experimento(exp)
            experimentos_validados.append(exp_validado)
            print(
                f"  Validación {exp.nombre}: {len(exp.observaciones)} obs iniciales "
                f"-> {len(exp_validado.observaciones)} obs finales."
            )
        return experimentos_validados

    def _validar_experimento(self, experimento: Experimento) -> Experimento:
        # 1. Filtrar observaciones individuales según flag o validez básica
        observaciones_validas = []
        for obs in experimento.observaciones:
            if self.solo_flag_1 and obs.flag != 1:
                continue
            observaciones_validas.append(obs)

        # 2. Agrupar por peatón para validar tamaño de trayectoria
        por_peaton: dict[int, list] = {}
        for obs in observaciones_validas:
            por_peaton.setdefault(obs.id_peaton, []).append(obs)

        observaciones_filtradas = []
        for id_peaton, obs_list in por_peaton.items():
            # Ordenar temporalmente por frame por seguridad
            obs_list.sort(key=lambda o: o.frame)

            # Descartar si tiene menos observaciones que el mínimo requerido
            if len(obs_list) < self.min_observaciones:
                continue

            # Validar que los frames sean estrictamente crecientes (sin duplicados exactos de frame maliciosos)
            obs_unicas_frame = []
            ultimo_frame = -1
            for obs in obs_list:
                if obs.frame > ultimo_frame:
                    obs_unicas_frame.append(obs)
                    ultimo_frame = obs.frame

            if len(obs_unicas_frame) >= self.min_observaciones:
                observaciones_filtradas.extend(obs_unicas_frame)

        # Retornar un nuevo objeto Experimento con las observaciones validadas
        return Experimento(
            nombre=experimento.nombre,
            observaciones=observaciones_filtradas,
            trayectorias=experimento.trayectorias,
            resultados_individuales=experimento.resultados_individuales,
            resultados_colectivos=experimento.resultados_colectivos,
        )