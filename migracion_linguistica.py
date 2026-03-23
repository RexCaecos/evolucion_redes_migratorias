import pandas as pd
import matplotlib.pyplot as plt

pais_colono_idioma = pd.read_csv("fuentes_de_datos/idiomas_coloniales.csv")
migraciones = pd.read_csv("fuentes_de_datos/migras_90_24.csv")
migraciones = migraciones[migraciones["region_orig_EN"]=="Africa"]
migraciones = migraciones[migraciones["iso3_orig"].isin(pais_colono_idioma["codigo_pais"])]


# migraciones a las colonias de los paises colonos

df = migraciones.merge(pais_colono_idioma, left_on="iso3_orig", right_on="codigo_pais")
df = df.merge(pais_colono_idioma, left_on="iso3_des", right_on="codigo_pais", suffixes=("_origen", "_destino"), how="left")
año = 1990
migras_acolonos= []
migras_intra_colonia = []
años = [1990,1995,2000,2005,2010,2015,2020,2024]
for año in años:
    intra_col = df[(df["codigo_colonia_de_origen"] == df["codigo_colonia_de_destino"])& (df["año"] == año)]
    total_colo = df[df["año"] == año]
    resultado   = df[ ((df["ingles_origen"] == df["ingles_destino"]) | (df["frances_origen"] == df["frances_destino"]) | (df["portugues_origen"] == df["portugues_destino"]) | (df["aleman_origen"] == df["aleman_destino"]) | (df["italiano_origen"] == df["italiano_destino"]) | (df["espanol_origen"] == df["espanol_destino"])) & (df["año"] == año)]
    total = migraciones[migraciones["año"] == año]
    # complemento = migraciones[ (migraciones["año"] == año)& (migraciones["iso3_orig"].isin(pais_colono_idioma["codigo_pais"])) & (migraciones["region_orig_EN"]=="Africa")]
    # df[df['id'].isin(resultado['id']) & (df["año"] == año)]
    migras_intra_colonia.append((int(intra_col["migrantes"].sum()), int(total_colo["migrantes"].sum() - intra_col["migrantes"].sum())))
    resultados_agrupados = (
        resultado
        .groupby(["iso3_orig"], as_index=False)["migrantes"]
        .sum()
    )

    total_agrupados = (
        total
        .groupby(["iso3_orig"], as_index=False)["migrantes"]
        .sum()
    )
    a= int(resultados_agrupados["migrantes"].sum())
    b = int(total_agrupados["migrantes"].sum())
    migras_acolonos.append(( a, b-a))
    # relacion = resultados_agrupados.merge(complemento_agrupados, left_on="iso3_orig", right_on="iso3_orig", how="outer", suffixes=("_colonos", "_otros")).fillna(0)
    print(a,b,a/b)

print(migras_intra_colonia)
fig = plt.figure(figsize=(20,12))
plt.bar(años, [x[0] for x in migras_acolonos], label="con idioma en comun", bottom=[x[1] for x in migras_acolonos])
plt.bar(años, [x[1] for x in migras_acolonos], label="sin idioma en comun")
plt.xlabel("Año")
plt.ylabel("Número de Migrantes")
# plt.title("Migraciones al mismo idioma vs. Otros Destinos")
plt.legend()
plt.savefig(
    f"resultados/Migraciones al mismo idioma.png",
    dpi=300,                 # calidad alta para impresión
    bbox_inches="tight",     # elimina márgenes blancos
    pad_inches=0.1,
    facecolor=fig.get_facecolor()
)
plt.show()

fig = plt.figure(figsize=(20,12))
plt.bar(años, [x[0] for x in migras_intra_colonia], label="mismo bloque colonial", bottom=[x[1] for x in migras_intra_colonia])
plt.bar(años, [x[1] for x in migras_intra_colonia], label="otro destino")
plt.xlabel("Año")
plt.ylabel("Número de Migrantes")
# plt.title("Migraciones al mismo idioma vs. Otros Destinos")
plt.legend()
plt.savefig(
    f"resultados/Migraciones a ex colonias del mismo bloque.png",
    dpi=300,                 # calidad alta para impresión
    bbox_inches="tight",     # elimina márgenes blancos
    pad_inches=0.1,
    facecolor=fig.get_facecolor()
)
plt.show()
