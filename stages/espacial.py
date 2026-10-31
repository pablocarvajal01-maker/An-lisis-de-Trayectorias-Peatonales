"""metricas locales por zona del corredor

idea: se corta el corredor en tramos a lo largo de y (la direccion en que
camina la gente) y para cada tramo se mide:
  - cuantos peatones lo cruzan completo
  - su velocidad media de avance dentro del tramo [m/s]
  - cuanto tardan en cruzarlo [s]

si una zona tiene velocidad claramente menor que las demas, ahi hay un
posible cuello de botella
"""

import numpy as np

from models.corredor import Corredor, Zona, sentido_de_avance
from models.experimento import Experimento
from models.trayectoria import Trayectoria
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline


class AnalisisEspacial(EtapaPipeline[list[Experimento], list[Experimento]]):
    """divide el corredor en zonas y calcula metricas locales en cada una"""

    def __init__(
        self,
        corredor: Corredor | None = None,
        num_zonas: int = 4,
        fps_por_defecto: float = 25.0,
    ) -> None:
        self.corredor = corredor or Corredor()
        self.num_zonas = num_zonas
        self.fps_por_defecto = fps_por_defecto

    def ejecutar(
        self,
        experimentos: list[Experimento],
        contexto: ContextoPipeline,
    ) -> list[Experimento]:
        """calcula las metricas por zona de cada experimento"""
        fps = contexto.fps if contexto.fps is not None else self.fps_por_defecto

        for exp in experimentos:
            # el sentido cambia entre experimentos, asi que se detecta en cada uno
            sentido = sentido_de_avance(exp.trayectorias)
            zonas = self.corredor.dividir_en_zonas(self.num_zonas, sentido)
            resultados = [self._analizar_zona(zona, exp.trayectorias, fps) for zona in zonas]
            exp.resultados_colectivos["sentido_avance"] = sentido
            exp.resultados_colectivos["zonas"] = resultados

            flecha = "y+" if sentido > 0 else "y-"
            print(f"  {exp.nombre}: análisis espacial ({len(zonas)} zonas, avance hacia {flecha})")
            for r in resultados:
                print(
                    f"    Zona {r['zona']} [y {r['y_entrada']:+.1f} -> {r['y_salida']:+.1f} m]: "
                    f"{r['peatones']:4d} peatones | v = {r['velocidad_media']:.2f} m/s | "
                    f"cruce = {r['tiempo_medio_cruce']:.2f} s (mediana {r['tiempo_mediano_cruce']:.2f} s)"
                )
        return experimentos

    def _analizar_zona(
        self,
        zona: Zona,
        trayectorias: list[Trayectoria],
        fps: float,
    ) -> dict[str, float]:
        """junta los cruces de todos los peatones por una zona y los resume"""
        # filter: solo los que atraviesan la zona completa
        que_cruzan = filter(zona.es_cruzada_por, trayectorias)
        # map: cada cruce -> (tiempo, velocidad), none si no alcanzo a medirse
        cruces = [c for c in map(lambda t: self._medir_cruce(zona, t, fps), que_cruzan) if c]

        if not cruces:
            # nadie cruzo la zona: se devuelven ceros para no dividir por cero
            return {
                "zona": zona.numero, "y_entrada": zona.y_entrada, "y_salida": zona.y_salida,
                "peatones": 0, "velocidad_media": 0.0, "velocidad_desviacion": 0.0,
                "tiempo_medio_cruce": 0.0, "tiempo_mediano_cruce": 0.0,
            }

        tiempos = np.array([tiempo for tiempo, _ in cruces])
        velocidades = np.array([velocidad for _, velocidad in cruces])
        return {
            "zona": zona.numero,
            "y_entrada": zona.y_entrada,
            "y_salida": zona.y_salida,
            "peatones": len(cruces),
            "velocidad_media": float(np.mean(velocidades)),
            "velocidad_desviacion": float(np.std(velocidades)),
            "tiempo_medio_cruce": float(np.mean(tiempos)),
            # la mediana no se deja arrastrar por los pocos que quedan atrapados
            # mucho rato en un taco (en el exp. 09 la media sube mucho por ellos)
            "tiempo_mediano_cruce": float(np.median(tiempos)),
        }

    @staticmethod
    def _medir_cruce(
        zona: Zona,
        trayectoria: Trayectoria,
        fps: float,
    ) -> tuple[float, float] | None:
        """tiempo [s] y velocidad media de avance [m/s] de un peaton en la zona"""
        dentro = [obs for obs in trayectoria.observaciones if zona.contiene(obs)]
        if len(dentro) < 2:
            return None
        # se reutiliza trayectoria con solo el pedazo dentro de la zona, asi el
        # tiempo se calcula con el mismo codigo del analisis individual
        tramo = Trayectoria(trayectoria.id_peaton, dentro)
        tiempo = tramo.calcular_tiempo_total(fps)
        if tiempo <= 0:
            return None
        # velocidad en la direccion de avance: cuanto avanzo en y / tiempo.
        # no se usa la distancia recorrida porque, cuando alguien esta casi
        # detenido, el ruido del tracking (la cabeza "tiembla" unos mm por frame)
        # suma metros falsos y la velocidad saldria inflada
        avance = abs(dentro[-1].y - dentro[0].y)
        return tiempo, avance / tiempo
