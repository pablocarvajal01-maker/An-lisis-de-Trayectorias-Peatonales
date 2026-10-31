"""pruebas del analisis por zonas (se corren con unittest)"""

import unittest

from models.corredor import Corredor, sentido_de_avance
from models.experimento import Experimento
from models.observacion import Observacion
from models.trayectoria import Trayectoria
from pipeline.contexto import ContextoPipeline
from stages.espacial import AnalisisEspacial

FPS = 10.0


def peaton_recto(id_peaton, y_inicio, y_fin, paso=0.1):
    """peaton que camina en linea recta de y_inicio a y_fin, 'paso' metros por frame"""
    n = round(abs(y_fin - y_inicio) / paso)
    signo = 1 if y_fin > y_inicio else -1
    return Trayectoria(
        id_peaton,
        [Observacion(id_peaton, f, 0.0, y_inicio + signo * f * paso, 1.7) for f in range(n + 1)],
    )


class TestCorredor(unittest.TestCase):
    def test_zonas_hacia_y_negativo(self):
        zonas = Corredor(y_min=-4.0, y_max=4.0).dividir_en_zonas(4, sentido=-1)
        self.assertEqual([(z.y_entrada, z.y_salida) for z in zonas],
                         [(4.0, 2.0), (2.0, 0.0), (0.0, -2.0), (-2.0, -4.0)])

    def test_zonas_hacia_y_positivo(self):
        zonas = Corredor(y_min=-4.0, y_max=4.0).dividir_en_zonas(4, sentido=1)
        self.assertEqual([(z.y_entrada, z.y_salida) for z in zonas],
                         [(-4.0, -2.0), (-2.0, 0.0), (0.0, 2.0), (2.0, 4.0)])

    def test_sentido_de_avance(self):
        self.assertEqual(sentido_de_avance([peaton_recto(1, 5.0, -5.0)]), -1)
        self.assertEqual(sentido_de_avance([peaton_recto(1, -5.0, 5.0)]), 1)

    def test_solo_cuenta_quien_cruza_completo(self):
        zona = Corredor().dividir_en_zonas(4, sentido=-1)[0]  # y de 4 a 2
        self.assertTrue(zona.es_cruzada_por(peaton_recto(1, 5.0, 1.0)))
        # aparece a mitad de zona -> no cuenta
        self.assertFalse(zona.es_cruzada_por(peaton_recto(2, 3.0, 1.0)))


class TestAnalisisEspacial(unittest.TestCase):
    def test_velocidad_y_tiempo_por_zona(self):
        # 0.1 m por frame a 10 fps = 1 m/s; cada zona mide 2 m
        for inicio, fin in [(5.0, -5.0), (-5.0, 5.0)]:
            exp = Experimento("prueba", trayectorias=[peaton_recto(1, inicio, fin)])
            AnalisisEspacial(num_zonas=4).ejecutar([exp], ContextoPipeline(None, None, FPS))
            for zona in exp.resultados_colectivos["zonas"]:
                self.assertEqual(zona["peatones"], 1)
                self.assertAlmostEqual(zona["velocidad_media"], 1.0, places=6)
                # entre la primera y la ultima observacion dentro de 2 m hay ~1.9 s
                self.assertAlmostEqual(zona["tiempo_medio_cruce"], 1.9, places=6)


if __name__ == "__main__":
    unittest.main()
