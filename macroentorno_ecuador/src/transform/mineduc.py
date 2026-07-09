from pathlib import Path
import sqlite3
import pandas as pd


RUTA_MINEDUC = Path("data/bronze/mineduc/2_MINEDUC_RegistrosAdministrativos_2023-2024Inicio (1).csv")
RUTA_SALIDA = Path("data/processed/silver_mineduc_bachillerato.csv")
DB_PATH = "db/macroentorno.db"


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


def limpiar_mineduc():
    print("Leyendo archivo MINEDUC...")

    df = pd.read_csv(RUTA_MINEDUC, sep=";", encoding="latin-1")

    print("Filas originales:", len(df))

    columnas_necesarias = [
        "Año lectivo",
        "AMIE",
        "Nombre_Institución",
        "Provincia",
        "Cod_Provincia",
        "Cantón",
        "Cod_Cantón",
        "Nivel Educación",
        "Sostenimiento",
        "EstudiantesMasculinoTercerAñoBACH",
        "EstudiantesFemeninoTercerAñoBACH"
    ]

    df = df[columnas_necesarias].copy()

    df["provincia"] = df["Provincia"].apply(normalizar_texto)
    df["canton"] = df["Cantón"].apply(normalizar_texto)

    df["masculino_tercero_bach"] = pd.to_numeric(
        df["EstudiantesMasculinoTercerAñoBACH"],
        errors="coerce"
    ).fillna(0).astype(int)

    df["femenino_tercero_bach"] = pd.to_numeric(
        df["EstudiantesFemeninoTercerAñoBACH"],
        errors="coerce"
    ).fillna(0).astype(int)

    df["total_bachilleres_3ro"] = (
        df["masculino_tercero_bach"] + df["femenino_tercero_bach"]
    )

    df = df[df["total_bachilleres_3ro"] > 0].copy()

    df_limpio = pd.DataFrame({
        "anio_lectivo": df["Año lectivo"],
        "amie": df["AMIE"],
        "nombre_institucion": df["Nombre_Institución"],
        "provincia": df["provincia"],
        "cod_provincia": pd.to_numeric(df["Cod_Provincia"], errors="coerce"),
        "canton": df["canton"],
        "cod_canton": pd.to_numeric(df["Cod_Cantón"], errors="coerce"),
        "nivel_educacion": df["Nivel Educación"],
        "sostenimiento": df["Sostenimiento"],
        "total_estudiantes": df["total_bachilleres_3ro"]
    })

    RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    df_limpio.to_csv(RUTA_SALIDA, index=False, encoding="utf-8-sig")

    print("Filas limpias:", len(df_limpio))
    print("Archivo limpio generado:", RUTA_SALIDA)

    return df_limpio


def cargar_mineduc_sqlite(df_limpio):
    print("Cargando MINEDUC a SQLite...")

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("DELETE FROM fact_mineduc_bachillerato")

    for _, fila in df_limpio.iterrows():
        id_geo = obtener_o_crear_geografia(
            conexion,
            fila["provincia"],
            None if pd.isna(fila["cod_provincia"]) else int(fila["cod_provincia"]),
            fila["canton"],
            None if pd.isna(fila["cod_canton"]) else int(fila["cod_canton"])
        )

        cursor.execute(
            """
            INSERT INTO fact_mineduc_bachillerato (
                id_geo,
                anio_lectivo,
                amie,
                nombre_institucion,
                nivel_educacion,
                sostenimiento,
                total_estudiantes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                id_geo,
                fila["anio_lectivo"],
                fila["amie"],
                fila["nombre_institucion"],
                fila["nivel_educacion"],
                fila["sostenimiento"],
                int(fila["total_estudiantes"])
            )
        )

    conexion.commit()
    conexion.close()

    print("Carga MINEDUC finalizada correctamente.")


if __name__ == "__main__":
    datos_limpios = limpiar_mineduc()
    cargar_mineduc_sqlite(datos_limpios)