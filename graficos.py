"""graficos del informe

lee los csv de results/ y guarda las figuras en figuras/ con ejes rotulados y unidades
solo la figura de trayectorias necesita los datos crudos (carpeta data/) porque los csv no traen posiciones

"""

import argparse
import contextlib
import csv
import io
import math
from pathlib import Path
from typing import Sequence

import matplotlib

# backend sin ventana pa que corra tambien en el servidor linux
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

DPI = 200
GRIS = "0.65"
COLUMNAS_GRILLA = 3


# lectura


def leer_csv(ruta: Path) -> list[dict]:
    """lee un csv y pasa a float lo que se pueda, lo vacio queda como texto vacio"""
    with open(ruta, encoding="utf-8", newline="") as archivo:
        filas = list(csv.DictReader(archivo))
    for fila in filas:
        for columna, valor in fila.items():
            if columna == "experimento":
                continue
            try:
                fila[columna] = float(valor)
            except (TypeError, ValueError):
                pass
    return filas


def agrupar(filas: list[dict]) -> dict[str, list[dict]]:
    """filas por experimento, en el orden en que aparecen"""
    grupos: dict[str, list[dict]] = {}
    for fila in filas:
        grupos.setdefault(fila["experimento"], []).append(fila)
    return grupos


def nombre_corto(experimento: str) -> str:
    """uni_corr_500_03 -> 03"""
    return experimento.split("_")[-1]


def columna(filas: list[dict], nombre: str) -> np.ndarray:
    return np.array([f[nombre] for f in filas], dtype=float)


def colores_por_experimento(experimentos: Sequence[str]) -> dict[str, tuple]:
    """un color fijo por experimento, el mismo en todas las figuras"""
    paleta = plt.get_cmap("tab10")
    return {exp: paleta(i % 10) for i, exp in enumerate(sorted(experimentos))}


#  utilidades de dibujo


def grilla(n: int, **opciones):
    """grilla de n paneles de 3 columnas, los paneles que sobran se esconden"""
    filas = math.ceil(n / COLUMNAS_GRILLA)
    fig, ejes = plt.subplots(
        filas, COLUMNAS_GRILLA, figsize=(4.0 * COLUMNAS_GRILLA, 2.9 * filas), squeeze=False, **opciones
    )
    planos = ejes.ravel()
    for eje in planos[n:]:
        eje.set_visible(False)
    return fig, planos[:n], ejes


def rotular_grilla(planos, xlabel: str, ylabel: str) -> None:
    """rotulos solo en el borde de la grilla pa no repetirlos en cada panel"""
    for i, eje in enumerate(planos):
        if i % COLUMNAS_GRILLA == 0:
            eje.set_ylabel(ylabel)
        # el ultimo panel de cada columna lleva el xlabel
        if i + COLUMNAS_GRILLA >= len(planos):
            eje.set_xlabel(xlabel)


def guardar(fig, ruta: Path) -> None:
    fig.tight_layout()
    fig.savefig(ruta, dpi=DPI)
    plt.close(fig)
    print(f"  {ruta}")


