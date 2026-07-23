from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
RPA_DIR = BASE_DIR / "data" / "rpa_inbox"

PALABRAS = ["PROVINCIA", "CANTON", "CANTÓN", "RUC", "SITUACION_LEGAL", "NOMBRE"]


def mostrar_contexto():
    archivos = list(RPA_DIR.glob("*.sql"))

    print("Archivos encontrados:")
    for archivo in archivos:
        print("-", archivo.name)

    print("\nBuscando líneas donde aparezcan campos importantes...\n")

    encontrados = 0

    for archivo in archivos:
        print(f"\n===== Revisando {archivo.name} =====")

        with open(archivo, "r", encoding="utf-8", errors="ignore") as entrada:
            for numero_linea, linea in enumerate(entrada, start=1):
                linea_mayuscula = linea.upper()

                if any(palabra in linea_mayuscula for palabra in PALABRAS):
                    texto = linea.strip()

                    print(f"\nLínea {numero_linea}:")
                    print(texto[:1500])

                    encontrados += 1

                    if encontrados >= 8:
                        return

    if encontrados == 0:
        print("No se encontraron líneas con esos campos.")


if __name__ == "__main__":
    mostrar_contexto()