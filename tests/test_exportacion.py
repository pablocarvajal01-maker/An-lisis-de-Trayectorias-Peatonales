"""Pruebas de la exportacion de resultados a csv"""

import contextlib
import csv
import io
import tempfile
import unittest
from pathlib import Path

from main import main
from models.experimento import Experimento
from models.resultado_analisis import ResultadoAnalisis
from pipeline.contexto import ContextoPipeline
from stages.exportacion import ExportacionResultados


def leer_csv(ruta):
    with open(ruta, encoding="utf-8", newline="") as archivo:
        return list(csv.DictReader(archivo))


def resultados_de_prueba():
    exp = Experimento("exp_a")
    exp.resultados_individuales = {
        2: {"tiempo_total": 4.0, "velocidad_media": 1.2},
        1: {"tiempo_total": 5.0, "velocidad_media": 0.9},
    }
    exp.resultados_colectivos = {
        "sentido_avance": -1,
        "zonas": [
            {"zona": 1, "peatones": 3, "velocidad_media": 1.1},
            {"zona": 2, "peatones": 2, "velocidad_media": 0.7},
        ],
        "serie_densidad": [{"tiempo": 0.0, "densidad": 0.1}, {"tiempo": 1.0, "densidad": 0.3}],
    }
    comparacion = {"exp_a": {"total_peatones": 2, "densidad_media": 0.2, "flujo_medio": 1.5}}
    return ResultadoAnalisis(experimentos=[exp], comparacion=comparacion)


class TestExportacion(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.salida = Path(self._tmp.name) / "a" / "results"
        self.addCleanup(self._tmp.cleanup)

    def _exportar(self, resultados):
        contexto = ContextoPipeline(ruta_entrada=Path("."), ruta_salida=self.salida)
        with contextlib.redirect_stdout(io.StringIO()):
            ExportacionResultados().ejecutar(resultados, contexto)

    def test_crea_la_carpeta_y_los_archivos(self):
        self._exportar(resultados_de_prueba())
        nombres = {p.name for p in self.salida.iterdir()}
        self.assertEqual(
            nombres,
            {"individual.csv", "zonas.csv", "densidad.csv", "resumen_experimentos.csv"},
        )

    def test_individual_tiene_una_fila_por_peaton_ordenada(self):
        self._exportar(resultados_de_prueba())
        filas = leer_csv(self.salida / "individual.csv")
        self.assertEqual([f["id_peaton"] for f in filas], ["1", "2"])
        self.assertEqual(filas[0]["experimento"], "exp_a")
        self.assertEqual(float(filas[0]["velocidad_media"]), 0.9)

    def test_zonas_trae_el_sentido_de_avance(self):
        self._exportar(resultados_de_prueba())
        filas = leer_csv(self.salida / "zonas.csv")
        self.assertEqual(len(filas), 2)
        self.assertEqual(filas[1]["sentido_avance"], "-1")
        self.assertEqual(filas[1]["peatones"], "2")

    def test_densidad_y_resumen(self):
        self._exportar(resultados_de_prueba())
        self.assertEqual(len(leer_csv(self.salida / "densidad.csv")), 2)
        (fila,) = leer_csv(self.salida / "resumen_experimentos.csv")
        self.assertEqual(fila["experimento"], "exp_a")
        self.assertEqual(float(fila["flujo_medio"]), 1.5)

    def test_un_experimento_sin_resultados_no_rompe(self):
        vacio = ResultadoAnalisis(experimentos=[Experimento("vacio")], comparacion={})
        self._exportar(vacio)
        self.assertEqual(leer_csv(self.salida / "individual.csv"), [])


class TestPipelineCompleto(unittest.TestCase):
    def test_main_genera_los_resultados(self):
        cabecera = "# <number> <frame> <x> [in m] <y> [in m] <z> [in m] <rot> [in rad] <id> <flag>"
        with tempfile.TemporaryDirectory() as tmp:
            entrada, salida = Path(tmp) / "data", Path(tmp) / "results"
            entrada.mkdir()
            lineas = [cabecera]
            for peaton in (1, 2, 3):
                for frame in range(0, 8 * 16 + 1):
                    y = 4.0 - frame / 16
                    # la primera columna es el numero del peaton
                    lineas.append(f"{peaton}\t{frame + peaton * 5}\t{0.1 * peaton:.2f}\t{y:.4f}\t1.7\t0.0\t{peaton}\t1")
            (entrada / "uni_corr_500_99.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                codigo = main(["--input", str(entrada), "--output", str(salida)])
            self.assertEqual(codigo, 0)
            self.assertEqual(len(leer_csv(salida / "individual.csv")), 3)
            self.assertEqual(len(leer_csv(salida / "zonas.csv")), 4)


if __name__ == "__main__":
    unittest.main()