"""Etapa de carga de varios experimentos."""

import re
from pathlib import Path

from models.experimento import Experimento
from models.observacion import Observacion
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline

# Orden de columnas de los archivos viene escrito en la primera línea de cada archivo
COLUMNAS_ESPERADAS = ("number", "frame", "x", "y", "z", "rot", "id", "flag")

# Factor pa' pasar cada unidad a metros, peeero los archivos 01-06 vienen en m
# y los 07-09 en cm, así que NO se puede asumir una sola unidad pa todos
UNIDAD_A_METROS = {"m": 1.0, "cm": 0.01, "mm": 0.001}

# Agarra cada "<columna>" con su "[in unidad]" si lo trae.
_COLUMNA_CON_UNIDAD = re.compile(r"<(\w+)>(?:\s*\[in\s+(\w+)\])?")


class CargaExperimentos(EtapaPipeline[None, list[Experimento]]):
    """Carga una colección de experimentos desde la ruta configurada."""

    def ejecutar(
        self,
        entrada: None,
        contexto: ContextoPipeline,
    ) -> list[Experimento]:
        """Carga los experimentos indicados por la configuracion"""
        experimentos = self._cargar_experimentos(contexto.ruta_entrada)
        for experimento in experimentos:
            print(f"  {experimento.nombre}: {len(experimento.observaciones)} observaciones")
        return experimentos

    def _cargar_experimentos(self, ruta_entrada: Path) -> list[Experimento]:
        """Carga los experimentos disponibles en la ruta recibida."""
        return [self._cargar_archivo(ruta) for ruta in self._listar_archivos(ruta_entrada)]

    def _listar_archivos(self, ruta_entrada: Path) -> list[Path]:
        """Un archivo suelto o todos los .txt de una carpeta, ordenados por nombre"""
        if ruta_entrada.is_file():
            return [ruta_entrada]
        if not ruta_entrada.is_dir():
            raise FileNotFoundError(f"La ruta de entrada no existe: {ruta_entrada}")
        rutas = sorted(ruta_entrada.glob("*.txt"))
        if not rutas:
            raise FileNotFoundError(f"No hay archivos .txt en: {ruta_entrada}")
        return rutas

    def _cargar_archivo(self, ruta: Path) -> Experimento:
        """Lee un archivo y lo convierte en un experimento con sus observaciones"""
        escalas = self._leer_cabecera(ruta)
        observaciones, descartadas = self._leer_observaciones(ruta, escalas)
        if descartadas:
            # no llegamos y las botamos, avisamos cuántas fueron
            print(f"  Ojo: {ruta.name} traía {descartadas} líneas malformadas y las salté.")
        return Experimento(nombre=ruta.stem, observaciones=observaciones)

    def _leer_cabecera(self, ruta: Path) -> dict[str, float]:
        """Lee la primera línea y devuelve el factor a metros de x, y, z."""
        # newline=None, da lo mismo si el archivo viene con \r\n (Windows) o \n
        with open(ruta, encoding="utf-8", newline=None) as archivo:
            primera_linea = archivo.readline()

        columnas = _COLUMNA_CON_UNIDAD.findall(primera_linea)
        nombres = tuple(nombre for nombre, _ in columnas)
        if nombres != COLUMNAS_ESPERADAS:
            raise ValueError(
                f"{ruta.name}: las columnas {nombres} no son las esperadas {COLUMNAS_ESPERADAS}"
            )

        escalas = {}
        for nombre, unidad in columnas:
            if nombre in ("x", "y", "z"):
                if unidad not in UNIDAD_A_METROS:
                    raise ValueError(f"{ruta.name}: unidad desconocida '{unidad}' en la columna {nombre}")
                escalas[nombre] = UNIDAD_A_METROS[unidad]
        return escalas

    def _leer_observaciones(
        self,
        ruta: Path,
        escalas: dict[str, float],
    ) -> tuple[list[Observacion], int]:
        """Devuelve observaciones, cantidad de líneas malformadas que se descartaron"""
        observaciones: list[Observacion] = []
        descartadas = 0
        with open(ruta, encoding="utf-8", newline=None) as archivo:
            for linea in archivo:
                if linea.startswith("#") or not linea.strip():
                    continue
                observacion = self._parsear_linea(linea, escalas)
                if observacion is None:
                    descartadas += 1
                else:
                    observaciones.append(observacion)
        return observaciones, descartadas

    def _parsear_linea(self, linea: str, escalas: dict[str, float]) -> Observacion | None:
        """Convierte una linea en Observacion; None si viene mala"""
        campos = linea.split()
        if len(campos) != len(COLUMNAS_ESPERADAS):
            return None
        try:
            return Observacion(
                # columna 1 ("number"), no la 7 ("id"): esa trae -1 para mucha gente
                id_peaton=int(campos[0]),
                frame=int(campos[1]),
                x=float(campos[2]) * escalas["x"],
                y=float(campos[3]) * escalas["y"],
                z=float(campos[4]) * escalas["z"],
                flag=int(campos[7]),
            )
        except ValueError:
            return None