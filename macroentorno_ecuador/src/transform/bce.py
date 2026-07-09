from pathlib import Path
import sqlite3
import pandas as pd


DB_PATH = "db/macroentorno.db"

RUTA_PIB = Path("data/bronze/bce/PIB.xlsx")
RUTA_PETROLEO = Path("data/bronze/bce/PETRÓLEO.xlsx")
RUTA_RIESGO = Path("data/bronze/bce/RIESGO PAÍS.xlsx")

RUTA_SALIDA_PIB = Path("data/processed/silver_pib.csv")
RUTA_SALIDA_INDICADORES = Path("data/processed/silver_indicadores_diarios.csv")


def conectar_db():
    conexion = sqlite3.connect(DB_PATH)
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def obtener_o_crear_tiempo(conexion, anio):
    cursor = conexion.cursor()
    fecha = f"{anio}-01-01"

    cursor.execute(
        """
        SELECT id_tiempo
        FROM dim_tiempo
        WHERE anio = ?
        """,
        (anio,)
    )

    resultado = cursor.fetchone()

    if resultado:
        return resultado[0]

    cursor.execute(
        """
        INSERT INTO dim_tiempo (
            fecha,
            anio,
            mes,
            trimestre
        )
        VALUES (?, ?, ?, ?)
        """,
        (fecha, anio, 1, 1)
    )

    return cursor.lastrowid


def limpiar_pib():
    print("Leyendo archivo PIB...")

    df = pd.read_excel(RUTA_PIB)

    print("Filas originales PIB:", len(df))

    columnas_necesarias = [
        "AÑO",
        "PIB 2018 = 100.1",
        "VAR ANUAL PIB",
        "PIB PER CÁPITA NOMINAL"
    ]

    df = df[columnas_necesarias].copy()

    df = df.rename(columns={
        "AÑO": "anio",
        "PIB 2018 = 100.1": "pib_real_musd",
        "VAR ANUAL PIB": "variacion_pib_pct",
        "PIB PER CÁPITA NOMINAL": "pib_percapita_nominal"
    })

    df["anio"] = pd.to_numeric(df["anio"], errors="coerce")
    df["pib_real_musd"] = pd.to_numeric(df["pib_real_musd"], errors="coerce")
    df["pib_percapita_nominal"] = pd.to_numeric(df["pib_percapita_nominal"], errors="coerce")
    df["variacion_pib_pct"] = pd.to_numeric(df["variacion_pib_pct"], errors="coerce")

    df = df.dropna(subset=["anio", "pib_real_musd"]).copy()

    df["anio"] = df["anio"].astype(int)

    # El archivo trae la variación como decimal: 0.042 = 4.2 %
    df["variacion_pib_pct"] = df["variacion_pib_pct"] * 100
    df["variacion_pib_pct"] = df["variacion_pib_pct"].fillna(0)

    RUTA_SALIDA_PIB.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(RUTA_SALIDA_PIB, index=False, encoding="utf-8-sig")

    print("Filas limpias PIB:", len(df))
    print("Archivo limpio generado:", RUTA_SALIDA_PIB)

    return df


def cargar_pib_sqlite(df):
    print("Cargando PIB a SQLite...")

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("DELETE FROM fact_macro_anual")

    for _, fila in df.iterrows():
        id_tiempo = obtener_o_crear_tiempo(conexion, int(fila["anio"]))

        cursor.execute(
            """
            INSERT INTO fact_macro_anual (
                id_tiempo,
                pib_real_musd,
                pib_percapita_nominal,
                variacion_pib_pct
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                id_tiempo,
                float(fila["pib_real_musd"]),
                float(fila["pib_percapita_nominal"]),
                float(fila["variacion_pib_pct"])
            )
        )

    conexion.commit()
    conexion.close()

    print("Carga PIB finalizada correctamente.")


def limpiar_petroleo():
    print("Leyendo archivo PETRÓLEO...")

    df = pd.read_excel(RUTA_PETROLEO)

    print("Filas originales petróleo:", len(df))

    # El archivo tiene una fila interna con los nombres reales de columnas.
    df = df.iloc[1:].copy()
    df.columns = ["fecha", "precio_petroleo_wti"]

    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["precio_petroleo_wti"] = pd.to_numeric(df["precio_petroleo_wti"], errors="coerce")

    df = df.dropna(subset=["fecha"]).copy()
    df["fecha"] = df["fecha"].dt.strftime("%Y-%m-%d")

    print("Filas limpias petróleo:", len(df))

    return df


def limpiar_riesgo_pais():
    print("Leyendo archivo RIESGO PAÍS...")

    df = pd.read_excel(RUTA_RIESGO)

    print("Filas originales riesgo país:", len(df))

    # El archivo tiene una fila interna con los nombres reales de columnas.
    df = df.iloc[1:].copy()
    df.columns = ["fecha", "riesgo_pais_pb"]

    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["riesgo_pais_pb"] = pd.to_numeric(df["riesgo_pais_pb"], errors="coerce")

    df = df.dropna(subset=["fecha"]).copy()
    df["fecha"] = df["fecha"].dt.strftime("%Y-%m-%d")

    print("Filas limpias riesgo país:", len(df))

    return df


def limpiar_indicadores_diarios():
    petroleo = limpiar_petroleo()
    riesgo = limpiar_riesgo_pais()

    df = pd.merge(
        petroleo,
        riesgo,
        on="fecha",
        how="outer"
    )

    df = df.sort_values("fecha").copy()

    RUTA_SALIDA_INDICADORES.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(RUTA_SALIDA_INDICADORES, index=False, encoding="utf-8-sig")

    print("Archivo limpio generado:", RUTA_SALIDA_INDICADORES)
    print("Filas limpias indicadores diarios:", len(df))

    return df


def cargar_indicadores_sqlite(df):
    print("Cargando indicadores diarios a SQLite...")

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("DELETE FROM fact_indicadores_diarios")

    for _, fila in df.iterrows():
        precio = None
        riesgo = None

        if not pd.isna(fila["precio_petroleo_wti"]):
            precio = float(fila["precio_petroleo_wti"])

        if not pd.isna(fila["riesgo_pais_pb"]):
            riesgo = int(fila["riesgo_pais_pb"])

        cursor.execute(
            """
            INSERT INTO fact_indicadores_diarios (
                fecha,
                precio_petroleo_wti,
                riesgo_pais_pb
            )
            VALUES (?, ?, ?)
            """,
            (
                fila["fecha"],
                precio,
                riesgo
            )
        )

    conexion.commit()
    conexion.close()

    print("Carga indicadores diarios finalizada correctamente.")


if __name__ == "__main__":
    datos_pib = limpiar_pib()
    cargar_pib_sqlite(datos_pib)

    datos_indicadores = limpiar_indicadores_diarios()
    cargar_indicadores_sqlite(datos_indicadores)