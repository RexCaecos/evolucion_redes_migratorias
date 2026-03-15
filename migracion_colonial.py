import pandas as pd
import matplotlib.pyplot as plt

pais_colono_idioma = pd.read_csv("fuentes_de_datos/idiomas_coloniales.csv")
migraciones = pd.read_csv("fuentes_de_datos/migras_90_24.csv")


# migraciones a las colonias de los paises colonos

df = migraciones.merge(pais_colono_idioma, left_on="iso3_orig", right_on="codigo_pais")
año = 1990
migras_acolonos= []
migras_acolonias = []
años = [1990,1995,2000,2005,2010,2015,2020,2024]
for año in años:
    resultado = df[(df["iso3_des"] == df["codigo_colonia_de"]) & (df["año"] == año)]
    complemento = df[(df["iso3_des"] != df["codigo_colonia_de"]) & (df["año"] == año)]

    resultados_agrupados = (
        resultado
        .groupby(["iso3_orig"], as_index=False)["migrantes"]
        .sum()
    )

    complemento_agrupados = (
        complemento
        .groupby(["iso3_orig"], as_index=False)["migrantes"]
        .sum()
    )
    migras_acolonos.append(( resultados_agrupados["migrantes"].sum(), complemento_agrupados["migrantes"].sum()))
    relacion = resultados_agrupados.merge(complemento_agrupados, left_on="iso3_orig", right_on="iso3_orig", how="outer", suffixes=("_colonos", "_otros")).fillna(0)
    print(relacion.head())

print(migras_acolonos)
fig = plt.figure(figsize=(20,12))
plt.bar(años, [x[0] for x in migras_acolonos], label="colonial", bottom=[x[1] for x in migras_acolonos])
plt.bar(años, [x[1] for x in migras_acolonos], label="no colonial")
plt.xlabel("Año")
plt.ylabel("Número de Migrantes")
plt.title("Migraciones a Paises colonizadores vs. Otros Destinos")
plt.legend()
plt.savefig(
    f"resultados/Migraciones a Paises colonizadores.png",
    dpi=300,                 # calidad alta para impresión
    bbox_inches="tight",     # elimina márgenes blancos
    pad_inches=0.1,
    facecolor=fig.get_facecolor()
)
plt.show()

