"""Etapa de análisis colectivo y comparación de experimentos."""

from models.corredor import Corredor
from models.experimento import Experimento
from models.resultado_analisis import ResultadoAnalisis
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline


class ComparacionExperimentos(EtapaPipeline[list[Experimento], ResultadoAnalisis]):

    def __init__(self, corredor: Corredor | None = None) -> None:
        # misma geometria que el analisis espacial (ver models/corredor.py)
        self.corredor = corredor or Corredor()

    def ejecutar(
        self,
        experimentos: list[Experimento],
        contexto: ContextoPipeline,
    ) -> ResultadoAnalisis:

        comparacion = {}

        for exp in experimentos:
            # cada archivo puede traer su fps, si no se usa el del contexto
            fps = exp.fps_efectivo(contexto.fps)
            densidad, flujo, serie = self._calcular_indicadores(exp, fps)
            # densidad maxima: el momento mas apretado del experimento
            densidad_maxima = max((s["densidad"] for s in serie), default=0.0)
            
            exp.resultados_colectivos["densidad_media"] = densidad
            exp.resultados_colectivos["densidad_maxima"] = densidad_maxima
            exp.resultados_colectivos["serie_densidad"] = serie
            exp.resultados_colectivos["flujo_medio"] = flujo
            

            comparacion[exp.nombre] = {
                "total_peatones": len(exp.trayectorias),
                "densidad_media": densidad,
                "densidad_maxima": densidad_maxima,
                "flujo_medio": flujo
            }
            print(f"  {exp.nombre}: análisis colectivo (Densidad: {densidad:.3f} p/m², máx {densidad_maxima:.3f} p/m², Flujo: {flujo:.3f} p/s)")

        return ResultadoAnalisis(experimentos=experimentos, comparacion=comparacion)

    def _calcular_indicadores(
        self, 
        experimento: Experimento, 
        fps: float
    ) -> tuple[float, float, list[dict[str, float]]]:
        if not experimento.trayectorias:
            return 0.0, 0.0, []

        # la densidad es = personas presentes / area de medicion,
        # calculada segundo a segundo. la media ocupa los segundos con gente
        # en el area, pero al principio y al final del experimento el corredor esta
        # vacio y denuevo se ensuciaria el promedio si tomamos en cuenta esos ceros
        serie = self._calcular_serie_densidad(experimento, fps)
        con_gente = [s["densidad"] for s in serie if s["densidad"] > 0]
        

        frame_min = min(obs.frame for t in experimento.trayectorias for obs in t.observaciones)
        frame_max = max(obs.frame for t in experimento.trayectorias for obs in t.observaciones)
        tiempo_total = (frame_max - frame_min) / fps


        densidad = sum(con_gente) / len(con_gente) if con_gente else 0.0
        flujo = len(experimento.trayectorias) / tiempo_total if tiempo_total > 0 else 0.0

        return densidad, flujo, serie

    def _calcular_serie_densidad(
        self,
        experimento: Experimento,
        fps: float
    ) -> list[dict[str, float]]:
        """densidad [p/m2] y velocidad media [m/s] dentro del area de medicion, segundo a segundo"""
        area = self.corredor.area_medicion
        cuadros = max(1, round(fps))  # frames que caben en 1 segundo
        frame_inicio = min(t.observaciones[0].frame for t in experimento.trayectorias)
        frame_fin = max(t.observaciones[-1].frame for t in experimento.trayectorias)

        # una sola pasada por los datos. para cada segundo se guarda:
        #  - cuantas observaciones cayeron dentro del area
        #  - por cada peaton, su primera y ultima observacion dentro del area
        observaciones_por_segundo = {}
        extremos = {}  # (segundo, id_peaton) -> [primera, ultima]
        for tray in experimento.trayectorias:
            for obs in filter(self.corredor.en_area_medicion, tray.observaciones):
                segundo = (obs.frame - frame_inicio) // cuadros
                observaciones_por_segundo[segundo] = observaciones_por_segundo.get(segundo, 0) + 1
                clave = (segundo, tray.id_peaton)
                if clave in extremos:
                    extremos[clave][1] = obs
                else:
                    extremos[clave] = [obs, obs]

        # velocidad de avance de cada peaton en ese segundo (mismo criterio que
        # en las zonas: cuanto avanzo en y / tiempo, para no sumar ruido).
        # solo se mide si estuvo al menos medio segundo en el area: con 1 o 2
        # frames, un error de pocos cm del tracking da velocidades absurdas
        velocidades_por_segundo = {}
        for (segundo, _), (primera, ultima) in extremos.items():
            if ultima.frame - primera.frame >= max(1, cuadros // 2):
                dt = (ultima.frame - primera.frame) / fps
                velocidades_por_segundo.setdefault(segundo, []).append(abs(ultima.y - primera.y) / dt)

        serie = []
        total_segundos = (frame_fin - frame_inicio) // cuadros + 1
        for segundo in range(total_segundos):
            # el ultimo segundo puede venir incompleto, por eso no se divide siempre por "cuadros"
            frames_en_segundo = min(cuadros, frame_fin - frame_inicio - segundo * cuadros + 1)
            # n medio = personas presentes en un frame tipico de ese segundo
            peatones_medios = observaciones_por_segundo.get(segundo, 0) / frames_en_segundo
            vels = velocidades_por_segundo.get(segundo, [])
            serie.append({
                "tiempo": segundo * cuadros / fps,
                "peatones": peatones_medios,
                "densidad": peatones_medios / area,
                "velocidad_media": sum(vels) / len(vels) if vels else 0.0,
            })
        return serie
