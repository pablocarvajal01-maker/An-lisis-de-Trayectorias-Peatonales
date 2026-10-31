"""Pruebas de la carga del formato del 02 y del fps que declara comillas el archivo"""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from models.experimento import Experimento
from models.observacion import Observacion
from pipeline.contexto import ContextoPipeline
from stages import CargaExperimentos, ValidacionExperimentos

CABECERA_M = "# <number> <frame> <x> [in m] <y> [in m] <z> [in m] <rot> [in rad] <id> <flag>"
CABECERA_02 = ["# description: UNI_CORR_500_02", "# framerate: 25.00", "", "# PersID\tFrame\tX\tY\tZ"]


class TestFormatoSimple(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _cargar(self, nombre, lineas):
        ruta = self.dir / nombre
        ruta.write_bytes("\r\n".join(lineas).encode("utf-8") + b"\r\n")
        contexto = ContextoPipeline(ruta_entrada=ruta, ruta_salida=self.dir / "salida")
        with contextlib.redirect_stdout(io.StringIO()):
            (exp,) = CargaExperimentos().ejecutar(None, contexto)
        return exp

    def test_lee_el_formato_de_5_columnas(self):
        exp = self._cargar("b.txt", CABECERA_02 + ["1\t85\t4.6057\t1.7769\t1.7600", "1\t86\t4.5448\t1.7682\t1.7600"])
        self.assertEqual(len(exp.observaciones), 2)
        o = exp.observaciones[0]
        self.assertEqual((o.id_peaton, o.frame, o.flag), (1, 85, 1))
        self.assertAlmostEqual(o.x, 4.6057)
        self.assertAlmostEqual(o.y, 1.7769)

    def test_lee_el_framerate_de_la_cabecera(self):
        exp = self._cargar("b.txt", CABECERA_02 + ["1\t85\t4.6\t1.7\t1.7"])
        self.assertEqual(exp.fps, 25.0)

    def test_el_formato_normal_no_declara_fps(self):
        exp = self._cargar("a.txt", [CABECERA_M, "1\t100\t1.5\t2.5\t1.7\t0.1\t-1\t1"])
        self.assertIsNone(exp.fps)
        self.assertEqual(len(exp.observaciones), 1)

    def test_una_cabecera_desconocida_sigue_dando_error(self):
        ruta = self.dir / "c.txt"
        ruta.write_text("# cualquier cosa\n1 2 3\n", encoding="utf-8")
        contexto = ContextoPipeline(ruta_entrada=ruta, ruta_salida=self.dir / "salida")
        with self.assertRaises(ValueError):
            CargaExperimentos().ejecutar(None, contexto)

    def test_fps_efectivo(self):
        self.assertEqual(Experimento("a", fps=25.0).fps_efectivo(16.0), 25.0)
        self.assertEqual(Experimento("a").fps_efectivo(16.0), 16.0)

    def test_la_validacion_no_pierde_el_fps(self):
        obs = [Observacion(1, f, 0.0, f * 0.04, 1.7) for f in range(5)]
        exp = Experimento("a", observaciones=obs, fps=25.0)
        with contextlib.redirect_stdout(io.StringIO()):
            (validado,) = ValidacionExperimentos().ejecutar([exp], ContextoPipeline(None, None))
        self.assertEqual(validado.fps, 25.0)


if __name__ == "__main__":
    unittest.main()