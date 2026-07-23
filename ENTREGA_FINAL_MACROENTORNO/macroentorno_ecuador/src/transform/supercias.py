from pathlib import Path
import json
import sqlite3
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent.parent

RUTA_RPA = BASE_DIR / "data" / "rpa_inbox" / "tab_consolidado_export.sql"
RUTA_PROCESSED = BASE_DIR / "data" / "processed"
RUTA_DB = BASE_DIR / "db" / "macroentorno.db"

RUTA_SILVER = RUTA_PROCESSED / "silver_supercias_directorio.csv"


def separar_valores_sql(linea):
    inicio = linea.lower().find("values (")
    if inicio == -1:
        return []

    texto = linea[inicio + len("values ("):].strip()

    if texto.endswith(";"):
        texto = texto[:-1]

    if texto.endswith(")"):
        texto = texto[:-1]

    valores = []
    actual = []
    dentro_comilla = False
    profundidad_parentesis = 0

    i = 0
    while i < len(texto):
        caracter = texto[i]

        if caracter == "'":
            dentro_comilla = not dentro_comilla
            i += 1
            continue

        if not dentro_comilla:
            if caracter == "(":
                profundidad_parentesis += 1
            elif caracter == ")":
                profundidad_parentesis -= 1
            elif caracter == "," and profundidad_parentesis == 0:
                valores.append("".join(actual).strip())
                actual = []
                i += 1
                continue

        actual.append(caracter)
        i += 1

    if actual:
        valores.append("".join(actual).strip())

    return valores


def convertir_json(texto_json):
    try:
        datos = json.loads(texto_json)

        if isinstance(datos, str):
            datos = json.loads(datos)

        return datos

    except Exception:
        return None


def normalizar_texto(valor):
    if valor is None:
        return None

    return str(valor).strip().upper()


def limpiar_supercias():
    print("Procesando archivo RPA de Supercias...")

    RUTA_PROCESSED.mkdir(parents=True, exist_ok=True)

    registros = []
    lineas_leidas = 0
    lineas_directorio = 0
    errores_json = 0

    with open(RUTA_RPA, "r", encoding="utf-8", errors="ignore") as archivo:
        for linea in archivo:
            lineas_leidas += 1

            if "SUPERCIAS_DIRECTORIO" not in linea:
                continue

            lineas_directorio += 1

            valores = separar_valores_sql(linea)

            if len(valores) < 9:
                errores_json += 1
                continue

            datos_json = convertir_json(valores[6])

            if datos_json is None:
                errores_json += 1
                continue

            empresa = datos_json.get("empresa_metadata", {})
            ubicacion = datos_json.get("ubicacion", {})
            financiero = datos_json.get("financiero_ciiu", {})

            registros.append({
                "periodo_reporte": datos_json.get("periodo_reporte"),
                "ruc": empresa.get("ruc"),
                "expediente": empresa.get("expediente"),
                "nombre_empresa": empresa.get("nombre"),
                "situacion_legal": normalizar_texto(empresa.get("situacion_legal")),
                "fecha_constitucion": empresa.get("fecha_constitucion"),
                "tipo_compania": normalizar_texto(empresa.get("tipo_compania")),

                "pais": normalizar_texto(ubicacion.get("pais")),
                "region": normalizar_texto(ubicacion.get("region")),
                "provincia": normalizar_texto(ubicacion.get("provincia")),
                "canton": normalizar_texto(ubicacion.get("canton")),
                "ciudad": normalizar_texto(ubicacion.get("ciudad")),

                "representante": financiero.get("representante"),
                "cargo_representante": financiero.get("cargo"),
                "capital_suscrito": financiero.get("capital_suscrito"),
                "ciiu_nivel1": normalizar_texto(financiero.get("ciiu_nivel1")),
                "ciiu_nivel6": normalizar_texto(financiero.get("ciiu_nivel6")),
                "ultimo_balance_anio": financiero.get("ultimo_balance_anio"),

                "fuente": datos_json.get("fuente"),
                "ruta_logica": datos_json.get("ruta_logica")
            })

    df = pd.DataFrame(registros)

    if len(df) == 0:
        raise ValueError("No se extrajeron registros de Supercias. Revisa el archivo RPA.")

    df["capital_suscrito"] = pd.to_numeric(df["capital_suscrito"], errors="coerce")
    df["ultimo_balance_anio"] = pd.to_numeric(df["ultimo_balance_anio"], errors="coerce")

    df.to_csv(RUTA_SILVER, index=False, encoding="utf-8-sig")

    print(f"Líneas leídas: {lineas_leidas}")
    print(f"Líneas SUPERCIAS_DIRECTORIO: {lineas_directorio}")
    print(f"Registros extraídos: {len(df)}")
    print(f"Errores JSON o líneas no procesadas: {errores_json}")
    print(f"Archivo Silver generado: {RUTA_SILVER}")

    return df


