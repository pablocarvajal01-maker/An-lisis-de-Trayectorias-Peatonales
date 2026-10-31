"""Pruebas de la etapa de carga usa archivos chiquitos en una carpeta temporal"""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from pipeline.contexto import ContextoPipeline
from stages import CargaExperimentos

CABECERA_M = "# <number> <frame> <x> [in m] <y> [in m] <z> [in m] <rot> [in rad] <id> <flag>"
CABECERA_CM = CABECERA_M.replace("[in m]", "[in cm]")


class TestCargaExperimentos(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _escribir(self, nombre, lineas, fin="\n"):
        ruta = self.dir / nombre
        ruta.write_bytes(fin.join(lineas).encode("utf-8") + fin.encode("utf-8"))
        return ruta

    def _cargar(self, ruta):
        contexto = ContextoPipeline(ruta_entrada=ruta, ruta_salida=self.dir / "salida")
        with contextlib.redirect_stdout(io.StringIO()) as salida:
            experimentos = CargaExperimentos().ejecutar(None, contexto)
        return experimentos, salida.getvalue()

    def test_carga_en_metros(self):
        self._escribir("a.txt", [CABECERA_M, "# comentario", "1\t100\t1.5\t2.5\t1.7\t0.1\t-1\t1"])
        (exp,), _ = self._cargar(self.dir / "a.txt")
        o = exp.observaciones[0]
        self.assertEqual(exp.nombre, "a")
        self.assertEqual((o.id_peaton, o.frame, o.flag), (1, 100, 1))
        self.assertAlmostEqual(o.x, 1.5)
        self.assertAlmostEqual(o.y, 2.5)

    def test_convierte_centimetros_a_metros(self):
        self._escribir("b.txt", [CABECERA_CM, "1\t100\t150.0\t250.0\t170.0\t0.1\t-1\t1"])
        (exp,), _ = self._cargar(self.dir / "b.txt")
        o = exp.observaciones[0]
        self.assertAlmostEqual(o.x, 1.5)
        self.assertAlmostEqual(o.y, 2.5)
        self.assertAlmostEqual(o.z, 1.7)

    def test_id_peaton_sale_de_la_columna_1_no_de_id(self):
        self._escribir("c.txt", [CABECERA_M, "7\t1\t0\t0\t1.7\t0\t-1\t1", "8\t1\t1\t1\t1.7\t0\t-1\t1"])
        (exp,), _ = self._cargar(self.dir / "c.txt")
        self.assertEqual([o.id_peaton for o in exp.observaciones], [7, 8])

    def test_acepta_finales_de_linea_windows(self):
        self._escribir("d.txt", [CABECERA_M, "1\t1\t0.5\t0.5\t1.7\t0\t-1\t1"], fin="\r\n")
        (exp,), _ = self._cargar(self.dir / "d.txt")
        self.assertEqual(len(exp.observaciones), 1)

    def test_salta_lineas_malas_y_avisa(self):
        self._escribir("e.txt", [
            CABECERA_M,
            "1\t1\t0.5\t0.5\t1.7\t0\t-1\t1",
            "esto no es una linea",
            "2\t2\tabc\t0.5\t1.7\t0\t-1\t1",
        ])
        (exp,), salida = self._cargar(self.dir / "e.txt")
        self.assertEqual(len(exp.observaciones), 1)
        self.assertIn("2 líneas malformadas", salida)

    def test_cabecera_con_columnas_raras_falla(self):
        self._escribir("f.txt", ["# <number> <frame> <x> [in m] <y> [in m]", "1\t1\t0\t0"])
        with self.assertRaises(ValueError):
            self._cargar(self.dir / "f.txt")

    def test_carpeta_carga_todos_los_txt_ordenados(self):
        self._escribir("z.txt", [CABECERA_M, "1\t1\t0\t0\t1.7\t0\t-1\t1"])
        self._escribir("a.txt", [CABECERA_M, "1\t1\t0\t0\t1.7\t0\t-1\t1"])
        self._escribir("notas.md", ["no soy un txt"])
        experimentos, _ = self._cargar(self.dir)
        self.assertEqual([e.nombre for e in experimentos], ["a", "z"])

    def test_ruta_que_no_existe_o_vacia_falla(self):
        with self.assertRaises(FileNotFoundError):
            self._cargar(self.dir / "no_existe")
        with self.assertRaises(FileNotFoundError):
            self._cargar(self.dir)


if __name__ == "__main__":
    unittest.main()