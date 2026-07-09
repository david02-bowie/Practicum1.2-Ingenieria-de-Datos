from pathlib import Path
import pandas as pd


CARPETA_BCE = Path("data/bronze/bce")
CARPETA_MINEDUC = Path("data/bronze/mineduc")


def explorar_excel(ruta_archivo):
    print("\n" + "=" * 80)
    print("ARCHIVO EXCEL:", ruta_archivo.name)

    excel = pd.ExcelFile(ruta_archivo)
    print("Hojas encontradas:", excel.sheet_names)

    for hoja in excel.sheet_names:
        print("\n--- Hoja:", hoja, "---")

        df = pd.read_excel(ruta_archivo, sheet_name=hoja, nrows=5)

        print("Filas leídas:", len(df))
        print("Columnas:")
        for columna in df.columns:
            print("-", columna)

        print("\nPrimeras filas:")
        print(df.head())


def explorar_csv(ruta_archivo):
    print("\n" + "=" * 80)
    print("ARCHIVO CSV:", ruta_archivo.name)

    try:
        df = pd.read_csv(ruta_archivo, sep=";", encoding="latin-1", nrows=5)
    except Exception:
        df = pd.read_csv(ruta_archivo, nrows=5)

    print("Filas leídas:", len(df))
    print("Columnas:")
    for columna in df.columns:
        print("-", columna)

    print("\nPrimeras filas:")
    print(df.head())


def explorar_carpeta(carpeta):
    archivos = list(carpeta.glob("*"))

    for archivo in archivos:
        nombre = archivo.name.lower()

        if nombre.endswith(".xlsx") or nombre.endswith(".xls"):
            explorar_excel(archivo)

        elif nombre.endswith(".csv"):
            explorar_csv(archivo)

        else:
            print("Archivo ignorado:", archivo.name)


if __name__ == "__main__":
    print("EXPLORANDO ARCHIVOS BCE")
    explorar_carpeta(CARPETA_BCE)

    print("\n\nEXPLORANDO ARCHIVOS MINEDUC")
    explorar_carpeta(CARPETA_MINEDUC)