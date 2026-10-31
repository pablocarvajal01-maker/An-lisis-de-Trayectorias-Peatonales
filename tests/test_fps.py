"""Pruebas de la frecuencia de muestreo; valor por defecto es 16 fps"""

import contextlib
import io
import unittest

from main import crear_parser
from models.experimento import Experimento
from models.observacion import Observacion
from models.trayectoria import Trayectoria
from pipeline.contexto import FPS_EXPERIMENTOS, ContextoPipeline
from stages.individual import AnalisisIndividual


def peaton_a_paso_fijo(paso_m, n=17):
    """peaton que avanza 'paso_m' metros por frame sobre el eje y"""
    return Trayectoria(1, [Observacion(1, f, 0.0, f * paso_m, 1.7) for f in range(n)])


class TestFps(unittest.TestCase):
    def test_el_contexto_usa_16_fps_por_defecto(self):
        self.assertEqual(FPS_EXPERIMENTOS, 16.0)
        self.assertEqual(ContextoPipeline(None, None).fps, 16.0)

    def test_el_parser_usa_16_fps_por_defecto_y_permite_cambiarlo(self):
        self.assertEqual(crear_parser().parse_args([]).fps, 16.0)
        self.assertEqual(crear_parser().parse_args(["--fps", "25"]).fps, 25.0)

    def test_individual_usa_el_fps_del_contexto(self):
        exp = Experimento("prueba", trayectorias=[peaton_a_paso_fijo(0.0625)])
        with contextlib.redirect_stdout(io.StringIO()):
            AnalisisIndividual().ejecutar([exp], ContextoPipeline(None, None))
        r = exp.resultados_individuales[1]
        self.assertAlmostEqual(r["velocidad_media"], 1.0, places=6)
        self.assertAlmostEqual(r["tiempo_total"], 1.0, places=6)


if __name__ == "__main__":
    unittest.main()