import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

pais_colono_idioma = pd.read_csv("fuentes_de_datos/idiomas_coloniales.csv")
migraciones = pd.read_csv("fuentes_de_datos/migras_90_24.csv")
migraciones = migraciones[migraciones["region_orig_EN"]=="Africa"]
migraciones = migraciones[migraciones["iso3_orig"].isin(pais_colono_idioma["codigo_pais"])]


df = migraciones.merge(pais_colono_idioma, left_on="iso3_orig", right_on="codigo_pais")
df = df.merge(pais_colono_idioma, left_on="iso3_des",
              right_on="codigo_pais",
              suffixes=("_origen", "_destino"), how="left")

migrantes = {"a_soberano": [], "otra_colonia": [], "mismo_idioma": [], "total": []}

años = [1990,1995,2000,2005,2010,2015,2020,2024]
for año in años:
    df_anio = df[df["año"] == año]
    a_soberano = df_anio[df_anio["iso3_des"] == df_anio["codigo_colonia_de_origen"]]
    otra_colonia = df_anio[df_anio["codigo_colonia_de_destino"] == df_anio["codigo_colonia_de_origen"]]
    mismo_idioma = df_anio[ ((df_anio["ingles_origen"] == df_anio["ingles_destino"]) | (df_anio["frances_origen"] == df_anio["frances_destino"]) | (df_anio["portugues_origen"] == df_anio["portugues_destino"]) | (df_anio["aleman_origen"] == df_anio["aleman_destino"]) | (df_anio["italiano_origen"] == df_anio["italiano_destino"]) | (df_anio["espanol_origen"] == df_anio["espanol_destino"]))]

    migrantes["a_soberano"].append(int(a_soberano["migrantes"].sum()))
    migrantes["otra_colonia"].append(int(otra_colonia["migrantes"].sum()))
    migrantes["mismo_idioma"].append(int(mismo_idioma["migrantes"].sum()))
    migrantes["total"].append(int(df_anio["migrantes"].sum()))
    
a_soberano = np.array(migrantes["a_soberano"])
otra_colonia = np.array(migrantes["otra_colonia"])
mismo_idioma = np.array(migrantes["mismo_idioma"])
total = np.array(migrantes["total"])

a = total-mismo_idioma
b = mismo_idioma-otra_colonia-a_soberano
c = otra_colonia
d = a_soberano


fig = plt.figure(figsize=(5,7))
plt.barh(años, d, label="al ex pais soberano", left=c+b+a , color="green")
plt.barh(años, c, label="a ex colonias de la misma potencia", left=b+a , color="orange")
plt.barh(años, b, label="a paises con un idioma en comun", left=a, color="blue")
plt.barh(años, a, label="otros destinos", color="red")
plt.xlabel("Número de Migrantes",fontsize=10)
plt.ylabel("Año", fontsize=10)
plt.legend(fontsize=7)

plt.savefig(
    f"resultados/Migraciones culturales en africah.png",
    dpi=300,                 # calidad alta para impresión
    bbox_inches="tight",     # elimina márgenes blancos
    pad_inches=0.1,
    facecolor=fig.get_facecolor()
)
plt.show()

df_metropolis = df[df["iso3_des"].isin(pais_colono_idioma["codigo_colonia_de"])]

# df_metropolis_1990 = df_metropolis[df_metropolis["año"] == 1990]
df_metropolis_2024 = df_metropolis[df_metropolis["año"] == 2024]

# print(df_metropolis_2024[df_metropolis_2024["iso3_des"]=="GBR"].sort_values("migrantes", ascending=False)[["iso3_orig", "migrantes"]].head(1))
# print(df_metropolis_2024[df_metropolis_2024["iso3_des"]=="FRA"].sort_values("migrantes", ascending=False)[["iso3_orig", "migrantes"]].head(1))
# print(df_metropolis_2024[df_metropolis_2024["iso3_des"]=="GBR"].sort_values("migrantes", ascending=False)[["iso3_orig", "migrantes"]].head(1))
# print(df_metropolis_2024[df_metropolis_2024["iso3_des"]=="PRT"].sort_values("migrantes", ascending=False)[["iso3_orig", "migrantes"]].head(1))
# print(df_metropolis_2024[df_metropolis_2024["iso3_des"]=="ESP"].sort_values("migrantes", ascending=False)[["iso3_orig", "migrantes"]].head(1))
# print(df_metropolis_2024[df_metropolis_2024["iso3_des"]=="ITA"].sort_values("migrantes", ascending=False)[["iso3_orig", "migrantes"]].head(1))
# print(df_metropolis_2024[df_metropolis_2024["iso3_des"]=="DEU"].sort_values("migrantes", ascending=False)[["iso3_orig", "migrantes"]].head(1))

