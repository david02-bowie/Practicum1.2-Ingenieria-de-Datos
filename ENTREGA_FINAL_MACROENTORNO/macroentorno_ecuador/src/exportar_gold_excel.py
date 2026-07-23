import sqlite3
from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent

RUTA_DB = BASE_DIR / "db" / "macroentorno.db"
RUTA_GOLD = BASE_DIR / "data" / "gold"
RUTA_EXCEL = RUTA_GOLD / "macroentorno_gold_powerbi.xlsx"

RUTA_GOLD.mkdir(parents=True, exist_ok=True)


def exportar_gold_excel():
    print("========================================")
    print("EXPORTANDO VISTAS GOLD A EXCEL")
    print("========================================")

    vistas = {
        "gold_pib_tendencia": "PIB",
        "gold_petroleo_30dias": "Petroleo",
        "gold_vab_provincia": "VAB",
        "gold_bachilleres_provincia": "Bachilleres",

        "gold_empresas_provincia": "EmpresasProvincia",
        "gold_empresas_sector": "EmpresasSector",
        "gold_bachilleres_empresas_provincia": "BachilleresEmpresas"
    }

    conexion = sqlite3.connect(RUTA_DB)

    with pd.ExcelWriter(RUTA_EXCEL, engine="openpyxl") as writer:
        for vista, hoja in vistas.items():
            print(f"\nExportando {vista}...")

            consulta = f"SELECT * FROM {vista}"
            df = pd.read_sql_query(consulta, conexion)

            df.to_excel(writer, sheet_name=hoja, index=False)

            print(f"Hoja generada: {hoja}")
            print(f"Filas exportadas: {len(df)}")

    conexion.close()

    print("\n========================================")
    print("EXCEL GOLD GENERADO CORRECTAMENTE")
    print("========================================")
    print(f"Archivo generado: {RUTA_EXCEL}")


if __name__ == "__main__":
    exportar_gold_excel()