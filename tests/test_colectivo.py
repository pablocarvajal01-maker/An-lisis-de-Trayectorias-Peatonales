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


if __name__ == "__main__":
    unittest.main()