DESTINOS = ["GBR", "FRA", "PRT", "ESP"]#, "ITA", "DEU"]
ORIGENES = ["MAR","DZA","TUN","AGO","KEN","MOZ","SEN","MDG","ZAF"]
ORIGENES = ["MAR","DZA","TUN","NGA","ZAF","AGO","SEN","COM","MDG"]
# ORIGENES = ["NGA", "DZA",  "AGO", "MAR",
#             "COM","STP","ZAF","GNQ",
#             "SOM","BEN","MOZ","ZWE"]

# print(dict(df_metropolis_2024.groupby("iso3_orig")["migrantes"].sum()))


# df_porcentajes = df_metropolis_2024

# df_porcentajes["porcentaje"] = df_porcentajes["migrantes"].div(
#     df.groupby("iso3_orig")["migrantes"].transform("sum")
# ).mul(100)

# print(df_porcentajes[["migrantes", "porcentaje"]].head(10))


df_porcentajes = df_metropolis_2024

df_porcentajes["porcentaje"] = df_porcentajes["migrantes"].div(
    df.groupby("iso3_orig")["migrantes"].transform("sum")
).mul(100)

# print(df_porcentajes[["migrantes", "porcentaje"]].head(10))

df_porcentajes = df_porcentajes[df_porcentajes["iso3_des"] == df_porcentajes["codigo_colonia_de_origen"]]

# print(df_porcentajes[["iso3_orig","iso3_des", "porcentaje"]].sort_values("porcentaje", ascending=False).head(20))

año = 2020
imprimible = migraciones[#(df_metropolis["año"] == año) &
                           (migraciones["iso2_des"]=="ZW")&#.isin(DESTINOS))&
                           (migraciones["iso2_orig"]=="ZA")]#.isin(ORIGENES))&
                        #    (df_metropolis["migrantes"]<151000)]
print(imprimible[["iso3_orig", "iso3_des", "migrantes","año"]].sort_values("migrantes", ascending=False).head(10))

# print(df_metropolis.groupby("iso3_orig")["migrantes"].sum().sort_values(ascending=False).head(10))

print("==============",año,"==============")

# print(migraciones[migraciones["iso3_des"]== "PRT"].sort_values("migrantes", ascending=False)[["iso3_orig","iso3_des","año", "migrantes"]].head(10))
# print(migraciones[(migraciones["iso3_orig"] == "MAR")&
#                   (migraciones["iso3_des"] == "PRT")])
"""
\begin{tabular}{lrrrr}
\toprule
Origen & Francia & Portugal & Gran Bretaña & España \\
\midrule
Argelia & 1344 & - & - & 6 \\
Marruecos & 648 & -  & - & 100\\
Túnez & 358 & -  & - & -\\
Angola & - & 142  & - & -\\
Senegal & 70 & -  & - & -\\
Madagascar & 64 & -  & - & -\\
Sudáfrica & - & 6  & 63 & -\\
Kenya & - & -  & 111 & -\\
Mozambique & - & 75  & - & -\\
\bottomrule
        \caption{Migraciones(en miles) desde Africa en 1990)}
\end{tabular}

\begin{tabular}{lrrrr}
\toprule
Origen & Francia & Portugal & Gran Bretaña & España \\
\midrule
Argelia & 1407 & - & - & 70 \\
Marruecos & 1027 & 2  & - & 914\\
Túnez & 430 & -  & - & -\\
Angola & - & 180  & - & -\\
Senegal & 160 & 2  & - & 78\\
Madagascar & 151 & -  & - & -\\
Sudáfrica & - & 13  & 233 & -\\
Nigeria & - & -  & 286 & -33\\
Comoras & 151 &   & - & -\\
\bottomrule
        \caption{Migraciones(en miles) desde Africa en 2024)}
\end{tabular}
"""