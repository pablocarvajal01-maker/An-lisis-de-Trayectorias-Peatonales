"""Pruebas de la validacion, puntos fuera de rango y saltos imposibles"""

import contextlib
import io
import unittest

from models.experimento import Experimento
from models.observacion import Observacion
from pipeline.contexto import ContextoPipeline
from stages.validacion import ValidacionExperimentos

CONTEXTO = ContextoPipeline(None, None, 16.0)


def validar(observaciones, **opciones):
    exp = Experimento("prueba", observaciones=observaciones)
    with contextlib.redirect_stdout(io.StringIO()):
        (resultado,) = ValidacionExperimentos(**opciones).ejecutar([exp], CONTEXTO)
    return resultado.observaciones


def camina(id_peaton, n=10, y0=0.0, paso=0.0625):
    """peaton que avanza paso m por frame, con el paso por defecto va a 1 m/s a 16 fps"""
    return [Observacion(id_peaton, f, 0.0, y0 + f * paso, 1.7) for f in range(n)]


class TestValidacion(unittest.TestCase):
    def test_deja_pasar_datos_normales(self):
        self.assertEqual(len(validar(camina(1))), 10)

    def test_elimina_puntos_fuera_de_rango(self):
        obs = camina(1) + [Observacion(1, 20, 0.0, -1260.0, 1.7), Observacion(1, 21, 0.0, 428.0, 1.7)]
        resultado = validar(obs)
        self.assertEqual(len(resultado), 10)
        self.assertTrue(all(abs(o.y) < 15 for o in resultado))

    def test_elimina_x_fuera_del_corredor(self):
        obs = camina(1) + [Observacion(1, 20, 9.0, 1.0, 1.7)]
        self.assertEqual(len(validar(obs)), 10)

    def test_elimina_salto_imposible_pero_conserva_los_vecinos(self):
        obs = camina(1)
        obs[5] = Observacion(1, 5, 3.0, obs[5].y, 1.7)
        resultado = validar(obs)
        self.assertEqual([o.frame for o in resultado], [0, 1, 2, 3, 4, 6, 7, 8, 9])

    def test_hueco_de_frames_no_cuenta_como_salto(self):
        # 1 m en 16 frames es 1 m/s aunque falten frames en el medio
        obs = [Observacion(1, 0, 0.0, 0.0, 1.7), Observacion(1, 16, 0.0, 1.0, 1.7)]
        self.assertEqual(len(validar(obs)), 2)

    def test_descarta_trayectorias_demasiado_cortas(self):
        obs = camina(1) + camina(2, n=1)
        self.assertEqual({o.id_peaton for o in validar(obs)}, {1})

    def test_frames_repetidos_se_quedan_con_el_primero(self):
        obs = camina(1, n=3) + [Observacion(1, 2, 0.0, 0.5, 1.7)]
        self.assertEqual([o.frame for o in validar(obs)], [0, 1, 2])

    def test_los_saltos_usan_el_fps_del_experimento(self):
        obs = [Observacion(1, f, 0.0, f * 0.18, 1.7) for f in range(10)]
        for fps, esperado in ((None, 10), (25.0, 10), (32.0, 1)):
            exp = Experimento("a", observaciones=list(obs), fps=fps)
            with contextlib.redirect_stdout(io.StringIO()):
                (resultado,) = ValidacionExperimentos(min_observaciones=1).ejecutar([exp], CONTEXTO)
            self.assertEqual(len(resultado.observaciones), esperado, fps)

    def test_el_rango_por_defecto_deja_los_bordes_del_corredor(self):
        # el corredor mide 5 m de ancho, un peaton pegado a la pared esta a 2.4 m
        obs = [Observacion(1, f, 2.4, f * 0.0625, 1.7) for f in range(10)] + [Observacion(1, 10, 9.0, 0.6, 1.7)]
        self.assertEqual(len(validar(obs)), 10)

    def test_solo_flag_1(self):
        obs = camina(1) + [Observacion(1, 10, 0.0, 0.7, 1.7, flag=12)]
        self.assertEqual(len(validar(obs, solo_flag_1=True)), 10)
        self.assertEqual(len(validar(obs)), 11)


if __name__ == "__main__":
    unittest.main()