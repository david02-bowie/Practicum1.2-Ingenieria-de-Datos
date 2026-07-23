from pathlib import Path
import sqlite3
import pandas as pd


DB_PATH = "db/macroentorno.db"
RUTA_VAB = Path("data/bronze/bce/VAB 2018-2023.xlsx")
RUTA_SALIDA_VAB = Path("data/processed/silver_vab.csv")


def normalizar_texto(valor):
    if pd.isna(valor):
        return ""
    return str(valor).strip().upper()


def conectar_db():
    conexion = sqlite3.connect(DB_PATH)
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def obtener_o_crear_geografia(conexion, provincia, cod_provincia, canton, cod_canton):
    cursor = conexion.cursor()

    cursor.execute(
        """
        SELECT id_geo
        FROM dim_geografia
        WHERE provincia = ?
          AND canton = ?
        """,
        (provincia, canton)
    )

    resultado = cursor.fetchone()

    if resultado:
        return resultado[0]

    cursor.execute(
        """
        INSERT INTO dim_geografia (
            provincia,
            cod_provincia,
            canton,
            cod_canton
        )
        VALUES (?, ?, ?, ?)
        """,
        (provincia, cod_provincia, canton, cod_canton)
    )

    return cursor.lastrowid


def limpiar_vab():
    print("Leyendo archivo VAB...")

    df = pd.read_excel(RUTA_VAB, sheet_name="DATA")

    print("Filas originales VAB:", len(df))

    columnas_necesarias = [
        "AÑO",
        "CÓDIGO PROVINCIA",
        "PROVINCIA",
        "CÓDIGO CANTÓN",
        "CANTÓN",
        "SECTOR",
        "VALOR"
    ]

    df = df[columnas_necesarias].copy()

    df = df.rename(columns={
        "AÑO": "anio",
        "CÓDIGO PROVINCIA": "cod_provincia",
        "PROVINCIA": "provincia",
        "CÓDIGO CANTÓN": "cod_canton",
        "CANTÓN": "canton",
        "SECTOR": "ciiu",
        "VALOR": "vab_miles_usd"
    })

    df["provincia"] = df["provincia"].apply(normalizar_texto)
    df["canton"] = df["canton"].apply(normalizar_texto)
    df["ciiu"] = df["ciiu"].apply(normalizar_texto)

    df["anio"] = pd.to_numeric(df["anio"], errors="coerce")
    df["cod_provincia"] = pd.to_numeric(df["cod_provincia"], errors="coerce")
    df["cod_canton"] = pd.to_numeric(df["cod_canton"], errors="coerce")
    df["vab_miles_usd"] = pd.to_numeric(df["vab_miles_usd"], errors="coerce")

    df = df.dropna(subset=["anio", "provincia", "canton", "vab_miles_usd"]).copy()

    df["anio"] = df["anio"].astype(int)

    RUTA_SALIDA_VAB.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(RUTA_SALIDA_VAB, index=False, encoding="utf-8-sig")

    print("Filas limpias VAB:", len(df))
    print("Archivo limpio generado:", RUTA_SALIDA_VAB)

    return df


def cargar_vab_sqlite(df):
    print("Cargando VAB a SQLite...")

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("DELETE FROM fact_vab")

    for _, fila in df.iterrows():
        id_geo = obtener_o_crear_geografia(
            conexion,
            fila["provincia"],
            None if pd.isna(fila["cod_provincia"]) else int(fila["cod_provincia"]),
            fila["canton"],
            None if pd.isna(fila["cod_canton"]) else int(fila["cod_canton"])
        )

        cursor.execute(
            """
            INSERT INTO fact_vab (
                id_geo,
                anio,
                ciiu,
                vab_miles_usd
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                id_geo,
                int(fila["anio"]),
                fila["ciiu"],
                float(fila["vab_miles_usd"])
            )
        )

    conexion.commit()
    conexion.close()

    print("Carga VAB finalizada correctamente.")


if __name__ == "__main__":
    datos_vab = limpiar_vab()
    cargar_vab_sqlite(datos_vab)