"""Etapa de análisis colectivo y comparación de experimentos."""

from models.experimento import Experimento
from models.resultado_analisis import ResultadoAnalisis
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline


class ComparacionExperimentos(EtapaPipeline[list[Experimento], ResultadoAnalisis]):

    def ejecutar(
        self,
        experimentos: list[Experimento],
        contexto: ContextoPipeline,
    ) -> ResultadoAnalisis:

        comparacion = {}

        for exp in experimentos:
            # cada archivo puede traer su fps, si no se usa el del contexto
            fps = exp.fps_efectivo(contexto.fps)
            densidad, flujo = self._calcular_indicadores(exp, fps)
            
            exp.resultados_colectivos["densidad_media"] = densidad
            exp.resultados_colectivos["flujo_medio"] = flujo
            

            comparacion[exp.nombre] = {
                "total_peatones": len(exp.trayectorias),
                "densidad_media": densidad,
                "flujo_medio": flujo
            }
            print(f"  {exp.nombre}: análisis colectivo (Densidad: {densidad:.3f} p/m², Flujo: {flujo:.3f} p/s)")

        return ResultadoAnalisis(experimentos=experimentos, comparacion=comparacion)

    def _calcular_indicadores(
        self, 
        experimento: Experimento, 
        fps: float
    ) -> tuple[float, float]:
        if not experimento.trayectorias:
            return 0.0, 0.0


        x_min = min(obs.x for t in experimento.trayectorias for obs in t.observaciones)
        x_max = max(obs.x for t in experimento.trayectorias for obs in t.observaciones)
        y_min = min(obs.y for t in experimento.trayectorias for obs in t.observaciones)
        y_max = max(obs.y for t in experimento.trayectorias for obs in t.observaciones)
        area = (x_max - x_min) * (y_max - y_min)
        

        frame_min = min(obs.frame for t in experimento.trayectorias for obs in t.observaciones)
        frame_max = max(obs.frame for t in experimento.trayectorias for obs in t.observaciones)
        tiempo_total = (frame_max - frame_min) / fps


        densidad = len(experimento.trayectorias) / area if area > 0 else 0.0
        flujo = len(experimento.trayectorias) / tiempo_total if tiempo_total > 0 else 0.0

        return densidad, flujo