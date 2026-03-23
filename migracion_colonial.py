import pandas as pd
import matplotlib.pyplot as plt

pais_colono_idioma = pd.read_csv("fuentes_de_datos/idiomas_coloniales.csv")
migraciones = pd.read_csv("fuentes_de_datos/migras_90_24.csv")
migraciones = migraciones[migraciones["region_orig_EN"]=="Africa"]



# migraciones a las colonias de los paises colonos

df = migraciones.merge(pais_colono_idioma, left_on="iso3_orig", right_on="codigo_pais")
año = 1990
migras_acolonos= []
destino_principal = []
años = [1990,1995,2000,2005,2010,2015,2020,2024]
for año in años:
    resultado = df[(df["iso3_des"] == df["codigo_colonia_de"]) & (df["año"] == año)]    
    complemento = df[(df["iso3_des"] != df["codigo_colonia_de"]) & (df["año"] == año)]
    
    df_anio = df[df["año"] == año].copy()
    # principales_destinos = df_anio[df_anio["migrantes"] ==df_anio.groupby("iso3_orig")["migrantes"].transform("max")][["iso3_orig","iso3_des","codigo_colonia_de","migrantes"]]

    idx = df_anio.groupby("iso3_orig")["migrantes"].idxmax()
    principales_destinos = df_anio.loc[idx, ["iso3_orig","iso3_des","codigo_colonia_de","migrantes"]]

    es_metropoli = principales_destinos["iso3_des"] == principales_destinos["codigo_colonia_de"]

    destino_principal.append((es_metropoli.sum(), (~es_metropoli).sum()))

    print("Principal destino = metrópoli:", es_metropoli.sum())
    print("Principal destino ≠ metrópoli:", (~es_metropoli).sum())
    print("Total países:", len(principales_destinos))

    # principales_destinos = df[(df["migrantes"] ==df.groupby("iso3_orig")["migrantes"].transform("max")) & (df["año"] == año)][["iso3_orig","iso3_des","codigo_colonia_de","migrantes"]]
    # print((principales_destinos["iso3_des"] == principales_destinos["codigo_colonia_de"]).sum(),
    #       (principales_destinos["iso3_des"] != principales_destinos["codigo_colonia_de"]).sum())
    # print(resultado.shape, complemento.shape, df[df["año"] == año].groupby("iso3_orig"))

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
    a =  int(resultados_agrupados["migrantes"].sum())
    b = int(complemento_agrupados["migrantes"].sum())
    migras_acolonos.append((a, b))
    relacion = resultados_agrupados.merge(complemento_agrupados, left_on="iso3_orig", right_on="iso3_orig", how="outer", suffixes=("_colonos", "_otros")).fillna(0)
    print(a,b,a/(a+b))

print(migras_acolonos)
fig = plt.figure(figsize=(20,12))
plt.bar(años, [x[0] for x in destino_principal], label="a pais soberano", bottom=[x[1] for x in destino_principal])
plt.bar(años, [x[1] for x in destino_principal], label="otros destinos")
plt.xlabel("Año")
plt.ylabel("Número de Paises")
# plt.title("Migraciones a Paises colonizadores vs. Otros Destinos")
plt.legend()
plt.savefig(
    f"resultados/Migraciones a paises soberanos.png",
    dpi=300,                 # calidad alta para impresión
    bbox_inches="tight",     # elimina márgenes blancos
    pad_inches=0.1,
    facecolor=fig.get_facecolor()
)
plt.show()

fig = plt.figure(figsize=(20,12))
plt.bar(años, [x[0] for x in migras_acolonos], label="a pais soberano", bottom=[x[1] for x in migras_acolonos])
plt.bar(años, [x[1] for x in migras_acolonos], label="otros destinos")
plt.xlabel("Año")
plt.ylabel("Número de Migrantes")
# plt.title("Migraciones a Paises colonizadores vs. Otros Destinos")
plt.legend()
plt.savefig(
    f"resultados/Migrantes a paises soberanos.png",
    dpi=300,                 # calidad alta para impresión
    bbox_inches="tight",     # elimina márgenes blancos
    pad_inches=0.1,
    facecolor=fig.get_facecolor()
)
plt.show()