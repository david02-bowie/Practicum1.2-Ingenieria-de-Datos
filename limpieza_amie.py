import pandas as pd
import sqlite3
import glob
import re
import unicodedata
import os

# Crear carpetas por si no existen
os.makedirs("salida", exist_ok=True)
os.makedirs("db", exist_ok=True)

# Buscar archivos CSV
archivos = sorted(glob.glob("data/*.csv"))

print("ARCHIVOS ENCONTRADOS:")
for archivo in archivos:
    print(archivo)

columnas_base = [
    "Año lectivo",
    "AMIE",
    "Nombre_Institución",
    "Zona",
    "Provincia",
    "Cantón",
    "Parroquia",
    "Sostenimiento",
    "Área"
]


def quitar_tildes(texto):
    texto = str(texto)
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join([c for c in texto if not unicodedata.combining(c)])
    return texto


def limpiar_texto_columna(texto):
    texto = str(texto).replace("\ufeff", "").strip()
    texto = quitar_tildes(texto).lower()
    texto = texto.replace("_", " ")
    texto = " ".join(texto.split())
    return texto


def normalizar_nombre_columna(nombre):
    nombre = quitar_tildes(str(nombre)).lower()
    nombre = nombre.replace(" ", "")
    nombre = nombre.replace("-", "")
    nombre = nombre.replace("_", "")
    nombre = nombre.replace(".", "")
    nombre = nombre.replace("/", "")
    nombre = nombre.replace("(", "")
    nombre = nombre.replace(")", "")
    return nombre


def convertir_numero(valor):
    if pd.isna(valor):
        return 0

    texto = str(valor).strip()

    if texto == "" or texto.lower() in ["nan", "none", "null", "-", "--"]:
        return 0

    texto = texto.replace("\u00a0", "")
    texto = texto.replace(" ", "")

    # Dejar solo números, coma, punto y signo negativo
    texto = re.sub(r"[^0-9,.\-]", "", texto)

    if texto == "" or texto == "-":
        return 0

    # Caso: 1.234,56
    if "," in texto and "." in texto:
        if texto.rfind(",") > texto.rfind("."):
            texto = texto.replace(".", "")
            texto = texto.replace(",", ".")
        else:
            texto = texto.replace(",", "")

    # Caso: 1,234 o 12,5
    elif "," in texto:
        partes = texto.split(",")
        if len(partes[-1]) == 3 and len(partes) > 1:
            texto = texto.replace(",", "")
        else:
            texto = texto.replace(",", ".")

    # Caso: 1.234
    elif "." in texto:
        partes = texto.split(".")
        if len(partes[-1]) == 3 and len(partes) > 1:
            texto = texto.replace(".", "")

    try:
        return float(texto)
    except ValueError:
        return 0


def estandarizar_columnas(df):
    nuevas_columnas = {}

    for columna in df.columns:
        original = str(columna).replace("\ufeff", "").strip()
        comparacion = limpiar_texto_columna(original)

        if comparacion == "ano lectivo":
            nuevas_columnas[columna] = "Año lectivo"
        elif comparacion == "amie":
            nuevas_columnas[columna] = "AMIE"
        elif comparacion in ["nombre institucion", "nombre de institucion"]:
            nuevas_columnas[columna] = "Nombre_Institución"
        elif comparacion == "zona":
            nuevas_columnas[columna] = "Zona"
        elif comparacion == "provincia":
            nuevas_columnas[columna] = "Provincia"
        elif comparacion == "canton":
            nuevas_columnas[columna] = "Cantón"
        elif comparacion == "parroquia":
            nuevas_columnas[columna] = "Parroquia"
        elif comparacion == "sostenimiento":
            nuevas_columnas[columna] = "Sostenimiento"
        elif comparacion == "area":
            nuevas_columnas[columna] = "Área"
        else:
            nuevas_columnas[columna] = original

    df = df.rename(columns=nuevas_columnas)
    df = df.loc[:, ~df.columns.duplicated()]

    return df


