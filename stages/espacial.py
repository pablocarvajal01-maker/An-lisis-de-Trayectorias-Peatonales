"""Etapa de análisis espacial de los experimentos."""

import math
from models.experimento import Experimento
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline


class AnalisisEspacial(EtapaPipeline[list[Experimento], list[Experimento]]):
    """Divide el espacio en zonas y calcula métricas locales (conteo, velocidad, tiempo)."""

    def __init__(self, num_zonas: int = 5) -> None:
        self.num_zonas = num_zonas

    def ejecutar(
        self,
        experimentos: list[Experimento],
        contexto: ContextoPipeline,
    ) -> list[Experimento]:
        """Ejecuta el análisis espacial para cada experimento."""
        fps = contexto.fps if contexto.fps is not None else 25.0

        for exp in experimentos:
            zonas = self._definir_zonas(exp)
            
            # Inicializar resultados por zona
            resultados_zonas = {
                i: {"limites_x": limites, "peatones": 0, "tiempos_cruce": [], "velocidades": []} 
                for i, limites in enumerate(zonas)
            }

            for tray in exp.trayectorias:
                self._analizar_trayectoria_en_zonas(tray, resultados_zonas, fps)

            # Consolidar promedios finales
            for data in resultados_zonas.values():
                tiempos = data["tiempos_cruce"]
                vels = data["velocidades"]
                data["tiempo_medio_cruce"] = sum(tiempos) / len(tiempos) if tiempos else 0.0
                data["velocidad_media"] = sum(vels) / len(vels) if vels else 0.0
                
                # Limpiar listas temporales
                del data["tiempos_cruce"]
                del data["velocidades"]

            exp.resultados_colectivos["analisis_espacial"] = resultados_zonas
            print(f"  {exp.nombre}: análisis espacial completado en {self.num_zonas} zonas.")

        return experimentos

    def _definir_zonas(self, experimento: Experimento) -> list[tuple[float, float]]:
        """Divide el corredor longitudinalmente en zonas de igual tamaño."""
        if not experimento.trayectorias:
            return []
        
        x_min = min(obs.x for tray in experimento.trayectorias for obs in tray.observaciones)
        x_max = max(obs.x for tray in experimento.trayectorias for obs in tray.observaciones)
        ancho = (x_max - x_min) / self.num_zonas
        
        return [(x_min + i * ancho, x_min + (i + 1) * ancho) for i in range(self.num_zonas)]

    def _analizar_trayectoria_en_zonas(self, trayectoria, resultados_zonas: dict, fps: float) -> None:
        """Asigna las observaciones a sus zonas y calcula métricas locales."""
        obs_por_zona = {i: [] for i in resultados_zonas.keys()}
        
        for obs in trayectoria.observaciones:
            for i, data_zona in resultados_zonas.items():
                x_min, x_max = data_zona["limites_x"]
                if x_min <= obs.x <= x_max:
                    obs_por_zona[i].append(obs)
                    break
                    
        for i, observaciones in obs_por_zona.items():
            if len(observaciones) >= 2:
                resultados_zonas[i]["peatones"] += 1
                
                t_cruce = (observaciones[-1].frame - observaciones[0].frame) / fps
                resultados_zonas[i]["tiempos_cruce"].append(t_cruce)
                
                distancia = sum(
                    math.hypot(observaciones[j].x - observaciones[j-1].x, 
                               observaciones[j].y - observaciones[j-1].y)
                    for j in range(1, len(observaciones))
                )
                if t_cruce > 0:
                    resultados_zonas[i]["velocidades"].append(distancia / t_cruce)