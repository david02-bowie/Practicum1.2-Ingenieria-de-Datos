# Entrega final - Macroentorno Ecuador

## Prácticum 1.2 - Ingeniería de Datos

Este proyecto desarrolla un pipeline de datos del macroentorno ecuatoriano con arquitectura Bronze, Silver y Gold.

Integra información del BCE, MINEDUC y Supercias, procesa los datos con Python, los carga en SQLite, genera vistas Gold y presenta los resultados en Power BI.

## Estructura

- macroentorno_ecuador/src/: scripts del pipeline.
- macroentorno_ecuador/sql/: creación de tablas y vistas.
- macroentorno_ecuador/db/: base de datos SQLite.
- macroentorno_ecuador/data/processed/: datos limpios.
- macroentorno_ecuador/data/gold/: salidas finales para análisis.
- macroentorno_ecuador/dashboard/: tablero final en Power BI.
- macroentorno_ecuador/requirements.txt: dependencias del proyecto.

## Cómo ejecutar

Entrar a la carpeta:

macroentorno_ecuador

Instalar dependencias:

pip install -r requirements.txt

Ejecutar el pipeline:

python src/pipeline.py

## Dashboard

El dashboard final se encuentra en:

macroentorno_ecuador/dashboard/

## Nota sobre archivos RPA

Los archivos SQL originales generados por RPA no se suben al repositorio por su tamaño. Se conservan las salidas procesadas, la base SQLite y el dashboard final.
