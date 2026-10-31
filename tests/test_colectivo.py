"""pruebas de la densidad en el area de medicion"""

import unittest

from models.corredor import Corredor
from models.experimento import Experimento
from models.observacion import Observacion
from models.trayectoria import Trayectoria
from pipeline.contexto import ContextoPipeline
from stages.colectivo import ComparacionExperimentos

FPS = 10.0


def peaton_quieto(id_peaton, x, y, frames):
    """peaton parado en (x, y) durante 'frames' frames"""
    return Trayectoria(id_peaton, [Observacion(id_peaton, f, x, y, 1.7) for f in range(frames)])


def peaton_caminando(id_peaton, y_inicio, frames, paso=0.1):
    """peaton que avanza hacia y positivo 'paso' metros por frame (1 m/s a 10 fps)"""
    return Trayectoria(
        id_peaton,
        [Observacion(id_peaton, f, 0.0, y_inicio + f * paso, 1.7) for f in range(frames)],
    )


class TestAreaMedicion(unittest.TestCase):
    def test_area_por_defecto(self):
        # 5 m de ancho por 4 m de largo
        self.assertAlmostEqual(Corredor().area_medicion, 20.0)

    def test_en_area_medicion(self):
        corredor = Corredor()
        self.assertTrue(corredor.en_area_medicion(Observacion(1, 0, 0.0, 0.0, 1.7)))
        self.assertFalse(corredor.en_area_medicion(Observacion(1, 0, 0.0, 3.0, 1.7)))


class TestSerieDensidad(unittest.TestCase):
    def ejecutar(self, trayectorias):
        exp = Experimento("prueba", trayectorias=trayectorias)
        ComparacionExperimentos().ejecutar([exp], ContextoPipeline(None, None, FPS))
        return exp.resultados_colectivos

    def test_dos_personas_quietas(self):
        # 2 personas dentro del area durante 2 s -> 2 / 20 m2 = 0.1 p/m2 cada segundo
        resultados = self.ejecutar([peaton_quieto(1, 0.0, 0.0, 20), peaton_quieto(2, 1.0, 1.0, 20)])
        self.assertEqual(len(resultados["serie_densidad"]), 2)
        for segundo in resultados["serie_densidad"]:
            self.assertAlmostEqual(segundo["densidad"], 0.1)
            self.assertAlmostEqual(segundo["velocidad_media"], 0.0)
        self.assertAlmostEqual(resultados["densidad_media"], 0.1)

    def test_personas_fuera_del_area_no_cuentan(self):
        resultados = self.ejecutar([peaton_quieto(1, 0.0, 0.0, 20), peaton_quieto(2, 0.0, 3.0, 20)])
        self.assertAlmostEqual(resultados["densidad_maxima"], 0.05)

    def test_velocidad_dentro_del_area(self):
        # camina de y = -2 a y = 1.9 a 1 m/s: todos los segundos con velocidad 1
        resultados = self.ejecutar([peaton_caminando(1, -2.0, 40)])
        for segundo in resultados["serie_densidad"]:
            self.assertAlmostEqual(segundo["velocidad_media"], 1.0)



class TestFlujo(unittest.TestCase):
    def test_instante_de_cruce_interpolado(self):
        # va de y = -0.05 (frame 0) a y = 0.05 (frame 1): toca y = 0 a mitad de camino
        tray = Trayectoria(1, [Observacion(1, 0, 0.0, -0.05, 1.7), Observacion(1, 1, 0.0, 0.05, 1.7)])
        exp = Experimento("prueba", trayectorias=[tray])
        self.assertAlmostEqual(ComparacionExperimentos()._calcular_cruces(exp, FPS)[0], 0.05)

    def test_un_peaton_que_tiembla_en_la_linea_cuenta_una_vez(self):
        ys = [-0.1, 0.01, -0.01, 0.01, 0.1]
        tray = Trayectoria(1, [Observacion(1, f, 0.0, y, 1.7) for f, y in enumerate(ys)])
        exp = Experimento("prueba", trayectorias=[tray])
        self.assertEqual(len(ComparacionExperimentos()._calcular_cruces(exp, FPS)), 1)

    def test_flujo_constante(self):
        # 11 peatones a 1 m/s, uno cada 2 s: cruzan y = 0 cada 2 s -> 0.5 p/s
        trayectorias = [peaton_caminando(i, -1.0, 21) for i in range(11)]
        for i, tray in enumerate(trayectorias):
            tray.observaciones = [
                Observacion(i, o.frame + 20 * i, o.x, o.y, o.z) for o in tray.observaciones
            ]
        exp = Experimento("prueba", trayectorias=trayectorias)
        ComparacionExperimentos().ejecutar([exp], ContextoPipeline(None, None, FPS))
        self.assertAlmostEqual(exp.resultados_colectivos["flujo_medio"], 0.5)
        # flujo especifico = 0.5 p/s / 5 m de ancho
        self.assertAlmostEqual(exp.resultados_colectivos["flujo_especifico"], 0.1)



class TestComparacion(unittest.TestCase):
    def test_meseta_sin_llenado_ni_vaciado(self):
        # 0 -> sube -> meseta de 2.0 -> baja -> 0
        densidades = [0.0, 0.5, 2.0, 2.0, 2.2, 1.8, 2.0, 0.4, 0.0]
        serie = [{"densidad": d, "velocidad_media": 0.5} for d in densidades]
        densidad, velocidad = ComparacionExperimentos._resumir_estado_estacionario(serie)
        self.assertEqual([s["estacionario"] for s in serie], [0, 0, 1, 1, 1, 1, 1, 0, 0])
        self.assertAlmostEqual(densidad, 2.0)
        self.assertAlmostEqual(velocidad, 0.5)

    def test_promedios_individuales(self):
        exp = Experimento("prueba", trayectorias=[peaton_quieto(1, 0.0, 0.0, 20)])
        exp.resultados_individuales = {
            1: {"velocidad_media": 1.0, "distancia_total": 10.0},
            2: {"velocidad_media": 0.5, "distancia_total": 14.0},
        }
        resultado = ComparacionExperimentos().ejecutar([exp], ContextoPipeline(None, None, FPS))
        fila = resultado.comparacion["prueba"]
        self.assertAlmostEqual(fila["velocidad_media"], 0.75)
        self.assertAlmostEqual(fila["distancia_media"], 12.0)
        # si ningun peaton tiene el indicador, da 0 en vez de caerse
        self.assertAlmostEqual(fila["tiempo_medio"], 0.0)


if __name__ == "__main__":
    unittest.main()