def leer_csv_con_encabezado_real(archivo):
    codificaciones = ["utf-8-sig", "latin1", "utf-8"]
    separadores = [";", ",", "\t", "|"]

    mejor_df = None
    mejor_puntaje = -1

    for encoding in codificaciones:
        for separador in separadores:
            try:
                bruto = pd.read_csv(
                    archivo,
                    encoding=encoding,
                    sep=separador,
                    engine="python",
                    header=None,
                    dtype=str
                )

                fila_encabezado = None

                for indice in range(min(50, len(bruto))):
                    fila = bruto.iloc[indice].astype(str).tolist()
                    fila_limpia = [limpiar_texto_columna(valor) for valor in fila]

                    tiene_amie = "amie" in fila_limpia
                    tiene_provincia = "provincia" in fila_limpia
                    tiene_anio = "ano lectivo" in fila_limpia

                    if tiene_amie and tiene_provincia and tiene_anio:
                        fila_encabezado = indice
                        break

                if fila_encabezado is None:
                    continue

                columnas = bruto.iloc[fila_encabezado].tolist()
                datos = bruto.iloc[fila_encabezado + 1:].copy()
                datos.columns = columnas

                datos = estandarizar_columnas(datos)

                puntaje = 0
                for columna in columnas_base:
                    if columna in datos.columns:
                        puntaje += 1

                if puntaje > mejor_puntaje:
                    mejor_puntaje = puntaje
                    mejor_df = datos

            except Exception:
                pass

    return mejor_df


def calcular_matricula_total(df_temp):
    columnas_normalizadas = {}

    for columna in df_temp.columns:
        columnas_normalizadas[normalizar_nombre_columna(columna)] = columna

    columna_total_estudiantes = None

    posibles_columnas_total = [
        "totalestudiantes",
        "totalalumnos",
        "estudiantestotal",
        "matriculatotal",
        "totalmatricula",
        "totalmatriculados",
        "totalgeneral"
    ]

    for posible in posibles_columnas_total:
        if posible in columnas_normalizadas:
            columna_total_estudiantes = columnas_normalizadas[posible]
            break

    if columna_total_estudiantes is not None:
        df_temp["Matricula_Total"] = df_temp[columna_total_estudiantes].apply(convertir_numero)

        print("Matrícula tomada desde columna resumen:", columna_total_estudiantes)
        return df_temp

    columna_femenino = None
    columna_masculino = None

    posibles_femenino = [
        "estudiantesfemenino",
        "totalestudiantesfemenino",
        "alumnosfemenino",
        "totalalumnosfemenino",
        "femenino"
    ]

    posibles_masculino = [
        "estudiantesmasculino",
        "totalestudiantesmasculino",
        "alumnosmasculino",
        "totalalumnosmasculino",
        "masculino"
    ]

    for posible in posibles_femenino:
        if posible in columnas_normalizadas:
            columna_femenino = columnas_normalizadas[posible]
            break

    for posible in posibles_masculino:
        if posible in columnas_normalizadas:
            columna_masculino = columnas_normalizadas[posible]
            break

    if columna_femenino is not None and columna_masculino is not None:
        df_temp[columna_femenino] = df_temp[columna_femenino].apply(convertir_numero)
        df_temp[columna_masculino] = df_temp[columna_masculino].apply(convertir_numero)

        df_temp["Matricula_Total"] = df_temp[columna_femenino] + df_temp[columna_masculino]

        print("Matrícula tomada desde columnas resumen por género:")
        print(columna_femenino)
        print(columna_masculino)

        return df_temp

    niveles_validos = [
        "menor3anos",
        "3anos",
        "4anos",
        "primeranoegb",
        "segundoanoegb",
        "terceranoegb",
        "cuartoanoegb",
        "quintoanoegb",
        "sextoanoegb",
        "septimoanoegb",
        "octavoanoegb",
        "novenoanoegb",
        "decimoanoegb",
        "primeranobach",
        "segundoanobach",
        "terceranobach",
        "noescolarizado",
        "desconoce",
        "postbasico",
        "alfabetizacion",
        "artesanal",
        "basicoacelerado"
    ]

    columnas_matricula = []

    for columna in df_temp.columns:
        columna_normalizada = normalizar_nombre_columna(columna)

        if columna_normalizada.startswith("estudiantesfemenino"):
            nivel = columna_normalizada.replace("estudiantesfemenino", "", 1)
            if nivel in niveles_validos:
                columnas_matricula.append(columna)

        if columna_normalizada.startswith("estudiantesmasculino"):
            nivel = columna_normalizada.replace("estudiantesmasculino", "", 1)
            if nivel in niveles_validos:
                columnas_matricula.append(columna)

    columnas_matricula = list(dict.fromkeys(columnas_matricula))

    if len(columnas_matricula) > 0:
        datos_matricula = df_temp[columnas_matricula].applymap(convertir_numero)

        df_temp["Matricula_Total"] = datos_matricula.sum(axis=1)

        print("Matrícula calculada sumando columnas por nivel.")
        print("Cantidad de columnas usadas:", len(columnas_matricula))
    else:
        df_temp["Matricula_Total"] = 0
        print("No se encontraron columnas de matrícula.")

    return df_temp