def cargar_supercias_sqlite(df):
    print("Cargando Supercias en SQLite...")

    conexion = sqlite3.connect(RUTA_DB)

    df.to_sql(
        "fact_supercias_directorio",
        conexion,
        if_exists="replace",
        index=False
    )

    conexion.close()

    print("Tabla creada: fact_supercias_directorio")


def crear_vistas_gold_supercias():
    print("Creando vistas Gold de Supercias...")

    conexion = sqlite3.connect(RUTA_DB)
    cursor = conexion.cursor()

    cursor.executescript("""
    DROP VIEW IF EXISTS gold_empresas_provincia;

    CREATE VIEW gold_empresas_provincia AS
    SELECT
        provincia,
        COUNT(DISTINCT ruc) AS total_empresas,
        SUM(
            CASE
                WHEN situacion_legal = 'ACTIVA' THEN 1
                ELSE 0
            END
        ) AS empresas_activas,
        SUM(capital_suscrito) AS capital_suscrito_total
    FROM fact_supercias_directorio
    WHERE provincia IS NOT NULL
      AND provincia <> ''
    GROUP BY provincia
    ORDER BY empresas_activas DESC;


    DROP VIEW IF EXISTS gold_empresas_sector;

    CREATE VIEW gold_empresas_sector AS
    SELECT
        ciiu_nivel1,
        COUNT(DISTINCT ruc) AS total_empresas,
        SUM(
            CASE
                WHEN situacion_legal = 'ACTIVA' THEN 1
                ELSE 0
            END
        ) AS empresas_activas,
        SUM(capital_suscrito) AS capital_suscrito_total
    FROM fact_supercias_directorio
    WHERE ciiu_nivel1 IS NOT NULL
      AND ciiu_nivel1 <> ''
    GROUP BY ciiu_nivel1
    ORDER BY empresas_activas DESC;


    DROP VIEW IF EXISTS gold_bachilleres_empresas_provincia;

    CREATE VIEW gold_bachilleres_empresas_provincia AS
    SELECT
        b.provincia,
        SUM(b.total_bachilleres) AS total_bachilleres,
        COALESCE(e.empresas_activas, 0) AS empresas_activas,
        COALESCE(e.total_empresas, 0) AS total_empresas,
        COALESCE(e.capital_suscrito_total, 0) AS capital_suscrito_total
    FROM gold_bachilleres_provincia b
    LEFT JOIN gold_empresas_provincia e
        ON UPPER(TRIM(b.provincia)) = UPPER(TRIM(e.provincia))
    GROUP BY
        b.provincia,
        e.empresas_activas,
        e.total_empresas,
        e.capital_suscrito_total
    ORDER BY total_bachilleres DESC;
    """)

    conexion.commit()
    conexion.close()

    print("Vistas creadas:")
    print("- gold_empresas_provincia")
    print("- gold_empresas_sector")
    print("- gold_bachilleres_empresas_provincia")


if __name__ == "__main__":
    datos = limpiar_supercias()
    cargar_supercias_sqlite(datos)
    crear_vistas_gold_supercias()