from pathlib import Path
import sqlite3
import pandas as pd


DB_PATH = "db/macroentorno.db"
RUTA_IEE = Path("data/bronze/bce/IEE.xlsx")
RUTA_SALIDA_IEE = Path("data/processed/silver_iee.csv")


def conectar_db():
    conexion = sqlite3.connect(DB_PATH)
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def preparar_tabla_iee():
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("PRAGMA table_info(fact_iee)")
    columnas = [fila[1] for fila in cursor.fetchall()]

    if "servicios" not in columnas:
        cursor.execute("ALTER TABLE fact_iee ADD COLUMN servicios REAL")

    conexion.commit()
    conexion.close()


def limpiar_iee():
    print("Leyendo archivo IEE...")

    df = pd.read_excel(
        RUTA_IEE,
        sheet_name="IEE",
        header=7
    )

    print("Filas originales IEE:", len(df))

    columnas_necesarias = [
        "Fecha",
        "IEE Global (2)",
        "Comercio",
        "Construcción",
        "Manufactura",
        "Servicios"
    ]

    df = df[columnas_necesarias].copy()

    df = df.rename(columns={
        "Fecha": "fecha",
        "IEE Global (2)": "iee_global",
        "Comercio": "comercio",
        "Construcción": "construccion",
        "Manufactura": "manufactura",
        "Servicios": "servicios"
    })

    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["iee_global"] = pd.to_numeric(df["iee_global"], errors="coerce")
    df["comercio"] = pd.to_numeric(df["comercio"], errors="coerce")
    df["construccion"] = pd.to_numeric(df["construccion"], errors="coerce")
    df["manufactura"] = pd.to_numeric(df["manufactura"], errors="coerce")
    df["servicios"] = pd.to_numeric(df["servicios"], errors="coerce")

    df = df.dropna(subset=["fecha"]).copy()

    df["anio"] = df["fecha"].dt.year
    df["mes"] = df["fecha"].dt.month
    df["fecha"] = df["fecha"].dt.strftime("%Y-%m-%d")

    df = df[
        [
            "fecha",
            "anio",
            "mes",
            "iee_global",
            "comercio",
            "construccion",
            "manufactura",
            "servicios"
        ]
    ].copy()

    RUTA_SALIDA_IEE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(RUTA_SALIDA_IEE, index=False, encoding="utf-8-sig")

    print("Filas limpias IEE:", len(df))
    print("Archivo limpio generado:", RUTA_SALIDA_IEE)

    return df


def cargar_iee_sqlite(df):
    print("Cargando IEE a SQLite...")

    preparar_tabla_iee()

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("DELETE FROM fact_iee")

    for _, fila in df.iterrows():
        cursor.execute(
            """
            INSERT INTO fact_iee (
                fecha,
                anio,
                mes,
                iee_global,
                comercio,
                construccion,
                manufactura,
                servicios
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fila["fecha"],
                int(fila["anio"]),
                int(fila["mes"]),
                float(fila["iee_global"]),
                float(fila["comercio"]),
                float(fila["construccion"]),
                float(fila["manufactura"]),
                float(fila["servicios"])
            )
        )

    conexion.commit()
    conexion.close()

    print("Carga IEE finalizada correctamente.")


if __name__ == "__main__":
    datos_iee = limpiar_iee()
    cargar_iee_sqlite(datos_iee)