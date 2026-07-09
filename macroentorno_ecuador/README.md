# Pipeline de datos del macroentorno ecuatoriano

Este proyecto desarrolla un pipeline de datos para organizar, limpiar y visualizar indicadores del macroentorno ecuatoriano. La solución sigue una arquitectura medallón con tres capas: Bronze, Silver y Gold.

## Objetivo

Construir un flujo de datos reproducible que permita pasar desde archivos crudos de fuentes públicas hasta un dashboard analítico en Power BI.

## Metodología

La metodología usada se basa en el modelo medallón y en un proceso ETL.

- Bronze: almacenamiento de archivos originales sin modificaciones.
- Silver: limpieza, normalización y carga de datos en SQLite.
- Gold: creación de vistas SQL con indicadores listos para Power BI.

## Herramientas

- Python
- Pandas
- SQLite
- Power BI
- draw.io
- GitHub