import pandas as pd

archivo = "data/amie2023-2024.csv"

separadores = [";", ",", "\t", "|"]
codificaciones = ["latin1", "utf-8-sig", "utf-8"]

for encoding in codificaciones:
    for sep in separadores:
        print("\n==============================")
        print("Probando encoding:", encoding, " separador:", repr(sep))

        try:
            df = pd.read_csv(
                archivo,
                encoding=encoding,
                sep=sep,
                engine="python",
                nrows=5
            )

            print("Filas y columnas:", df.shape)
            print("Columnas encontradas:")
            print(list(df.columns))

            print("\nPrimeras filas:")
            print(df.head())

        except Exception as error:
            print("Error:", error)