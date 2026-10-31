"""Etapa de exportación de resultados."""

import csv
from pathlib import Path

from models.experimento import Experimento
from models.resultado_analisis import ResultadoAnalisis
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline

# una fila es un dict columna -> valor, cada tabla es una lista de filas
Fila = dict[str, object]


class ExportacionResultados(EtapaPipeline[ResultadoAnalisis, None]):
    """Exporta los resultados de los experimentos y su comparación."""

    def ejecutar(
        self,
        resultados: ResultadoAnalisis,
        contexto: ContextoPipeline,
    ) -> None:
        """Guarda los resultados en la ruta de salida configurada."""
        self._exportar(resultados, contexto.ruta_salida)

    def _exportar(self, resultados: ResultadoAnalisis, ruta_salida: Path) -> None:
        """Exporta los resultados a la ruta indicada."""
        ruta_salida.mkdir(parents=True, exist_ok=True)
        experimentos = resultados.experimentos

        tablas = {
            "individual.csv": self._filas_individuales(experimentos),
            "zonas.csv": self._filas_zonas(experimentos),
            "densidad.csv": self._filas_densidad(experimentos),
            "resumen_experimentos.csv": self._filas_resumen(resultados),
        }
        for nombre, filas in tablas.items():
            self._escribir_csv(ruta_salida / nombre, filas)
            print(f"  {nombre}: {len(filas)} filas")

        print(f"  resultados guardados en {ruta_salida}")

    @staticmethod
    def _filas_individuales(experimentos: list[Experimento]) -> list[Fila]:
        """una fila por peatón con todos sus indicadores"""
        return [
            {"experimento": exp.nombre, "id_peaton": id_peaton, **indicadores}
            for exp in experimentos
            for id_peaton, indicadores in sorted(exp.resultados_individuales.items())
        ]

    @staticmethod
    def _filas_zonas(experimentos: list[Experimento]) -> list[Fila]:
        """una fila por zona de cada experimento"""
        return [
            {
                "experimento": exp.nombre,
                "sentido_avance": exp.resultados_colectivos.get("sentido_avance"),
                **zona,
            }
            for exp in experimentos
            for zona in exp.resultados_colectivos.get("zonas", [])
        ]

    @staticmethod
    def _filas_densidad(experimentos: list[Experimento]) -> list[Fila]:
        """la densidad y la velocidad segundo a segundo de cada experimento"""
        return [
            {"experimento": exp.nombre, **muestra}
            for exp in experimentos
            for muestra in exp.resultados_colectivos.get("serie_densidad", [])
        ]

    @staticmethod
    def _filas_resumen(resultados: ResultadoAnalisis) -> list[Fila]:
        """una fila por experimento con los indicadores de la comparación"""
        return [
            {"experimento": nombre, **indicadores}
            for nombre, indicadores in resultados.comparacion.items()
        ]

    @staticmethod
    def _escribir_csv(ruta: Path, filas: list[Fila]) -> None:
        """escribe la tabla"""
        columnas = list(dict.fromkeys(columna for fila in filas for columna in fila))
        with open(ruta, "w", encoding="utf-8", newline="") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=columnas, restval="", lineterminator="\n")
            escritor.writeheader()
            # 6 decimales alcanzan sobrado 
            escritor.writerows(
                {columna: round(valor, 6) if isinstance(valor, float) else valor for columna, valor in fila.items()}
                for fila in filas
            )