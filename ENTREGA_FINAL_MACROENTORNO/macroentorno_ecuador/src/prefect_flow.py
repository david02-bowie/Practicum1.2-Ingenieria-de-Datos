from pathlib import Path
import subprocess
import sys
from prefect import flow, task


BASE_DIR = Path(__file__).resolve().parent.parent


@task(name="Revisar carpeta RPA")
def revisar_carpeta_rpa():
    carpeta_rpa = BASE_DIR / "data" / "rpa_inbox"

    if not carpeta_rpa.exists():
        raise FileNotFoundError("No existe la carpeta data/rpa_inbox")

    archivos = list(carpeta_rpa.glob("*"))

    if len(archivos) == 0:
        raise FileNotFoundError("No existen archivos en data/rpa_inbox")

    print("Archivos encontrados en RPA:")
    for archivo in archivos:
        print(f"- {archivo.name}")

    return len(archivos)


@task(name="Ejecutar pipeline completo")
def ejecutar_pipeline():
    resultado = subprocess.run(
        [sys.executable, "src/pipeline.py"],
        cwd=BASE_DIR,
        text=True,
        capture_output=True
    )

    print(resultado.stdout)

    if resultado.stderr:
        print(resultado.stderr)

    if resultado.returncode != 0:
        raise RuntimeError("El pipeline terminó con errores")

    return "Pipeline ejecutado correctamente"


@flow(name="Pipeline Macroentorno Ecuador")
def pipeline_macroentorno_ecuador():
    revisar_carpeta_rpa()
    ejecutar_pipeline()


if __name__ == "__main__":
    pipeline_macroentorno_ecuador()