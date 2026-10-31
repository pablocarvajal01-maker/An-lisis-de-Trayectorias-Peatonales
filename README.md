# Análisis de Trayectorias Peatonales

Los argumentos permiten configurar el programa desde la terminal sin editar el código fuente. `--input` y `--output` tienen valores predeterminados y pueden cambiarse al ejecutar el programa.

## Requisitos

Python 3.10 o superior y las dependencias de `requirements.txt` (`numpy` y `matplotlib`).

## Ejecución en equipo nuevo

```bash
python3 --version
git clone https://github.com/pablocarvajal01-maker/An-lisis-de-Trayectorias-Peatonales.git
cd An-lisis-de-Trayectorias-Peatonales
python3 -m pip install --user -r requirements.txt
python3 -m unittest
python3 main.py
python3 graficos.py
```

## Ejecución general

Si ya tienes el repositorio, desde su carpeta:

```bash
python3 --version
python3 -m pip install --user -r requirements.txt
```

## Datos

Los archivos van en `data/` con el nombre `uni_corr_500_XX.txt` (XX = 01 a 09).

## Ejecución básica

```bash
python3 main.py
```

## Ejecución con parámetros

```bash
python3 main.py --input ./data --output ./results
```

## Especificar frecuencia

```bash
python3 main.py --input ./data --output ./results --fps 25
```

## Mostrar ayuda

```bash
python3 main.py --help
```

## Resultados

El programa guarda en `results/` (o en la carpeta de `--output`):

- `individual.csv`: una fila por peatón (tiempo, distancia, velocidad, eficiencia y detenciones).
- `zonas.csv`: velocidad y tiempo de cruce por zona de cada experimento.
- `densidad.csv`: densidad y velocidad media segundo a segundo, con la marca de la meseta.
- `flujo.csv`: cruces de la línea y flujo en ventanas de 10 s.
- `resumen_experimentos.csv`: una fila por experimento con los indicadores colectivos.

## Gráficos

```bash
python3 graficos.py
```

Lee los CSV de `results/` y guarda las figuras en `figuras/`.

## Tests

```bash
python3 -m unittest
```

Los comandos también pueden ejecutarse con `python` cuando corresponda. En el servidor Linux del curso se usa `python3`; en Windows normalmente es `python` (o `py`) y `pip` se llama con `python -m pip`. La versión debe ser 3.10 o superior en ambos casos.