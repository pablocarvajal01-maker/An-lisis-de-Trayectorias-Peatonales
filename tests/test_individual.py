"""Pruebas de las detenciones del analisis individual"""

import contextlib
import io
import unittest

from models.experimento import Experimento
from models.observacion import Observacion
from models.trayectoria import Trayectoria
from pipeline.contexto import ContextoPipeline
from stages.individual import AnalisisIndividual

FPS = 16.0


def trayectoria(pasos):
    """un peaton sobre el eje y cada paso son los m que avanza en un frame"""
    y, obs = 0.0, [Observacion(1, 0, 0.0, 0.0, 1.7)]
    for i, paso in enumerate(pasos, start=1):
        y += paso
        obs.append(Observacion(1, i, 0.0, y, 1.7))
    return Trayectoria(1, obs)


def analizar(tray, **kwargs):
    exp = Experimento("a", observaciones=tray.observaciones, trayectorias=[tray])
    with contextlib.redirect_stdout(io.StringIO()):
        AnalisisIndividual(**kwargs).ejecutar([exp], ContextoPipeline(None, None, FPS))
    return exp.resultados_individuales[1]


class TestDetenciones(unittest.TestCase):
    def test_sin_detenciones_si_camina_siempre(self):
        r = analizar(trayectoria([0.06] * 40))
        self.assertEqual(r["n_detenciones"], 0)
        self.assertEqual(r["tiempo_detenido"], 0.0)
        self.assertEqual(r["pct_tiempo_detenido"], 0.0)

    def test_una_detencion_larga_se_cuenta(self):
        # 16 frames caminando, 16 quieto, 16 caminando
        r = analizar(trayectoria([0.06] * 16 + [0.0] * 16 + [0.06] * 16))
        self.assertEqual(r["n_detenciones"], 1)
        self.assertAlmostEqual(r["tiempo_detenido"], 1.0, places=6)
        self.assertAlmostEqual(r["pct_tiempo_detenido"], 100.0 / 3, places=6)

    def test_una_pausa_corta_no_cuenta(self):
        r = analizar(trayectoria([0.06] * 20 + [0.0] * 3 + [0.06] * 20))
        self.assertEqual(r["n_detenciones"], 0)
        self.assertEqual(r["tiempo_detenido"], 0.0)

    def test_dos_detenciones_separadas(self):
        pasos = [0.0] * 10 + [0.06] * 10 + [0.0] * 10 + [0.06] * 10
        r = analizar(trayectoria(pasos))
        self.assertEqual(r["n_detenciones"], 2)

    def test_la_duracion_minima_se_puede_cambiar(self):
        tray = trayectoria([0.06] * 20 + [0.0] * 3 + [0.06] * 20)
        self.assertEqual(analizar(tray, duracion_minima=0.1)["n_detenciones"], 1)

    def test_los_frames_que_faltan_no_inflan_la_velocidad(self):
        obs = [Observacion(1, 0, 0.0, 0.0, 1.7), Observacion(1, 3, 0.0, 0.01, 1.7), Observacion(1, 20, 0.0, 0.02, 1.7)]
        r = analizar(Trayectoria(1, obs))
        self.assertEqual(r["n_detenciones"], 1)


if __name__ == "__main__":
    unittest.main()