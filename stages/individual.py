"""Etapa de análisis individual de los experimentos."""

import math
from models.experimento import Experimento
from models.trayectoria import Trayectoria
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline


class AnalisisIndividual(EtapaPipeline[list[Experimento], list[Experimento]]):
    """Coordina el análisis de múltiples trayectorias y reúne sus indicadores."""

    def __init__(self, umbral_detencion: float = 0.1) -> None:
        # Velocidad en m/s bajo la cual se considera que el peatón está detenido
        self.umbral_detencion = umbral_detencion

    def ejecutar(
        self,
        experimentos: list[Experimento],
        contexto: ContextoPipeline,
    ) -> list[Experimento]:
        """Analiza las trayectorias de cada experimento."""
        fps = contexto.fps

        for exp in experimentos:
            resultados = {}
            for tray in exp.trayectorias:
                # 1. Calculamos los indicadores base
                indicadores = self._calcular_indicadores(tray, fps)
                
                # 2. Detectamos detenciones
                detenciones = self._detectar_detenciones(tray, fps)
                
                # Opcional: calcular el tiempo total detenido para mantener el dict[str, float]
                tiempo_detenido = sum((fin - inicio) for inicio, fin in detenciones) / fps if fps else 0.0
                indicadores["tiempo_detenido"] = tiempo_detenido
                
                # Guardamos en el diccionario usando el id_peaton como llave
                resultados[tray.id_peaton] = indicadores
            
            exp.resultados_individuales = resultados
            print(f"  {exp.nombre}: análisis individual completado para {len(resultados)} peatones.")

        return experimentos

    def _calcular_indicadores(
        self,
        trayectoria: Trayectoria,
        fps: float,
    ) -> dict[str, float]:
        """Calcula los indicadores individuales de una trayectoria."""
        x0, y0 = trayectoria.posicion_inicial
        x1, y1 = trayectoria.posicion_final
        
        eficiencia = trayectoria.calcular_eficiencia()
        
        return {
            "pos_inicial_x": x0,
            "pos_inicial_y": y0,
            "pos_final_x": x1,
            "pos_final_y": y1,
            "tiempo_total": trayectoria.calcular_tiempo_total(fps),
            "distancia_total": trayectoria.calcular_distancia_total(),
            "desplazamiento": trayectoria.calcular_desplazamiento(),
            "velocidad_media": trayectoria.calcular_velocidad_media(fps),
            "velocidad_maxima": trayectoria.calcular_velocidad_maxima(fps),
            "eficiencia": eficiencia if eficiencia is not None else 0.0,
        }

    def _detectar_detenciones(
        self,
        trayectoria: Trayectoria,
        fps: float,
    ) -> list[tuple[int, int]]:
        """Identifica intervalos de detención de una trayectoria."""
        detenciones = []
        if len(trayectoria.observaciones) < 2:
            return detenciones
        
        dt = 1.0 / fps

        en_detencion = False
        frame_inicio = -1

        # Revisamos la velocidad instantánea entre cada par de observaciones
        for i in range(1, len(trayectoria.observaciones)):
            obs_ant = trayectoria.observaciones[i-1]
            obs_act = trayectoria.observaciones[i]
            
            distancia = math.hypot(obs_act.x - obs_ant.x, obs_act.y - obs_ant.y)
            velocidad = distancia / dt
            
            if velocidad < self.umbral_detencion:
                if not en_detencion:
                    en_detencion = True
                    frame_inicio = obs_ant.frame
            else:
                if en_detencion:
                    en_detencion = False
                    detenciones.append((frame_inicio, obs_act.frame))
        
        # Si la trayectoria termina y el peatón seguía detenido
        if en_detencion:
            detenciones.append((frame_inicio, trayectoria.observaciones[-1].frame))

        return detenciones