def normalizar_anio_lectivo(valor):
    texto = str(valor).strip()

    if texto == "" or texto.lower() == "nan":
        return ""

    texto = texto.replace("–", "-")
    texto = texto.replace("_", "-")

    coincidencia = re.search(r"(\d{4})\s*-\s*(\d{4})", texto)

    if coincidencia:
        anio_inicio = coincidencia.group(1)
        anio_fin = coincidencia.group(2)
        return anio_inicio + "-" + anio_fin + " Fin"

    return texto


lista_df = []

for archivo in archivos:
    print("\nLeyendo archivo:", archivo)

    df_temp = leer_csv_con_encabezado_real(archivo)

    if df_temp is None:
        print("No se pudo leer correctamente:", archivo)
        continue

    # Eliminar columnas basura
    columnas_validas = []

    for columna in df_temp.columns:
        nombre = str(columna)
        if not nombre.startswith("Unnamed") and nombre != "nan":
            columnas_validas.append(columna)

    df_temp = df_temp[columnas_validas]

    # Si no aparece el año lectivo, tomarlo desde el nombre del archivo
    if "Año lectivo" not in df_temp.columns:
        coincidencia = re.search(r"amie(\d{4}-\d{4})", archivo)
        if coincidencia:
            df_temp["Año lectivo"] = coincidencia.group(1) + " Fin"

    # Limpiar espacios en columnas de texto
    for columna in df_temp.columns:
        if df_temp[columna].dtype == "object":
            df_temp[columna] = df_temp[columna].astype(str).str.strip()

    # Normalizar Año lectivo
    if "Año lectivo" in df_temp.columns:
        df_temp["Año lectivo"] = df_temp["Año lectivo"].apply(normalizar_anio_lectivo)

    # Crear Matricula_Total
    df_temp = calcular_matricula_total(df_temp)

    # Garantizar que existan las columnas base
    for columna in columnas_base:
        if columna not in df_temp.columns:
            df_temp[columna] = ""

    # Dejar solo columnas necesarias para el dashboard
    df_temp = df_temp[columnas_base + ["Matricula_Total"]]

    print("Filas leídas:", len(df_temp))
    print("Años encontrados:", df_temp["Año lectivo"].drop_duplicates().tolist())

    lista_df.append(df_temp)


if len(lista_df) == 0:
    print("No se pudo cargar ningún archivo CSV.")
    raise SystemExit


# Unir todos los años
df = pd.concat(lista_df, ignore_index=True)

print("\nDATASET UNIFICADO CORRECTAMENTE")
print("Filas y columnas originales:", df.shape)


