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
            # flujo especifico: flujo por metro de ancho, sirve para comparar
            # con corredores de otro ancho y con la relacion j = densidad * velocidad
            flujo_especifico = flujo / self.corredor.ancho
            # meseta de la serie: el tramo sin llenado ni vaciado del corredor
            densidad_estacionaria, velocidad_estacionaria = self._resumir_estado_estacionario(serie)
            
            exp.resultados_colectivos["densidad_media"] = densidad
            exp.resultados_colectivos["densidad_maxima"] = densidad_maxima
            exp.resultados_colectivos["serie_densidad"] = serie
            exp.resultados_colectivos["flujo_medio"] = flujo
            exp.resultados_colectivos["flujo_especifico"] = flujo_especifico
            exp.resultados_colectivos["serie_flujo"] = self._calcular_serie_flujo(exp, fps)
            

            comparacion[exp.nombre] = {
                "total_peatones": len(exp.trayectorias),
                "densidad_media": densidad,
                "densidad_maxima": densidad_maxima,
                "flujo_medio": flujo,
                "flujo_especifico": flujo_especifico,
                "densidad_estacionaria": densidad_estacionaria,
                "velocidad_estacionaria": velocidad_estacionaria,
                # promedios de los indicadores individuales de todos los peatones
                "velocidad_media": self._promedio_individual(exp, "velocidad_media"),
                "distancia_media": self._promedio_individual(exp, "distancia_total"),
                "tiempo_medio": self._promedio_individual(exp, "tiempo_total"),
                "eficiencia_media": self._promedio_individual(exp, "eficiencia"),
                "pct_tiempo_detenido_medio": self._promedio_individual(exp, "pct_tiempo_detenido"),
            }
            print(f"  {exp.nombre}: análisis colectivo (Densidad: {densidad:.3f} p/m², máx {densidad_maxima:.3f} p/m², Flujo: {flujo:.3f} p/s, {flujo_especifico:.3f} p/(m·s))")
            c = comparacion[exp.nombre]
            print(
                f"    estacionario: {densidad_estacionaria:.2f} p/m² a {velocidad_estacionaria:.2f} m/s | "
                f"por peaton: v = {c['velocidad_media']:.2f} m/s, {c['distancia_media']:.1f} m, "
                f"{c['tiempo_medio']:.1f} s, detenido {c['pct_tiempo_detenido_medio']:.1f} %"
            )

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
        

        # flujo = peatones que cruzan la linea / tiempo. el tiempo va desde el
        # primer cruce hasta el ultimo, asi no cuentan los ratos con el corredor vacio
        cruces = self._calcular_cruces(experimento, fps)
        tiempo_cruzando = cruces[-1] - cruces[0] if len(cruces) > 1 else 0.0


        densidad = sum(con_gente) / len(con_gente) if con_gente else 0.0
        flujo = (len(cruces) - 1) / tiempo_cruzando if tiempo_cruzando > 0 else 0.0

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

    def _calcular_cruces(
        self,
        experimento: Experimento,
        fps: float
    ) -> list[float]:
        """instantes [s] en que cada peaton cruza la linea de flujo, ordenados"""
        linea = self.corredor.y_linea_flujo
        cruces = []
        for tray in experimento.trayectorias:
            for a, b in zip(tray.observaciones, tray.observaciones[1:]):
                # cruza si la linea queda entre las dos posiciones consecutivas
                if (a.y - linea) * (b.y - linea) <= 0 and a.y != b.y:
                    # interpolacion lineal: en que fraccion del paso a -> b toco la linea
                    fraccion = (linea - a.y) / (b.y - a.y)
                    cruces.append((a.frame + fraccion * (b.frame - a.frame)) / fps)
                    # solo el primer cruce: si alguien "tiembla" justo en la linea
                    # no se cuenta dos veces
                    break
        return sorted(cruces)

    def _calcular_serie_flujo(
        self,
        experimento: Experimento,
        fps: float,
        ventana: float = 10.0
    ) -> list[dict[str, float]]:
        """flujo [p/s] en ventanas de 'ventana' segundos

        se usan 10 s y no 1 s porque en un segundo pasan entre 0 y 8 personas
        y la serie sale demasiado saltona
        """
        cruces = self._calcular_cruces(experimento, fps)
        if not cruces:
            return []
        inicio = cruces[0]
        conteo = {}
        for t in cruces:
            indice = int((t - inicio) // ventana)
            conteo[indice] = conteo.get(indice, 0) + 1
        return [
            {"tiempo": inicio + i * ventana, "cruces": conteo.get(i, 0), "flujo": conteo.get(i, 0) / ventana}
            for i in range(max(conteo) + 1)
        ]

    @staticmethod
    def _resumir_estado_estacionario(
        serie: list[dict[str, float]],
        fraccion: float = 0.8
    ) -> tuple[float, float]:
        """marca los segundos de la meseta y devuelve su densidad y velocidad medias

        la meseta va desde el primer hasta el ultimo segundo en que la densidad
        llega al 80 % de la densidad tipica: el valor del medio (mediana) de los
        segundos con gente, que no se deja mover por los picos ni por los ratos vacios
        """
        con_gente = sorted(s["densidad"] for s in serie if s["densidad"] > 0)
        if not con_gente:
            return 0.0, 0.0
        umbral = fraccion * con_gente[len(con_gente) // 2]
        sobre_umbral = [i for i, s in enumerate(serie) if s["densidad"] >= umbral]
        inicio, fin = sobre_umbral[0], sobre_umbral[-1]
        for i, s in enumerate(serie):
            # 1 = meseta, 0 = llenado o vaciado; queda en densidad.csv para graficar
            s["estacionario"] = 1 if inicio <= i <= fin else 0
        meseta = serie[inicio:fin + 1]
        densidad = sum(s["densidad"] for s in meseta) / len(meseta)
        velocidad = sum(s["velocidad_media"] for s in meseta) / len(meseta)
        return densidad, velocidad

    @staticmethod
    def _promedio_individual(experimento: Experimento, clave: str) -> float:
        """promedio de un indicador individual entre todos los peatones del experimento"""
        valores = [ind[clave] for ind in experimento.resultados_individuales.values() if clave in ind]
        return sum(valores) / len(valores) if valores else 0.0
