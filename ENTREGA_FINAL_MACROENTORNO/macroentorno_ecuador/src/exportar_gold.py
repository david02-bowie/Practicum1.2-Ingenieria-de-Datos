import sqlite3
from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent

RUTA_DB = BASE_DIR / "db" / "macroentorno.db"
RUTA_GOLD = BASE_DIR / "data" / "gold"

RUTA_GOLD.mkdir(parents=True, exist_ok=True)


def exportar_vistas_gold():
    print("========================================")
    print("EXPORTANDO VISTAS GOLD A CSV")
    print("========================================")

    vistas = [
        "gold_pib_tendencia",
        "gold_petroleo_30dias",
        "gold_vab_provincia",
        "gold_bachilleres_provincia"
    ]

    conexion = sqlite3.connect(RUTA_DB)

    for vista in vistas:
        print(f"\nExportando {vista}...")

        consulta = f"SELECT * FROM {vista}"
        df = pd.read_sql_query(consulta, conexion)

        ruta_salida = RUTA_GOLD / f"{vista}.csv"
        df.to_csv(ruta_salida, index=False, encoding="utf-8-sig")

        print(f"Archivo generado: {ruta_salida}")
        print(f"Filas exportadas: {len(df)}")

    conexion.close()

    print("\n========================================")
    print("EXPORTACIÓN GOLD FINALIZADA CORRECTAMENTE")
    print("========================================")


if __name__ == "__main__":
    exportar_vistas_gold()