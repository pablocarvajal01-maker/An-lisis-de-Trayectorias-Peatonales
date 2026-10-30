"""Pruebas de los calculos se corren con unittest"""

import unittest

from models.observacion import Observacion
from models.trayectoria import Trayectoria

FPS = 16.0


def crear(puntos):
    """puntos = [(frame, x, y), ...] -> Trayectoria del peaton 1"""
    return Trayectoria(1, [Observacion(1, f, x, y, 1.7) for f, x, y in puntos])


class TestTrayectoria(unittest.TestCase):
    def setUp(self):
        self.t = crear([(100, 1.22, 0.81), (101, 1.27, 0.82), (102, 1.33, 0.84)])

    def test_distancia_total(self):
        self.assertAlmostEqual(self.t.calcular_distancia_total(), 0.114236, places=5)

    def test_desplazamiento(self):
        self.assertAlmostEqual(self.t.calcular_desplazamiento(), 0.114018, places=5)

    def test_eficiencia_casi_directa(self):
        self.assertAlmostEqual(self.t.calcular_eficiencia(), 0.99809, places=4)

    def test_tiempo_y_velocidades(self):
        self.assertAlmostEqual(self.t.calcular_tiempo_total(FPS), 0.125)
        self.assertAlmostEqual(self.t.calcular_velocidad_media(FPS), 0.91389, places=4)
        self.assertAlmostEqual(self.t.calcular_velocidad_maxima(FPS), 1.01194, places=4)

    def test_posiciones_inicial_y_final(self):
        self.assertEqual(self.t.posicion_inicial, (1.22, 0.81))
        self.assertEqual(self.t.posicion_final, (1.33, 0.84))

    def test_ida_y_vuelta_tiene_eficiencia_cero(self):
        t = crear([(0, 0.0, 0.0), (1, 1.0, 0.0), (2, 0.0, 0.0)])
        self.assertAlmostEqual(t.calcular_eficiencia(), 0.0)

    def test_peaton_quieto_no_tiene_eficiencia(self):
        t = crear([(0, 2.0, 2.0), (1, 2.0, 2.0)])
        self.assertIsNone(t.calcular_eficiencia())
        self.assertEqual(t.calcular_velocidad_media(FPS), 0.0)

    def test_un_solo_punto_no_se_cae(self):
        t = crear([(5, 1.0, 1.0)])
        self.assertEqual(t.calcular_distancia_total(), 0.0)
        self.assertEqual(t.calcular_desplazamiento(), 0.0)
        self.assertEqual(t.calcular_velocidad_maxima(FPS), 0.0)

    def test_hueco_de_frames_usa_el_dt_real(self):
        # 0.4 m en 4 frames a 16 fps = 0.25 s -> 1.6 m/s
        t = crear([(100, 0.0, 0.0), (104, 0.4, 0.0)])
        self.assertAlmostEqual(t.velocidades_tramos(FPS)[0], 1.6)

    def test_frames_repetidos_avisan(self):
        t = crear([(100, 0.0, 0.0), (100, 0.1, 0.0)])
        with self.assertRaises(ValueError):
            t.velocidades_tramos(FPS)

    def test_fps_invalido_avisa(self):
        with self.assertRaises(ValueError):
            self.t.calcular_velocidad_media(0)
        with self.assertRaises(ValueError):
            self.t.calcular_velocidad_media(None)


if __name__ == "__main__":
    unittest.main()