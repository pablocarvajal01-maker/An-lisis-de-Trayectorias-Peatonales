"""Etapa de validación y filtrado de observaciones y trayectorias."""

import math

from models.experimento import Experimento
from models.observacion import Observacion
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline


class ValidacionExperimentos(EtapaPipeline[list[Experimento], list[Experimento]]):
    """Valida y filtra observaciones inconsistentes en cada experimento."""

    def __init__(
        self,
        solo_flag_1: bool = False,
        min_observaciones: int = 2,
        x_max_abs: float = 3.5,
        y_max_abs: float = 12.0,
        velocidad_max: float = 5.0,
    ) -> None:
        self.solo_flag_1 = solo_flag_1
        self.min_observaciones = min_observaciones
        # rango fisico aceptado en m, el corredor mide 5 m de ancho asi que 3.5 deja margen
        # solo saca basura como y = -1260
        self.x_max_abs = x_max_abs
        self.y_max_abs = y_max_abs
        # velocidad maxima creible entre dos observaciones consecutivas en m/s; nadie camina a 5 y sobre eso es ruido del tracking
        self.velocidad_max = velocidad_max

    def ejecutar(
        self,
        experimentos: list[Experimento],
        contexto: ContextoPipeline,
    ) -> list[Experimento]:
        """Aplica las validaciones sobre cada experimento cargado."""
        experimentos_validados = []
        for exp in experimentos:
            exp_validado, fuera_de_rango, saltos = self._validar_experimento(exp, exp.fps_efectivo(contexto.fps))
            experimentos_validados.append(exp_validado)
            print(
                f"  Validación {exp.nombre}: {len(exp.observaciones)} obs iniciales "
                f"-> {len(exp_validado.observaciones)} obs finales "
                f"({fuera_de_rango} fuera de rango, {saltos} saltos imposibles)."
            )
        return experimentos_validados

    def _es_valida(self, obs: Observacion) -> bool:
        """Dice si la observacion cumple el flag pedido y cae en el rango fisico"""
        if self.solo_flag_1 and obs.flag != 1:
            return False
        return abs(obs.x) <= self.x_max_abs and abs(obs.y) <= self.y_max_abs

    def _quitar_saltos(self, observaciones: list[Observacion], fps: float) -> list[Observacion]:
        """Descarta los puntos que implican una velocidad imposible

        Cada punto se compara con el ultimo aceptado y no con el anterior bruto x siaca,
        por lo cual un punto malo aislado se descarta y el siguiente bueno se conserva
        recibe las observaciones de un peaton ordenadas por frame y sin frames repetidos
        """
        aceptadas: list[Observacion] = []
        for obs in observaciones:
            if aceptadas:
                ultima = aceptadas[-1]
                dt = (obs.frame - ultima.frame) / fps
                distancia = math.hypot(obs.x - ultima.x, obs.y - ultima.y)
                if distancia / dt > self.velocidad_max:
                    continue
            aceptadas.append(obs)
        return aceptadas

    def _validar_experimento(
        self,
        experimento: Experimento,
        fps: float,
    ) -> tuple[Experimento, int, int]:
        """Devuelve el experimento validado, los puntos fuera de rango y los saltos descartados"""
        # 1. Filtrar observaciones individuales según flag o validez básica
        observaciones_validas = list(filter(self._es_valida, experimento.observaciones))
        fuera_de_rango = len(experimento.observaciones) - len(observaciones_validas)

        # 2. Agrupar por peatón para validar tamaño de trayectoria
        por_peaton: dict[int, list[Observacion]] = {}
        for obs in observaciones_validas:
            por_peaton.setdefault(obs.id_peaton, []).append(obs)

        observaciones_filtradas: list[Observacion] = []
        saltos = 0
        for obs_list in por_peaton.values():
            # Ordenar temporalmente por frame por seguridad
            obs_list.sort(key=lambda o: o.frame)

            # Validar que los frames sean estrictamente crecientes (sin duplicados exactos de frame maliciosos)
            obs_unicas_frame = []
            ultimo_frame = -1
            for obs in obs_list:
                if obs.frame > ultimo_frame:
                    obs_unicas_frame.append(obs)
                    ultimo_frame = obs.frame

            # Quitar los saltos imposibles de posicion
            sin_saltos = self._quitar_saltos(obs_unicas_frame, fps)
            saltos += len(obs_unicas_frame) - len(sin_saltos)

            # Descartar si tiene menos observaciones que el mínimo requerido
            if len(sin_saltos) >= self.min_observaciones:
                observaciones_filtradas.extend(sin_saltos)

        # Retornar un nuevo objeto Experimento con las observaciones validadas
        validado = Experimento(
            nombre=experimento.nombre,
            observaciones=observaciones_filtradas,
            trayectorias=experimento.trayectorias,
            resultados_individuales=experimento.resultados_individuales,
            resultados_colectivos=experimento.resultados_colectivos,
            fps=experimento.fps,
        )
        return validado, fuera_de_rango, saltos