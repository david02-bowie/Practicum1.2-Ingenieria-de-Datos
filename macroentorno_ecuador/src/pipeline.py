from transform.mineduc import limpiar_mineduc, cargar_mineduc_sqlite
from transform.bce import limpiar_pib, cargar_pib_sqlite, limpiar_indicadores_diarios, cargar_indicadores_sqlite
from transform.vab import limpiar_vab, cargar_vab_sqlite
from transform.iee import limpiar_iee, cargar_iee_sqlite


def ejecutar_pipeline():
    print("========================================")
    print("INICIANDO PIPELINE MACROENTORNO ECUADOR")
    print("========================================")

    print("\n1. Procesando MINEDUC...")
    datos_mineduc = limpiar_mineduc()
    cargar_mineduc_sqlite(datos_mineduc)

    print("\n2. Procesando PIB...")
    datos_pib = limpiar_pib()
    cargar_pib_sqlite(datos_pib)

    print("\n3. Procesando petróleo y riesgo país...")
    datos_indicadores = limpiar_indicadores_diarios()
    cargar_indicadores_sqlite(datos_indicadores)

    print("\n4. Procesando VAB...")
    datos_vab = limpiar_vab()
    cargar_vab_sqlite(datos_vab)

    print("\n5. Procesando IEE...")
    datos_iee = limpiar_iee()
    cargar_iee_sqlite(datos_iee)

    print("\n========================================")
    print("PIPELINE FINALIZADO CORRECTAMENTE")
    print("========================================")


if __name__ == "__main__":
    ejecutar_pipeline()