def ajuste_lineal(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    """recta y = a + b x por minimos cuadrados, devuelve (a, b, r2)"""
    b, a = np.polyfit(x, y, 1)
    residuo = y - (a + b * x)
    total = y - y.mean()
    r2 = 1.0 - float(residuo @ residuo) / float(total @ total) if float(total @ total) > 0 else 0.0
    return float(a), float(b), r2


#  figuras


def fig_velocidad_por_zona(zonas: list[dict], colores: dict, salida: Path) -> None:
    """velocidad media de avance en cada zona, una barra por zona y una barrita de error con la desviacion"""
    grupos = agrupar(zonas)
    fig, planos, _ = grilla(len(grupos), sharey=True)
    for eje, (exp, filas) in zip(planos, grupos.items()):
        z = columna(filas, "zona")
        eje.bar(z, columna(filas, "velocidad_media"), yerr=columna(filas, "velocidad_desviacion"),
                color=colores[exp], capsize=3, edgecolor="white")
        sentido = "y+" if filas[0].get("sentido_avance", 1) > 0 else "y-"
        eje.set_title(f"Exp. {nombre_corto(exp)} (avance hacia {sentido})", fontsize=10)
        eje.set_xticks(z)
        eje.grid(axis="y", alpha=0.3)
    planos[0].set_ylim(bottom=0)
    rotular_grilla(planos, "Zona (1 = entrada)", "Velocidad de avance [m/s]")
    guardar(fig, salida / "velocidad_por_zona.png")


def fig_densidad_tiempo(densidad: list[dict], colores: dict, salida: Path) -> None:
    """densidad segundo a segundo, la meseta en color y las rampas de llenado y vaciado en gris"""
    grupos = agrupar(densidad)
    fig, planos, _ = grilla(len(grupos), sharey=True)
    for eje, (exp, filas) in zip(planos, grupos.items()):
        t = columna(filas, "tiempo")
        rho = columna(filas, "densidad")
        meseta = columna(filas, "estacionario") == 1
        eje.plot(t, rho, color=GRIS, lw=1.0, label="llenado y vaciado")
        eje.plot(t, np.where(meseta, rho, np.nan), color=colores[exp], lw=1.6, label="meseta")
        eje.set_title(f"Exp. {nombre_corto(exp)}", fontsize=10)
        eje.grid(alpha=0.3)
    planos[0].set_ylim(bottom=0)
    planos[0].legend(fontsize=8, loc="upper left")
    rotular_grilla(planos, "Tiempo [s]", "Densidad [p/m²]")
    guardar(fig, salida / "densidad_tiempo.png")


def fig_flujo_tiempo(flujo: list[dict], resumen: list[dict], colores: dict, salida: Path) -> None:
    """flujo por la linea de medicion en ventanas de tiempo, con el flujo medio como linea punteada"""
    medio = {f["experimento"]: f.get("flujo_medio") for f in resumen}
    grupos = agrupar(flujo)
    fig, planos, _ = grilla(len(grupos), sharey=True)
    for eje, (exp, filas) in zip(planos, grupos.items()):
        t = columna(filas, "tiempo")
        # ancho de la ventana, sale de la distancia entre ventanas (10 s en el pipeline)
        ventana = float(np.median(np.diff(t))) if len(t) > 1 else 10.0
        eje.bar(t, columna(filas, "flujo"), width=ventana, align="edge", color=colores[exp], edgecolor="white")
        if isinstance(medio.get(exp), float):
            eje.axhline(medio[exp], color="black", ls="--", lw=1.0, label="flujo medio")
        eje.set_title(f"Exp. {nombre_corto(exp)}", fontsize=10)
        eje.grid(axis="y", alpha=0.3)
    planos[0].set_ylim(bottom=0)
    if any(isinstance(v, float) for v in medio.values()):
        planos[0].legend(fontsize=8, loc="upper right")
    rotular_grilla(planos, "Tiempo [s]", "Flujo [p/s]")
    guardar(fig, salida / "flujo_tiempo.png")


def datos_validos(densidad: list[dict]):
    """segundos con gente y con velocidad medida, los demas no sirven pa el diagrama"""
    filas = [f for f in densidad if f["densidad"] > 0 and f["velocidad_media"] > 0]
    return (
        [f["experimento"] for f in filas],
        columna(filas, "densidad"),
        columna(filas, "velocidad_media"),
        columna(filas, "estacionario") == 1,
    )


def fig_diagrama_fundamental(densidad: list[dict], colores: dict, salida: Path):
    """velocidad contra densidad, meseta en color por experimento, rampas en gris y la recta del ajuste
    el ajuste usa solo la meseta porque en las rampas el corredor se esta llenando o vaciando
    """
    exps, rho, v, meseta = datos_validos(densidad)
    fig, eje = plt.subplots(figsize=(6.5, 4.6))
    eje.scatter(rho[~meseta], v[~meseta], s=6, color=GRIS, alpha=0.6, label="llenado y vaciado")
    for exp in sorted(set(exps)):
        marca = np.array([e == exp for e in exps]) & meseta
        eje.scatter(rho[marca], v[marca], s=9, color=colores[exp], alpha=0.8, label=f"Exp. {nombre_corto(exp)}")
    ajuste = None
    if meseta.sum() >= 3 and np.ptp(rho[meseta]) > 0:
        a, b, r2 = ajuste_lineal(rho[meseta], v[meseta])
        xs = np.linspace(0, rho.max() * 1.05, 50)
        signo = "-" if b < 0 else "+"
        eje.plot(xs, a + b * xs, "k--", lw=1.5,
                 label=f"Ajuste: v = {a:.2f} {signo} {abs(b):.2f}·ρ  (R² = {r2:.2f})")
        ajuste = (a, b, r2, int(meseta.sum()))
    eje.set_xlabel("Densidad [p/m²]")
    eje.set_ylabel("Velocidad media [m/s]")
    eje.set_xlim(left=0)
    eje.set_ylim(bottom=0)
    eje.grid(alpha=0.3)
    eje.legend(fontsize=7, ncol=2, loc="upper right")
    guardar(fig, salida / "diagrama_fundamental.png")
    return ajuste


def fig_flujo_densidad(densidad: list[dict], resumen: list[dict], colores: dict, ajuste, salida: Path) -> None:
    """flujo especifico contra densidad

    puntitos = rho * v de cada segundo de la meseta, en el area de medicion
    puntos grandes = flujo medido contando cruces por la linea, uno por experimento
    si los dos coinciden se validan densidad velocidad y flujo con metodos independientes
    """
    exps, rho, v, meseta = datos_validos(densidad)
    fig, eje = plt.subplots(figsize=(6.5, 4.6))
    for exp in sorted(set(exps)):
        marca = np.array([e == exp for e in exps]) & meseta
        eje.scatter(rho[marca], rho[marca] * v[marca], s=7, color=colores[exp], alpha=0.35)
    # el flujo medido sale del resumen, junto a la densidad de la meseta
    for fila in resumen:
        exp = fila["experimento"]
        if not isinstance(fila.get("densidad_estacionaria"), float):
            continue
        eje.scatter(fila["densidad_estacionaria"], fila["flujo_especifico"], s=90, color=colores[exp],
                    edgecolor="black", zorder=3)
        eje.annotate(nombre_corto(exp), (fila["densidad_estacionaria"], fila["flujo_especifico"]),
                     textcoords="offset points", xytext=(6, 6), fontsize=8)
    if ajuste is not None:
        a, b, _, _ = ajuste
        xs = np.linspace(0, rho.max() * 1.05, 80)
        eje.plot(xs, xs * (a + b * xs), "k--", lw=1.2, label="ρ·v del ajuste lineal")
    eje.scatter([], [], s=90, color="white", edgecolor="black", label="J medido en la línea (por experimento)")
    eje.scatter([], [], s=7, color=GRIS, label="ρ·v por segundo (meseta)")
    eje.legend(fontsize=8, loc="upper right")
    eje.set_xlabel("Densidad [p/m²]")
    eje.set_ylabel("Flujo específico [p/(m·s)]")
    eje.set_xlim(left=0)
    eje.set_ylim(bottom=0)
    eje.grid(alpha=0.3)
    guardar(fig, salida / "flujo_densidad.png")


def cargar_trayectorias(ruta_datos: Path, experimento: str):
    """carga y valida un experimento con las mismas etapas del pipeline pa dibujar sus trayectorias"""
    # se importa aca pa que el resto de las figuras no dependa de los datos crudos
    from pipeline.contexto import ContextoPipeline
    from stages import CargaExperimentos, PreparacionTrayectorias, ValidacionExperimentos

    archivo = ruta_datos / f"{experimento}.txt"
    if not archivo.is_file():
        return None
    contexto = ContextoPipeline(ruta_entrada=archivo, ruta_salida=Path("."))
    with contextlib.redirect_stdout(io.StringIO()):
        exps = CargaExperimentos().ejecutar(None, contexto)
        exps = ValidacionExperimentos().ejecutar(exps, contexto)
        exps = PreparacionTrayectorias().ejecutar(exps, contexto)
    return exps[0].trayectorias


def fig_trayectorias(
    zonas: list[dict], ruta_datos: Path, elegidos: Sequence[str], colores: dict, salida: Path, muestra: int = 30
) -> None:
    """trayectorias de muestra con las paredes del corredor y las zonas, una columna por experimento"""
    from models.corredor import Corredor

    corredor = Corredor()
    sentidos = {exp: filas[0].get("sentido_avance", 1) for exp, filas in agrupar(zonas).items()}
    paneles = []
    for corto in elegidos:
        exp = next((e for e in sentidos if nombre_corto(e) == corto), None)
        trayectorias = cargar_trayectorias(ruta_datos, exp) if exp else None
        if trayectorias is None:
            print(f"  sin datos crudos pa el experimento {corto}, me salto sus trayectorias")
            continue
        paneles.append((exp, trayectorias))
    if not paneles:
        return

    fig, ejes = plt.subplots(1, len(paneles), figsize=(3.3 * len(paneles), 7.5), squeeze=False)
    for eje, (exp, trayectorias) in zip(ejes[0], paneles):
        # muestra repartida parejo entre los peatones del experimento
        paso = max(1, len(trayectorias) // muestra)
        for tray in trayectorias[::paso][:muestra]:
            eje.plot([o.x for o in tray.observaciones], [o.y for o in tray.observaciones],
                     color=colores[exp], lw=0.8, alpha=0.7)
        sentido = int(sentidos[exp])
        for zona in corredor.dividir_en_zonas(4, sentido):
            for borde in (zona.y_bajo, zona.y_alto):
                eje.axhline(borde, color="0.5", ls=":", lw=0.8)
            eje.text(corredor.x_max + 0.15, (zona.y_bajo + zona.y_alto) / 2, f"Z{zona.numero}",
                     va="center", fontsize=9)
        for pared in (corredor.x_min, corredor.x_max):
            eje.axvline(pared, color="black", lw=2)
        # flecha del sentido de avance
        y0 = corredor.y_min - 0.5 if sentido > 0 else corredor.y_max + 0.5
        eje.annotate("", xy=(0, y0 + 1.5 * sentido), xytext=(0, y0),
                     arrowprops=dict(arrowstyle="->", color="black", lw=1.5))
        eje.set_title(f"Exp. {nombre_corto(exp)}", fontsize=10)
        eje.set_xlabel("x [m]")
        eje.set_xlim(corredor.x_min - 0.5, corredor.x_max + 0.9)
        eje.set_ylim(corredor.y_min - 1.5, corredor.y_max + 1.5)
        eje.set_aspect("equal")
    ejes[0][0].set_ylabel("y [m]")
    guardar(fig, salida / "trayectorias.png")


# main


def crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gráficos del informe a partir de los CSV de results/")
    parser.add_argument("--results", type=Path, default=Path("./results"), help="carpeta con los csv (por defecto ./results)")
    parser.add_argument("--data", type=Path, default=Path("./data"), help="carpeta con los datos crudos, solo pa las trayectorias (por defecto ./data)")
    parser.add_argument("--output", type=Path, default=Path("./figuras"), help="carpeta donde se guardan las figuras (por defecto ./figuras)")
    parser.add_argument("--trayectorias", nargs="*", default=["03", "09"], metavar="NN",
                        help="experimentos pa la figura de trayectorias, por ejemplo 03 09")
    return parser


def main(argumentos: Sequence[str] | None = None) -> int:
    configuracion = crear_parser().parse_args(argumentos)
    res = configuracion.results
    necesarios = ["densidad.csv", "flujo.csv", "zonas.csv", "resumen_experimentos.csv"]
    faltan = [n for n in necesarios if not (res / n).is_file()]
    if faltan:
        print(f"faltan csv en {res}: {', '.join(faltan)}. corre primero python3 main.py")
        return 1

    densidad, flujo = leer_csv(res / "densidad.csv"), leer_csv(res / "flujo.csv")
    zonas, resumen = leer_csv(res / "zonas.csv"), leer_csv(res / "resumen_experimentos.csv")
    colores = colores_por_experimento([f["experimento"] for f in resumen])
    configuracion.output.mkdir(parents=True, exist_ok=True)
    salida = configuracion.output

    print("Guardando figuras:")
    if configuracion.trayectorias:
        fig_trayectorias(zonas, configuracion.data, configuracion.trayectorias, colores, salida)
    fig_velocidad_por_zona(zonas, colores, salida)
    fig_densidad_tiempo(densidad, colores, salida)
    fig_flujo_tiempo(flujo, resumen, colores, salida)
    ajuste = fig_diagrama_fundamental(densidad, colores, salida)
    fig_flujo_densidad(densidad, resumen, colores, ajuste, salida)
    if ajuste:
        a, b, r2, n = ajuste
        print(f"  ajuste de la meseta: v = {a:.3f} {'-' if b < 0 else '+'} {abs(b):.3f}·rho (R2 = {r2:.3f}, {n} segundos)")
        if b < 0:
            print(f"  velocidad libre = {a:.2f} m/s, densidad de atasco = {-a / b:.2f} p/m2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())