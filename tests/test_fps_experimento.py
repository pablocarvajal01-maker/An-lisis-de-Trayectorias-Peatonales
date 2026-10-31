"""Pruebas de que cada etapa usa el fps del experimento y no uno global"""

import contextlib
import io
import unittest

from models.experimento import Experimento
from models.observacion import Observacion
from models.trayectoria import Trayectoria
from pipeline.contexto import ContextoPipeline
from stages.colectivo import ComparacionExperimentos
from stages.individual import AnalisisIndividual


def experimento(nombre, fps=None, n=26, paso=0.04):
    """un peaton que avanza paso m por frame sobre el eje y"""
    obs = [Observacion(1, f, 0.0, f * paso, 1.7) for f in range(n)]
    return Experimento(nombre, observaciones=obs, trayectorias=[Trayectoria(1, obs)], fps=fps)


def callado(etapa, experimentos):
    with contextlib.redirect_stdout(io.StringIO()):
        etapa.ejecutar(experimentos, ContextoPipeline(None, None))


class TestFpsPorExperimento(unittest.TestCase):
    def test_individual_usa_el_fps_de_cada_experimento(self):
        # 0.04 m por frame son 1 m/s a 25 fps y 0.64 m/s a 16 fps
        a = experimento("a", fps=25.0)
        b = experimento("b")
        callado(AnalisisIndividual(), [a, b])
        self.assertAlmostEqual(a.resultados_individuales[1]["velocidad_media"], 1.0, places=6)
        self.assertAlmostEqual(b.resultados_individuales[1]["velocidad_media"], 0.64, places=6)

    def test_el_tiempo_total_sigue_el_fps_del_experimento(self):
        a = experimento("a", fps=25.0)
        callado(AnalisisIndividual(), [a])
        self.assertAlmostEqual(a.resultados_individuales[1]["tiempo_total"], 1.0, places=6)

    def test_colectivo_usa_el_fps_del_experimento(self):
        rapido = experimento("rapido", fps=32.0)
        normal = experimento("normal")
        callado(ComparacionExperimentos(), [rapido, normal])
        # el doble de fps, la mitad de tiempo observado, el doble de flujo
        self.assertAlmostEqual(
            rapido.resultados_colectivos["flujo_medio"],
            2 * normal.resultados_colectivos["flujo_medio"],
            places=6,
        )


if __name__ == "__main__":
    unittest.main()