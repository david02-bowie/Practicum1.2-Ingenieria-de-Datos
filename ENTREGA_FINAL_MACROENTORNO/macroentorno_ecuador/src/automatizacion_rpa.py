from pathlib import Path
from datetime import datetime
import json
import subprocess
import sys


BASE_DIR = Path(__file__).resolve().parent.parent

RPA_DIR = BASE_DIR / "data" / "rpa_inbox"
LOG_DIR = BASE_DIR / "data" / "logs"
LOG_FILE = LOG_DIR / "automatizacion_rpa.log"
ESTADO_FILE = LOG_DIR / "estado_rpa.json"

EXTENSIONES_VALIDAS = [".sql", ".csv", ".xlsx", ".xls"]


def escribir_log(mensaje):
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{fecha}] {mensaje}"

    with open(LOG_FILE, "a", encoding="utf-8") as archivo:
        archivo.write(linea + "\n")

    print(linea)


def obtener_estado_archivos():
    estado = {}

    if not RPA_DIR.exists():
        RPA_DIR.mkdir(parents=True, exist_ok=True)

    for archivo in RPA_DIR.iterdir():
        if archivo.is_file() and archivo.suffix.lower() in EXTENSIONES_VALIDAS:
            info = archivo.stat()

            estado[archivo.name] = {
                "tamano": info.st_size,
                "modificado": int(info.st_mtime)
            }

    return estado


def cargar_estado_anterior():
    if not ESTADO_FILE.exists():
        return {}

    with open(ESTADO_FILE, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def guardar_estado(estado):
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    with open(ESTADO_FILE, "w", encoding="utf-8") as archivo:
        json.dump(estado, archivo, indent=4, ensure_ascii=False)


def ejecutar_pipeline():
    escribir_log("Cambios detectados en carpeta RPA. Ejecutando pipeline completo...")

    resultado = subprocess.run(
        [sys.executable, "src/pipeline.py"],
        cwd=BASE_DIR,
        text=True,
        capture_output=True
    )

    with open(LOG_FILE, "a", encoding="utf-8") as archivo:
        archivo.write("\n--- SALIDA PIPELINE ---\n")
        archivo.write(resultado.stdout)
        archivo.write("\n--- ERRORES PIPELINE ---\n")
        archivo.write(resultado.stderr)
        archivo.write("\n--- FIN PIPELINE ---\n")

    if resultado.returncode != 0:
        escribir_log("ERROR: El pipeline terminó con errores.")
        raise RuntimeError("El pipeline falló. Revisar data/logs/automatizacion_rpa.log")

    escribir_log("Pipeline ejecutado correctamente.")


def revisar_rpa():
    escribir_log("Revisando carpeta RPA...")

    estado_actual = obtener_estado_archivos()
    estado_anterior = cargar_estado_anterior()

    if estado_actual == estado_anterior:
        escribir_log("No se detectaron archivos nuevos o modificados.")
        return

    escribir_log("Se detectaron cambios en archivos RPA.")
    escribir_log(f"Archivos detectados: {list(estado_actual.keys())}")

    ejecutar_pipeline()
    guardar_estado(estado_actual)

    escribir_log("Automatización RPA finalizada correctamente.")


if __name__ == "__main__":
    revisar_rpa()