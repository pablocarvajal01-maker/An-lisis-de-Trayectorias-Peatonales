"""geometria del corredor donde caminan los peatones
sistema de coordenadas de los datos (uni_corr):
  - x: ancho del corredor, de -2.5 m a 2.5 m (5 m de ancho)
  - y: largo del corredor, es la direccion en que avanza la gente

se observo que el sentido de como caminan los peatones cambia segun el experimento.
 en 01, 04, 06 y 08 la gente camina hacia y negativo, en 03, 05, 07 y 09 hacia y positivo.
 por eso las zonas se numeran segun el sentido detectado (zona 1 = la de la entrada)
"""

from dataclasses import dataclass

from .observacion import Observacion
from .trayectoria import Trayectoria


def sentido_de_avance(trayectorias: list[Trayectoria]) -> int:
    """+1 si la mayoria avanza hacia y positivo, -1 si hacia y negativo

    se cuenta cuantos peatones terminan mas arriba de donde partieron y se
    hace una votacion por mayoria, asi unos pocos peatones raros no cambian
    el resultado
    """
    if not trayectorias:
        return 1
    suben = sum(1 for t in trayectorias if t.posicion_final[1] > t.posicion_inicial[1])
    return 1 if suben >= len(trayectorias) / 2 else -1


@dataclass(frozen=True)
class Zona:
    """tramo del corredor entre y_bajo e y_alto"""

    numero: int
    y_bajo: float
    y_alto: float
    sentido: int = 1  # +1: se entra por y_bajo, -1: se entra por y_alto

    @property
    def largo(self) -> float:
        return self.y_alto - self.y_bajo

    @property
    def y_entrada(self) -> float:
        return self.y_bajo if self.sentido > 0 else self.y_alto

    @property
    def y_salida(self) -> float:
        return self.y_alto if self.sentido > 0 else self.y_bajo

    def contiene(self, observacion: Observacion) -> bool:
        """true si la observacion cae dentro del tramo"""
        return self.y_bajo <= observacion.y < self.y_alto

    def es_cruzada_por(self, trayectoria: Trayectoria) -> bool:
        """true si el peaton fue observado a ambos lados de la zona

        asi solo cuentan los peatones que la atravesaron completa. si alguien
        aparece o desaparece a mitad de zona, su tiempo de cruce saldria
        artificialmente corto y ensuciaria el promedio
        """
        ys = [obs.y for obs in trayectoria.observaciones]
        return min(ys) <= self.y_bajo and max(ys) >= self.y_alto


@dataclass(frozen=True)
class Corredor:
    """region del corredor que se analiza

    por defecto se toma y entre -4 m y 4 m: es el tramo que la camara cubre
    bien en todos los experimentos (en el 09 la cobertura cae despues de y = 4,
    y antes de y = -5 casi no hay datos en ninguno)
    """

    x_min: float = -2.5
    x_max: float = 2.5
    y_min: float = -4.0
    y_max: float = 4.0

    @property
    def ancho(self) -> float:
        return self.x_max - self.x_min

    def dividir_en_zonas(self, cantidad: int, sentido: int = 1) -> list[Zona]:
        """divide el tramo en cantidad zonas iguales, numeradas desde la entrada

        zona 1 = la primera que pisa el peaton segun el sentido de avance
        """
        if cantidad <= 0:
            raise ValueError(f"La cantidad de zonas debe ser positiva, llegó: {cantidad}")
        largo = (self.y_max - self.y_min) / cantidad
        bordes = [(self.y_min + i * largo, self.y_min + (i + 1) * largo) for i in range(cantidad)]
        if sentido < 0:
            bordes.reverse()  # la entrada queda en el y mas alto
        return [
            Zona(numero=i + 1, y_bajo=bajo, y_alto=alto, sentido=sentido)
            for i, (bajo, alto) in enumerate(bordes)
        ]
