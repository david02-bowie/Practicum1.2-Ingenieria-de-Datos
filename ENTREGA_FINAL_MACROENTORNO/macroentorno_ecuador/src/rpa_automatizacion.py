from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys


BASE_DIR = Path(__file__).resolve().parent.parent

RPA_INBOX = BASE_DIR / "data" / "rpa_inbox"
RPA_PROCESSED = BASE_DIR / "data" / "rpa_processed"
LOG_DIR = BASE_DIR / "data" / "logs"
LOG_FILE = LOG_DIR / "rpa_automatizacion.log"

BRONZE_BCE = BASE_DIR / "data" / "bronze" / "bce"
BRONZE_MINEDUC = BASE_DIR / "data" / "bronze" / "mineduc"

EXTENSIONES_PERMITIDAS = [".xlsx", ".xls", ".csv", ".sql"]


def preparar_carpetas():
    RPA_INBOX.mkdir(parents=True, exist_ok=True)
    RPA_PROCESSED.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    BRONZE_BCE.mkdir(parents=True, exist_ok=True)
    BRONZE_MINEDUC.mkdir(parents=True, exist_ok=True)


def escribir_log(mensaje):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{fecha}] {mensaje}"

    with open(LOG_FILE, "a", encoding="utf-8") as archivo:
        archivo.write(linea + "\n")

    print(linea)


def obtener_archivos_nuevos():
    archivos = []

    for archivo in RPA_INBOX.iterdir():
        if archivo.is_file() and archivo.suffix.lower() in EXTENSIONES_PERMITIDAS:
            archivos.append(archivo)

    return archivos


def decidir_destino(archivo):
    nombre = archivo.name.upper()

    if "MINEDUC" in nombre or archivo.suffix.lower() == ".csv":
        return BRONZE_MINEDUC / archivo.name

    return BRONZE_BCE / archivo.name


def ruta_unica(carpeta, nombre_archivo):
    ruta = carpeta / nombre_archivo

    if not ruta.exists():
        return ruta

    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
    nuevo_nombre = f"{ruta.stem}_{fecha}{ruta.suffix}"
    return carpeta / nuevo_nombre


def procesar_archivos_rpa():
    preparar_carpetas()

    escribir_log("Iniciando revisión de carpeta RPA.")

    archivos = obtener_archivos_nuevos()

    if len(archivos) == 0:
        escribir_log("No se encontraron archivos nuevos en data/rpa_inbox.")
        return

    escribir_log(f"Archivos nuevos detectados: {len(archivos)}")

    for archivo in archivos:
        destino_bronze = decidir_destino(archivo)

        shutil.copy2(archivo, destino_bronze)
        escribir_log(f"Archivo copiado a Bronze: {archivo.name} -> {destino_bronze}")

        destino_procesado = ruta_unica(RPA_PROCESSED, archivo.name)
        shutil.move(str(archivo), destino_procesado)
        escribir_log(f"Archivo movido a rpa_processed: {destino_procesado.name}")

    escribir_log("Ejecutando pipeline principal.")
    subprocess.run([sys.executable, "src/pipeline.py"], cwd=BASE_DIR, check=True)

    escribir_log("Actualizando Excel Gold para Power BI.")
    subprocess.run([sys.executable, "src/exportar_gold_excel.py"], cwd=BASE_DIR, check=True)

    escribir_log("Automatización RPA finalizada correctamente.")


if __name__ == "__main__":
    procesar_archivos_rpa()