# Limpieza final de texto
for columna in df.columns:
    if df[columna].dtype == "object":
        df[columna] = df[columna].replace("nan", "")
        df[columna] = df[columna].replace("None", "")
        df[columna] = df[columna].str.strip()


# Eliminar filas sin datos clave
df = df.dropna(subset=["Año lectivo", "AMIE", "Provincia"])

df = df[df["Año lectivo"] != ""]
df = df[df["AMIE"] != ""]
df = df[df["Provincia"] != ""]


# Normalizar textos
df["AMIE"] = df["AMIE"].astype(str).str.strip()
df["Año lectivo"] = df["Año lectivo"].astype(str).str.strip()
df["Provincia"] = df["Provincia"].astype(str).str.strip().str.upper()
df["Cantón"] = df["Cantón"].astype(str).str.strip().str.upper()
df["Parroquia"] = df["Parroquia"].astype(str).str.strip().str.upper()
df["Sostenimiento"] = df["Sostenimiento"].astype(str).str.strip().str.upper()
df["Área"] = df["Área"].astype(str).str.strip().str.upper()
df["Zona"] = df["Zona"].astype(str).str.strip()
df["Nombre_Institución"] = df["Nombre_Institución"].astype(str).str.strip()


# Asegurar que Matricula_Total sea numérica
df["Matricula_Total"] = df["Matricula_Total"].apply(convertir_numero).fillna(0)


# Revisar duplicados exactos
duplicados = df.duplicated().sum()
print("Filas duplicadas exactas encontradas:", duplicados)

df = df.drop_duplicates()


# IMPORTANTE:
# Convertir matrícula a entero para que Power BI no lea valores como 1054187.0 y los convierta mal.
df["Matricula_Total"] = df["Matricula_Total"].round(0).astype(int)


# Revisar nulos
nulos = df.isnull().sum()
print("\nColumnas con valores nulos:")
print(nulos[nulos > 0])


# Guardar listado de columnas
with open("salida/columnas_amie.txt", "w", encoding="utf-8") as archivo_columnas:
    for columna in df.columns:
        archivo_columnas.write(columna + "\n")


# Guardar CSV limpio
df.to_csv("salida/amie_limpio.csv", index=False, encoding="utf-8-sig")

print("\nLIMPIEZA FINALIZADA")
print("Filas y columnas finales:", df.shape)
print("Archivo limpio guardado en: salida/amie_limpio.csv")
print("Listado de columnas guardado en: salida/columnas_amie.txt")


# Guardar en SQLite
conexion = sqlite3.connect("db/amie.db")

df.to_sql("amie", conexion, if_exists="replace", index=False)

consulta = pd.read_sql_query(
    "SELECT COUNT(*) AS total_registros FROM amie",
    conexion
)

print("\nBASE DE DATOS CREADA CORRECTAMENTE")
print(consulta)


# Verificación rápida por año
consulta_anios = pd.read_sql_query(
    '''
    SELECT "Año lectivo", COUNT(DISTINCT "AMIE") AS total_instituciones
    FROM amie
    GROUP BY "Año lectivo"
    ORDER BY "Año lectivo";
    ''',
    conexion
)

print("\nINSTITUCIONES POR AÑO:")
print(consulta_anios)


# Verificación rápida de matrícula 2023-2024
consulta_matricula = pd.read_sql_query(
    '''
    SELECT "Provincia", SUM("Matricula_Total") AS matricula_total
    FROM amie
    WHERE "Año lectivo" = '2023-2024 Fin'
    GROUP BY "Provincia"
    ORDER BY matricula_total DESC;
    ''',
    conexion
)

print("\nMATRÍCULA POR PROVINCIA EN 2023-2024:")
print(consulta_matricula.head(15))


consulta_total_nacional = pd.read_sql_query(
    '''
    SELECT SUM("Matricula_Total") AS total_nacional
    FROM amie
    WHERE "Año lectivo" = '2023-2024 Fin';
    ''',
    conexion
)

print("\nTOTAL NACIONAL 2023-2024:")
print(consulta_total_nacional)


conexion.close()