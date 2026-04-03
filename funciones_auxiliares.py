import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader
import dipot
import itertools
import matplotlib.cm as cm
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import networkx as nx 
import numpy as np
import pandas as pd
import seaborn as sns
import seaborn.objects as so
import textwrap
import infomap



from pathlib import Path
from collections import Counter
from IPython.display import display
from matplotlib.axes import Axes
from matplotlib.colors import Normalize
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.colors import to_rgba
from matplotlib.colors import TwoSlopeNorm
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from tqdm.notebook import tqdm
from networkx.algorithms.community.quality import modularity






def crear_tabla_de_referencias(df_migraciones, df_m49) -> None:
    
    df_nombres_paises = (
        df_migraciones.groupby(['origen_ES'], as_index=False)
        .agg({'cod_orig':'first'})
    ).rename(columns={'origen_ES':'País'})
    
    df_paises_alfa = (
        df_nombres_paises.merge(
            df_m49,
            left_on=['cod_orig'],
            right_on=['cod_m49'],
            how='left',
        )
    )
    
    df_paises_alfa = df_paises_alfa[
        [
            'cod_m49',
            'iso2_m49',
            'iso3_m49',
            'País',
            'subregion_ES',
            'region_ES',
            'menos_desarrollado',
            'sin_litoral',
        ]
    ].rename(columns=
             {
                 'cod_m49':'Cód.', 
                 'iso2_m49':'Alfa-2',
                 'iso3_m49':'Alfa-3',
                 'subregion_ES': 'Subregión',
                 'region_ES': 'Región',
                 'menos_desarrollado': 'Menos-desarrollado',
                 'sin_litoral': 'Sin-litoral',
             }
    )
    df_paises_alfa = (
        df_paises_alfa.sort_values(
            ['Alfa-2', 'Alfa-3'], 
            ascending=[True, True]
        ).reset_index(drop=True)
    )
    
    # Exportamos la tabla como imagen
    fig, eje = plt.subplots(figsize=(10, 43))
    eje.axis('tight')
    eje.axis('off')
    tabla = (
        eje.table(
            cellText=df_paises_alfa.values, 
            colLabels=df_paises_alfa.columns, 
            cellLoc='center', 
            loc='center'
        )
    )
    tabla.auto_set_font_size(False)
    tabla.set_fontsize(12)
    # Las columnas se ajustan al valor más ancho
    tabla.auto_set_column_width(col=list(range(len(df_paises_alfa.columns))))

    # Encabezadao y filas impares con color
    for fila, col in tabla.get_celld().items():
        if fila[0] == 0:
            col.set_facecolor('#eb5959')        
        elif fila[0] % 2 != 0:
            col.set_facecolor('#94ebda')
        else:
            col.set_facecolor('white')
    
    fig.tight_layout(pad=5.0)
    plt.savefig('recursos/tabla_paises.png', bbox_inches='tight', dpi=150)
    plt.close()





def graficar_concentracion_emigracion(
    df_cant_destinos: pd.DataFrame,
    paises_que_explican: set[str],
    medianas: list[int | float], 
    promedios: list[int | float], 
    medianas_restantes: list[int | float], 
    promedios_restantes: list[int | float]    
) -> tuple[Figure, Axes]:    
    # Preparamos los datos para visualizar
    df_vis = pd.DataFrame(
        {
            'año': np.concatenate(
                [
                    df_cant_destinos.año.unique(),
                    df_cant_destinos.año.unique(),                
                    df_cant_destinos.año.unique(),
                    df_cant_destinos.año.unique()
                ]
            ),
            'valor': np.concatenate(
                [
                    medianas, promedios, medianas_restantes, promedios_restantes
                ]
            ),
            'medida':( 
                (['Mediana 90%'] * len(medianas)) +
                (['Promedio 90%'] * len(promedios)) +
                (['Promedio 10% restante'] * len(promedios_restantes)) +
                (['Mediana 10% restante'] * len(medianas_restantes))
            )
        }
    )
    
    # COnfiguración del gráfico
    color_ejes = '#121411'
    color_nombre_eje = '#1c1f1b'
    color_borde_refs = '#ffffff'
    tam_titulo = 10
    tam_nombre_eje = 9
    tam_marcas_ejes = 8
    tam_ref = 8
    colores = {
        'Mediana 90%': '#ff2643',
        'Promedio 90%': '#00b5b5',
        'Mediana 10% restante': '#b01a2e',
        'Promedio 10% restante': '#005e5e',
    }    
    fig, eje = plt.subplots(figsize=(9, 4))
    eje.minorticks_on()
    eje.grid(True, which="minor", axis="y", alpha=0.3)
    for medida, df_g in df_vis.groupby("medida"):
        linea, grosor = ('--', 1.1) if medida.startswith('P') else ('-', 1)
        alfa = 0.8 if medida.endswith('e') else 1     
        eje.plot(
            df_g['año'],
            df_g['valor'],
            linewidth=grosor,
            label=medida,       
            linestyle=linea,
            color=colores[medida],
            alpha=alfa,
        )
        eje.scatter(df_g['año'], df_g['valor'], s=5, color=colores[medida], alpha=alfa)
        
    eje.set_xlabel('Año', fontsize=tam_nombre_eje)
    eje.set_ylabel('Número de destinos', fontsize=tam_nombre_eje)
    eje.tick_params(axis="both", labelsize=tam_marcas_ejes)
    eje.spines['right'].set_visible(False)
    eje.spines['top'].set_visible(False)
    eje.spines['left'].set_color(color_ejes)
    eje.spines['bottom'].set_color(color_ejes)
    eje.tick_params(axis='x', colors=color_ejes)
    eje.tick_params(axis='y', colors=color_ejes)
    eje.xaxis.label.set_color(color_ejes)
    eje.yaxis.label.set_color(color_ejes)
    
    objetos, etiquetas = eje.get_legend_handles_labels()
    orden = [
        'Mediana 90%',
        'Promedio 90%',
        'Mediana 10% restante',
        'Promedio 10% restante',
    ]
    id_orden = [etiquetas.index(etq) for etq in orden]
    eje.legend(
        [objetos[i] for i in id_orden],
        [etiquetas[i] for i in id_orden],
        title=None, 
        fontsize=tam_ref, 
        framealpha=1,
        edgecolor=color_borde_refs,
    )
    titulo = 'Concentración de la emigración: número de destinos '
    titulo += 'que explican el 90% principal y el 10% restante (1990-2024)'
    eje.set_title(titulo, fontsize=tam_titulo, pad=13)
    
    descripcion = 'La figura muestra cuántos destinos necesitó un país para explicar el 90% '
    descripcion += ' y el 10% de su emigración en cada año.'
    descripcion += f'\n{len(paises_que_explican)} países explican, como origen o destino, el '
    descripcion += ' 90% del total de los datos migratorios durante el período.'
    fig.text(0.1, 0.01, descripcion, ha="left", va="top", fontsize=9, color=color_ejes)
    
    plt.tight_layout()
    plt.savefig('resultados/concentración_emigración.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return fig, eje





def graficar_comunidades_ppales(
    grafo_pobla_ext: nx.DiGraph,
    eje: Axes,
    año: int,
    **args,
) -> None:
    
    # Colores del mapa
    agua = args.get('agua','#ececec')
    tierra = args.get('tierra', '#cfcfcf')
    fronteras = args.get('fronteras', '#f3f3f3')
    continentes = args.get('continentes', '#a6a6a6')   
    # Colores del grafo
    color_nodos = args.get('color_nodos', '#b1b1b1')
    colores_por_region = {
        'Asia': '#b51b1e',
        'África': '#197c45',
        'Europa': '#0f00b0',
        'Américas': '#212121',
        'Oceanía': '#c67d00',        
    }
    
    # Vsualización 
    eje.set_facecolor(agua) 

    # Hacemos zoom en la región de interés
    posiciones_ingresadas = nx.get_node_attributes(grafo_pobla_ext, 'pos')
    lons = [pos[0] for pos in posiciones_ingresadas.values()]
    lats = [pos[1] for pos in posiciones_ingresadas.values()]
    
    # Márgenes que permiten regular el zoom sobre el mapa
    margen_lat = 5
    margen_lon = 4    
    
    # Extensión del mapa
    eje.set_extent([
        min(lons) - margen_lon,
        max(lons) + margen_lon,
        min(lats) - margen_lat,
        max(lats) + margen_lat
    ], crs=ccrs.PlateCarree())
    
    # Elementos del mapa
    eje.add_feature(cfeature.LAND, facecolor=tierra)
    eje.add_feature(cfeature.OCEAN, facecolor=agua)
    eje.add_feature(cfeature.COASTLINE, edgecolor=continentes, linewidth=0.8, zorder=1)
    eje.add_feature(cfeature.BORDERS, edgecolor=fronteras, linewidth=0.6, zorder=1)

    # Diccionario donde se guardan las coordenadas con referencia al mapa
    pos_nodos = {}
    for nodo in grafo_pobla_ext.nodes():
        lon, lat = posiciones_ingresadas[nodo]
        pos_nodos[nodo] = (lon, lat)
    
    # NODOS
    nx.draw_networkx_nodes(
        grafo_pobla_ext,
        pos_nodos,
        node_size=.5,
        ax=eje,
        node_color=tierra
    )
    
    # # ETIQUETAS
    etiquetas = nx.get_node_attributes(grafo_pobla_ext, 'etiqueta')
    region = nx.get_node_attributes(grafo_pobla_ext, 'region_inmig')
    for nodo, (x, y) in pos_nodos.items():
        eje.text(
            x,
            y,
            etiquetas[nodo],
            fontsize=11,
            fontweight='bold',
            fontstyle='italic',
            color=colores_por_region.get(region[nodo], 'none'),
            ha='center',
            va='center',
            alpha=.7
        )
    
    for comu, pais in grafo_pobla_ext.edges():
        nx.draw_networkx_edges(
            grafo_pobla_ext,
            pos_nodos,
            edgelist=[(comu, pais)],
            width=.5,
            edge_color=[colores_por_region.get(region[pais], 'none')],
            alpha=.6,
            connectionstyle='arc3,rad=0.2',            
            arrowstyle='->',
            arrows=True,
            ax=eje,
        )
        
    # Colores y texto de las referencias
    if año == 2024:
        del colores_por_region['Oceanía']
        lista_ref = []
        for region, color in colores_por_region.items():
            tex_ref = f'Comunidad inmigrante con origen en {region}.'
            ref = mpatches.Patch(color=color, label=tex_ref)
            lista_ref.append(ref)
    
        ref1 = eje.legend(
            # title='REFERENCIAS',
            handles=lista_ref,
            loc='lower left',
            fontsize=14,
            frameon=False,
            facecolor='black',
            framealpha=0.2,
            edgecolor='black',
        )
        # Color del texto de los ítems
        for text in ref1.get_texts():
            text.set_color('black')
        # Color del título
        ref1.get_title().set_color('white')
        eje.add_artist(ref1)





def cargar_nombres_es(
    path: str | None = None,
    key: str = 'iso3'
) -> dict:
    """Carga el listado de nombres normalizado.
    Devuelve {clave: name_es}. clave puede ser 'iso3' o 'cod_m49'.
    Si se elige cod_m49, las claves se convierten a int.
    """
    if path is None:
        p = Path(__file__).resolve().parent / 'fuentes_de_datos' / 'nombres_es.csv'
    else:
        p = Path(path)
    
    m = pd.read_csv(p, dtype=str)
    if key not in m.columns:
        raise KeyError(f"La clave '{key}' no está en el listado. Columnas disponibles: {list(m.columns)}")
    if key == 'cod_m49':
        m[key] = pd.to_numeric(m[key], errors='coerce').dropna().astype(int)
    m['name_es'] = m.get('name_es', '').fillna('').astype(str)
    return dict(zip(m[key], m['name_es']))




def graficar_distribucion_pobla_emig_inmig(
    dicc_datos_por_año: dict[int, pd.DataFrame] 
) -> None:
    
    # Definimos el dominio
    lados = 10
    angulos = np.linspace(0, 2*np.pi, lados, endpoint=False)
    vertices_dominio = [(np.cos(theta), np.sin(theta)) for theta in angulos]
    
    dpi = 300
   
    años = [1990, 2024]
    
    lista_magnitudes_objetivo = [
        ('poblacion', 'Marrón'), ('emigrantes', 'Verde'), ('inmigrantes', 'Roja')
    ]

    for magnitud_objetivo, paleta in lista_magnitudes_objetivo:
        for año in años:  
        
            df = dicc_datos_por_año[año].copy()
            
            columnas_de_interes = [
                'alfa2',
                magnitud_objetivo,
                f'pct_aporte_{magnitud_objetivo}',
                'lon', 
                'lat', 
            ]            
            # Recortamos a las columnas de interes y ordenamos
            df = df[columnas_de_interes]
            df = df.sort_values([columnas_de_interes[2]], ascending=False).reset_index(drop=True)
            # Separamos los paises que explican 90%
            df[f'pct_aporte_{magnitud_objetivo}_acum'] = df[f'pct_aporte_{magnitud_objetivo}'].cumsum()
            df = df[df[f'pct_aporte_{magnitud_objetivo}_acum'] < 91]
    
            # Datos para la construcción del gráfico
            nombres_de_celdas = df.alfa2.values
        
            # Datos para la construcción del diagrama
            valores_magnitud_objetivo = df[magnitud_objetivo].values
            x, y = df.lon.values, df.lat.values    
        
            # Normalizamos las coordenadas a [-1, 1]
            x = (x + 180) / 180 - 1
            y = (y + 90) / 90 - 1
            coordenadas_de_sitios = np.column_stack((x, y))

                   
            pct_barra = 0.0
            formato_barra: str = "{desc}: [{bar}] {percentage:3.0f}% | {elapsed}"
            texto_barra: str = f'Construyendo diagrama: {magnitud_objetivo}-{año}'       
    
            diagrama = dipot.DiagramaDePotencia(
                vertices_dominio,
                coordenadas_de_sitios,
                nombres_de_celdas,
                valores_magnitud_objetivo,   
            )
            
            with tqdm(total=100, desc=texto_barra, bar_format=formato_barra) as barra_pct:    
                diagrama.construir_diagrama(        
                    .13, # alfa_base
                    500, # max_iteraciones
                    5, # umbral_estancamiento
                    1e-5, # error_rel_max_permitido,
                    False, # imprimir progreso
                    barra_pct
                )
        
            
            config_grafico = {
                # Título
                'margen_titulo': 7,
                # Nombres de celdas
                'alfa_nombres_de_celdas': .8, 
                'factor_aumento': 4,
                # Celdas
                'tam_min_nombre_celda': 8,
                'grosor_borde_celdas': 1,
                'alfa_borde_celdas': .7,
                'paleta_celdas': paleta,
            }    
                    
            vis = diagrama._graficar_diagrama(    
                10, # Ancho
                10, # Alto
                dpi, # DPI
                '', # Título
                '', # Nota al pie
                0, # Núm. de caracteres por línea
                f'resultados/diagrama_potencia_{magnitud_objetivo}_{año}', # Ruta de salida
                None, # eje
                **config_grafico,
            )

            display(vis)




  


def graficar_corredores_principales(
    df_migraciones: pd.DataFrame,
    año: int = 2024,
    top_n: int = 30,
    palette: str = 'viridis',
    out_path: str | None = None,
    show=False,
    xlim: tuple | None = None,
) -> tuple:
    """
    Construye el Top N corredores a partir del DF de migraciones y grafica. 
    Parámetros:
      - df_migraciones: DF con columnas 'cod_orig','cod_des','año','migrantes'
      - año: año a filtrar
      - top_n: cantidad de corredores a mostrar
      - palette: paleta de matplotlib (ej. 'viridis', 'plasma')
      - out_path: ruta de salida para la imagen
      - show: si True, muestra el gráfico al finalizar
      - xlim: tupla (min, max) para el límite del eje x. Sino, se ajusta automáticamente.
    """
    if out_path is None:
        out_path = f'resultados/corredores_{año}_top{top_n}.png'

    dicc_nombres_es = cargar_nombres_es(key='cod_m49')  # claves: int

    df = df_migraciones.copy()
    if 'migrantes' in df.columns:
        df['migrantes'] = pd.to_numeric(df['migrantes'], errors='coerce').fillna(0)
    if 'año' in df.columns:
        df['año'] = df['año'].astype(int)

    # Numérico para que coincida con las claves int del diccionario
    df['cod_orig'] = pd.to_numeric(df['cod_orig'], errors='coerce')
    df['cod_des']  = pd.to_numeric(df['cod_des'],  errors='coerce')

    df_a = df[df['año'] == int(año)].copy()

    df_a['origen_nombre_sp'] = df_a['cod_orig'].map(dicc_nombres_es)
    df_a['destino_nombre_sp'] = df_a['cod_des'].map(dicc_nombres_es)
    df_a['corredor'] = df_a['origen_nombre_sp'] + ' → ' + df_a['destino_nombre_sp']

    agg = df_a.groupby(
        ['corredor', 'origen_nombre_sp', 'destino_nombre_sp'], as_index=False
    )['migrantes'].sum().rename(columns={'migrantes': 'stock'})

    top_vis = agg.sort_values('stock', ascending=False).head(int(top_n)).reset_index(drop=True)

    labels = [
        f"{row['origen_nombre_sp'][:20]} → {row['destino_nombre_sp'][:20]}"
        for _, row in top_vis.iterrows()
    ]

    cmap   = plt.get_cmap(palette)
    colors = cmap(np.linspace(0.3, 0.9, len(top_vis)))

    fig, ax = plt.subplots(figsize=(14, max(6, 0.35 * len(top_vis))))
    ax.barh(range(len(top_vis)), top_vis['stock'].astype(float), color=colors)
    ax.set_yticks(range(len(top_vis)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel('Stock de migrantes', fontsize=11, fontweight='bold')
    # No title by request; show the año discretely in the lower-left corner
    ax.text(
        0.01,
        0.02,
        str(año),
        transform=ax.transAxes,
        fontsize=10,
        fontweight='semibold',
        verticalalignment='bottom',
        horizontalalignment='left',
        color='0.15'
    )
    ax.invert_yaxis()
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1e6):.1f}M'))
    ax.grid(axis='x', alpha=0.3, linestyle='--')

    if xlim is not None:
        ax.set_xlim(*xlim)

    plt.tight_layout()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    if show:
        plt.show()
    plt.close()
    return fig, ax





def graficar_red_corredores(
    df_migraciones: pd.DataFrame,
    df_coordenadas: pd.DataFrame,
    año: int = 2024,
    threshold_pct: float = 1.0,
    palette: str = 'YlOrRd',
    tipo_linea: str = 'recta',
    dpi: int = 300,
    excluir_otros: bool = True,
    out_path: str | None = None,
    show: bool = False,
) -> tuple:
    """
    Grafica la red global de corredores migratorios para un año dado.

    Parámetros:
      - df_migraciones : DF con columnas cod_orig, iso3_orig, cod_des, iso3_des, año, migrantes
      - df_coordenadas : DF con columnas iso3_coord, lat, lon
      - año            : año a visualizar
      - threshold_pct  : porcentaje superior de aristas a mostrar por peso (ej: 1 → top 1%)
      - palette        : paleta matplotlib para nodos
      - tipo_linea     : 'recta' o 'geodesica'
      - ancho_px       : ancho de salida en píxeles (default 6000)
      - excluir_otros  : excluir el nodo ZZZ ('Otros / origen desconocido')
      - out_path       : ruta de salida; si es None se genera automáticamente
      - show           : mostrar en notebook
    """
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    if out_path is None:
        out_path = f'resultados/red_corredores_{año}_top{int(threshold_pct)}pct.png'

    dicc_nombres = cargar_nombres_es(key='iso3')

    df = df_migraciones.copy()
    df['migrantes'] = pd.to_numeric(df['migrantes'], errors='coerce').fillna(0)
    df['año'] = df['año'].astype(int)
    df_a = df[df['año'] == año].copy()

    if excluir_otros:
        df_a = df_a[(df_a['iso3_orig'] != 'ZZZ') & (df_a['iso3_des'] != 'ZZZ')]

    coords = df_coordenadas.set_index('iso3_coord')[['lat', 'lon']].to_dict('index')

    # --- Construir grafo ---
    G = nx.DiGraph()

    paises = pd.concat([
        df_a[['iso3_orig']].rename(columns={'iso3_orig': 'iso3'}),
        df_a[['iso3_des']].rename(columns={'iso3_des':  'iso3'}),
    ]).drop_duplicates('iso3')

    for _, row in paises.iterrows():
        iso = row['iso3']
        c = coords.get(iso, {})
        if c:
            G.add_node(iso, nombre=dicc_nombres.get(iso, iso), lat=c['lat'], lon=c['lon'])

    for _, row in df_a.iterrows():
        u, v, w = row['iso3_orig'], row['iso3_des'], row['migrantes']
        if w > 0 and u in G.nodes and v in G.nodes:
            if G.has_edge(u, v):
                G[u][v]['weight'] += w
            else:
                G.add_edge(u, v, weight=w)

    # --- Aplicar threshold ---
    all_weights = np.array([d['weight'] for _, _, d in G.edges(data=True)])
    umbral = np.percentile(all_weights, 100 - threshold_pct)
    G_vis = nx.DiGraph()
    G_vis.add_nodes_from(G.nodes(data=True))
    G_vis.add_edges_from([(u, v, d) for u, v, d in G.edges(data=True) if d['weight'] >= umbral])

    # --- Figura ---
    ancho_in = 40
    alto_in  = ancho_in * (9 / 16)

    fig = plt.figure(figsize=(ancho_in, alto_in), dpi=dpi, facecolor='white')
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_facecolor('white')

    ax.add_feature(cfeature.LAND,      facecolor='#f2f2f2', alpha=1.0)
    ax.add_feature(cfeature.OCEAN,     facecolor='#ddeeff', alpha=1.0)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5, edgecolor='#888888')
    ax.add_feature(cfeature.BORDERS,   linewidth=0.25, edgecolor='#aaaaaa')
    ax.set_extent([-180, 180, -60, 90], crs=ccrs.PlateCarree())

    gl = ax.gridlines(draw_labels=True, linewidth=0.3, alpha=0.4, linestyle='--', color='gray')
    gl.top_labels   = False
    gl.right_labels = False
    gl.xlabel_style = {'size': 14, 'color': '#555555'}
    gl.ylabel_style = {'size': 14, 'color': '#555555'}

    # --- Aristas ---
    transform_linea = ccrs.Geodetic() if tipo_linea == 'geodesica' else ccrs.PlateCarree()

    pesos_vis = np.array([d['weight'] for _, _, d in G_vis.edges(data=True)])
    log_min = np.log10(pesos_vis.min() + 1)
    log_max = np.log10(pesos_vis.max() + 1)

    LW_MIN, LW_MAX       = 0.2, 7.0
    ALPHA_MIN, ALPHA_MAX = 0.04, 0.65

    for u, v, data in G_vis.edges(data=True):
        lon_u = G_vis.nodes[u].get('lon')
        lat_u = G_vis.nodes[u].get('lat')
        lon_v = G_vis.nodes[v].get('lon')
        lat_v = G_vis.nodes[v].get('lat')
        if None in (lon_u, lat_u, lon_v, lat_v):
            continue

        norm     = (np.log10(data['weight'] + 1) - log_min) / (log_max - log_min) if log_max > log_min else 0.5
        norm_exp = norm ** 0.4

        ax.plot(
            [lon_u, lon_v], [lat_u, lat_v],
            color='#cc2200',
            linewidth=LW_MIN + (LW_MAX - LW_MIN) * norm_exp,
            alpha=ALPHA_MIN + (ALPHA_MAX - ALPHA_MIN) * norm_exp,
            transform=transform_linea,
            zorder=2,
            solid_capstyle='round',
        )

    # --- Nodos ---
    grados = dict(G_vis.degree())
    lons, lats, sizes, colores_nodo = [], [], [], []

    for node_id, attrs in G_vis.nodes(data=True):
        if 'lon' not in attrs or 'lat' not in attrs:
            continue
        lons.append(attrs['lon'])
        lats.append(attrs['lat'])
        grado = grados.get(node_id, 0)
        sizes.append(max(120, grado ** 1.6 * 8))
        colores_nodo.append(grado)

    scatter = ax.scatter(
        lons, lats,
        s=sizes,
        c=colores_nodo,
        cmap=palette,
        alpha=0.9,
        edgecolors='#333333',
        linewidths=0.6,
        transform=ccrs.PlateCarree(),
        zorder=5,
    )

    # --- Etiquetas top 20 por grado ---
    top20 = sorted(
        [(n, a) for n, a in G_vis.nodes(data=True) if 'lon' in a and 'lat' in a],
        key=lambda x: grados.get(x[0], 0),
        reverse=True
    )[:20]

    for node_id, attrs in top20:
        ax.annotate(
            attrs.get('nombre', node_id)[:22],
            (attrs['lon'], attrs['lat']),
            xytext=(8, 8),
            textcoords='offset points',
            fontsize=16,
            fontweight='bold',
            color='#111111',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7, linewidth=0),
            zorder=6,
            transform=ccrs.PlateCarree(),
        )

    cbar = plt.colorbar(scatter, ax=ax, fraction=0.018, pad=0.02, shrink=0.55)
    cbar.set_label('Grado (conexiones)', rotation=270, labelpad=22, fontsize=16)
    cbar.ax.tick_params(labelsize=13)

    ax.set_title(
        f'Red Global de Corredores Migratorios ({año})  —  Top {threshold_pct:.1f}% por stock absoluto\n'
        f'Umbral: {umbral:,.0f} migrantes  |  '
        f'{G_vis.number_of_nodes()} países  |  {G_vis.number_of_edges():,} aristas',
        fontsize=22,
        fontweight='bold',
        color='#111111',
        pad=18,
    )

    plt.tight_layout()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=dpi, bbox_inches='tight', facecolor='white')
    if show:
        plt.show()
    plt.close()
    print(f'Red guardada en: {out_path}')
    return fig, ax



def calcular_cuadro_global(df: pd.DataFrame, año: int) -> dict:

    # --- FILTRO ---
    d = df[(df['año'] == año) & (df['iso3_orig'] != 'ZZZ')].copy()

    # --- GRAFO DIRIGIDO PONDERADO ---
    G = nx.DiGraph()
    for _, r in d.iterrows():
        u, v, w = r['iso3_orig'], r['iso3_des'], r['migrantes']
        if w > 0:
            if G.has_edge(u, v):
                G[u][v]['weight'] += w
            else:
                G.add_edge(u, v, weight=w)

    # --- BÁSICOS ---
    nodos = G.number_of_nodes()
    aristas = G.number_of_edges()
    densidad = nx.density(G)
    reciprocidad = nx.reciprocity(G)

    # --- CLUSTERING BINARIO (como en tu cuadro) ---
    G_undir = G.to_undirected()
    clustering_binario = nx.average_clustering(G_undir)

    # --- LONGITUD DE CAMINO (SCC) ---
    scc = max(nx.strongly_connected_components(G), key=len)
    G_scc = G.subgraph(scc).copy()

    if G_scc.number_of_nodes() > 1:
        long_camino = nx.average_shortest_path_length(G_scc)
    else:
        long_camino = float('nan')

    # --- INFOMAP ---
    nodos_lista = list(G.nodes())
    nodo_a_id = {n: i for i, n in enumerate(nodos_lista)}

    im = infomap.Infomap("--directed --silent")
    for u, v, data in G.edges(data=True):
        im.add_link(nodo_a_id[u], nodo_a_id[v], data['weight'])
    im.run()

    # comunidades
    comunidades_dict = {}
    for node in im.nodes:
        cid = node.module_id
        comunidades_dict.setdefault(cid, set()).add(nodos_lista[node.node_id])
    comunidades = list(comunidades_dict.values())

    # --- MODULARIDAD ---
    mod = modularity(G_undir, comunidades, weight='weight')

    return {
        'Nodos': nodos,
        'Aristas': aristas,
        'Densidad': round(densidad, 4),
        'Reciprocidad': round(reciprocidad, 4),
        'Clustering binario (BCC)': round(clustering_binario, 4),
        'Longitud promedio de camino': round(long_camino, 3),
        'Modularidad (Infomap)': round(mod, 4),
    }
    
def graficar_migraciones_africa(
        
    migras_hacia_africa: pd.DataFrame,
    migras_desde_africa: pd.DataFrame,
) -> Figure:   


    fig1 = plt.figure(figsize=(9, 6), dpi=300)  

    # Hacia
    vis1 = (
        so.Plot(migras_hacia_africa, 'año', 'migrantes', color='region_orig_ES')
        .add(so.Dot(pointsize=3.5))
        .add(so.Line(linewidth=1.7))
        .scale(color='colorblind')
            .layout(size=(9, 6))
        .label(
            title='Migraciones hacia África desde otros continentes',
            x='Año',
            y='Migrantes',
            color='Continente origen'
        )
    )    
    vis1.on(fig1).plot()
    fig1.tight_layout()
    fig1.savefig('resultados/migras_hacia_Africa.png', bbox_inches='tight', dpi=300)

    # Desde
    fig2 = plt.figure(figsize=(9, 6), dpi=300)
    vis2 = (
        so.Plot(migras_desde_africa, 'año', 'migrantes', color='region_des_ES')
        .add(so.Dot(pointsize=3.5))
        .add(so.Line(linewidth=1.7))
        .scale(color='colorblind')
            .layout(size=(9, 6))
        .label(
            title='Migraciones desde África hacia otros continentes',
            x='Año',
            y='Migrantes',
            color='Continente destino'
        )
    )    
    vis2.on(fig2).plot()
    fig2.tight_layout()
    fig2.savefig('resultados/migras_desde_Africa.png', bbox_inches='tight', dpi=300)



# Función para convertir valores
def convertir_valor(valor: int, redondeo:int = 2) -> str:
    cambiar_signo = False
    if valor < 0:
        valor *= -1
        cambiar_signo = True
    if valor < 1e3:
        return f'{valor}' if not cambiar_signo else f'{-1*valor}' 
    elif valor < 1e6:
        prefijo = 'k'
        denominador = 1e3
    else:
        prefijo = 'M'
        denominador = 1e6
    conversion = valor / denominador
    valor_redondeado = round(conversion, redondeo)
    # si el decimal es 0 lo descarto
    if valor_redondeado.is_integer():
        return (
            f'{int(valor_redondeado)}{prefijo}' 
            if not cambiar_signo 
            else f'{int(-1*valor_redondeado)}{prefijo}'
        ) 
    else:
        return (
            f'{valor_redondeado}{prefijo}' 
            if not cambiar_signo 
            else f'{-1*valor_redondeado}{prefijo}'
        )
    





    
def graficar_bloques_africa(
    paises_sin_bloque: set[str],
    dicc_bloques_asignados: dict[int, set[str]],
    dicc_cohesion_por_bloque:  dict[int, float],
    df_coords: pd.DataFrame,
) -> Figure: 

    paises_africa = [
        pais 
        for bloques in dicc_bloques_asignados.values() 
        for pais in bloques
    ]
    
    # Creamos la red que permite graficar sobre el mapa
    red_bloques = nx.Graph()
    for bloque, cohesion  in zip(dicc_bloques_asignados.values(), dicc_cohesion_por_bloque.values()):
        for tupla_miembros in itertools.combinations(bloque, 2):
            # Nombres de países
            m1 = tupla_miembros[0]
            m2 = tupla_miembros[1]
            
            # Posiciones de los países
            lon_m1 = df_coords.loc[df_coords.iso3_coord == m1, 'lon'].iloc[0]
            lat_m1 = df_coords.loc[df_coords.iso3_coord == m1, 'lat'].iloc[0]        
            lon_m2 = df_coords.loc[df_coords.iso3_coord == m2, 'lon'].iloc[0]
            lat_m2 = df_coords.loc[df_coords.iso3_coord == m2, 'lat'].iloc[0]        

            # Agregamos el vínculo
            red_bloques.add_edge(m1, m2, weight=cohesion)

            # Si el nodo origen aún no fue ingresado
            if not bool(red_bloques.nodes[m1]):
                red_bloques.add_node(m1, pos=(lon_m1, lat_m1))
            if not bool(red_bloques.nodes[m2]):  
                red_bloques.add_node(m2, pos=(lon_m2, lat_m2))

    
    # Configuración de la visualización
    # Tamaño del gráfico
    tam_figura = (20,17)  
    # Márgenes que permiten regular el zoom sobre el mapa
    margen_lon = 7
    margen_lat = 7
    # Colores del mapa
    agua = '#ffffff'
    tierra = '#c3c3ca'
    fronteras = '#cdced5'
    continentes = '#525255'
    # Colores del grafo
    color_titulo = '#0c0c0c'
    color_nodos = '#ba0000'
    color_aris = '#000000'#5eebc1'
    color_etq_pais = '#000000'
    # Paleta de colores para los nodos
    paleta = [
        '#9d3c43',
        '#d9d697',
        '#98eaa4',
        '#f98c78',
        '#b172ff',
        '#06c9d3',
        '#377054',
        '#f1d438',
        '#f8474a',
        '#3e38ff',
        '#ff1a98',
    ]
    
    
    # Tamaños de fuentes
    tam_tex_etq = 12 # nodos
    tam_tex_titulo = 17 # título gráfico
    tam_tex_ref = 17 # referencias
    
    # Vsualización de la red
    fig = plt.figure(figsize=tam_figura)
    
    # Configuración de colores
    fig.set_facecolor(agua) # Color predominante (fondo)
    eje = fig.add_subplot(1,1,1)
    eje.set_facecolor(agua)  # Fondo interior donde se dibuja el grafo
    eje.axis('off') # Remueve el marco y el color blanco dentro del grafo
    
    # Hago zoom en la región de interés
    posiciones_ingresadas = nx.get_node_attributes(red_bloques, 'pos')
    lons = [pos[0] for pos in posiciones_ingresadas.values()]
    lats = [pos[1] for pos in posiciones_ingresadas.values()]
    
    
    # Proyección
    eje = plt.axes(projection=ccrs.PlateCarree())
    
    # Extensión del mapa
    eje.set_extent(
        [
            min(lons) - margen_lon,
            max(lons) + margen_lon,
            min(lats) - margen_lat,
            max(lats) + margen_lat,
        ],
        crs=ccrs.PlateCarree()
    )
    
    # Elementos del mapa
    eje.add_feature(cfeature.LAND, facecolor=tierra)
    eje.add_feature(cfeature.OCEAN, facecolor=agua)
    eje.add_feature(cfeature.COASTLINE, edgecolor=continentes, linewidth=0.8)
    eje.add_feature(cfeature.BORDERS, edgecolor=fronteras, linewidth=0.6)
    forma_paises = shpreader.natural_earth(
        resolution='110m',
        category='cultural',
        name='admin_0_countries'
    )
    lector = shpreader.Reader(forma_paises)
    poligonos_paises = {}
    for p in lector.records():
        iso = p.attributes['ISO_A3']
        nombre = p.attributes['NAME']    
        if nombre == 'Somaliland':
            iso = 'SOMI'    
        poligonos_paises[iso] = p.geometry
        
    
    # Geometrías de países
    for i, bloque in enumerate(dicc_bloques_asignados.values()):
        for pais in bloque:
            if poligonos_paises.get(pais, None):
                eje.add_geometries(
                    [poligonos_paises[pais]],
                    crs=ccrs.PlateCarree(),
                    edgecolor='black',
                    linewidth=.6,
                    facecolor=paleta[i],
                    alpha=.7,
                    hatch='//' if pais in paises_sin_bloque else None
                )
            if pais == 'SOM':                   
                eje.add_geometries(
                    [poligonos_paises['SOMI']],
                    crs=ccrs.PlateCarree(),
                    edgecolor='black',
                    linewidth=.6,
                    facecolor=paleta[i],
                    alpha=.7, 
                    hatch='//' if pais in paises_sin_bloque else None
                )
    
    for i, bloque in enumerate(dicc_bloques_asignados.values()):
        for pais in bloque:
            if pais in ['MUS', 'SYC', 'COM', 'STP', 'CPV']:
                tamaño_nodo = 900
            else:
                tamaño_nodo = 0
            nx.draw_networkx_nodes(
                red_bloques,            
                posiciones_ingresadas,
                nodelist=[pais],
                node_size=tamaño_nodo,
                node_color=paleta[i],
                node_shape='o',
                alpha=.7,
                ax=eje,
            )
    
    
    # ETIQUETAS    
    for nodo in red_bloques.nodes():
        if nodo in paises_sin_bloque:
            fuente = 'normal'
        else: 
            fuente = 'black'            
        nx.draw_networkx_labels(
            red_bloques,
            posiciones_ingresadas,
            labels={nodo: nodo},
            font_color=color_etq_pais,
            font_weight=fuente,
            alpha=1,
            font_size=tam_tex_etq,
            ax=eje,
        )


    
    # REFERENCIAS
    lista_ref = []
    for i, cohesion in dicc_cohesion_por_bloque.items():
        lista_ref.append(
            mpatches.Patch(
                color=to_rgba(paleta[i], alpha=.7),
                label=f'Cohesión: {round(cohesion, 3)}'
            )
        )
    
    ref1 = eje.legend(
        # title='REFERENCIAS',
        handles=lista_ref,
        loc='lower left',
        fontsize=tam_tex_ref,
        frameon=True,
        facecolor='none',
        framealpha=0,
    )
    
    for text in ref1.get_texts():
        text.set_color('black')
    eje.add_artist(ref1)
    
    
    eje.set_title(
        '',
        fontsize=tam_tex_titulo,
        color=color_titulo,
    )
    
    fig.tight_layout()
    plt.savefig("resultados/bloques_africa.png", bbox_inches='tight', dpi=300) 
    plt.close()
    
    return fig
    
    



def red_migra_intra_afr(df_migras: pd.DataFrame, **args) -> Figure:

    # Red
    año = df_migras.iloc[0].año
    # Valores para normalizar grosor aristas y tamaño nodos
    tot_emig = df_migras.emigrantes.sum()
    max_emig = df_migras.emigrantes.max()   
    max_orig, max_des = (
        df_migras.loc[
            df_migras['emigrantes'].idxmax(),
            ['iso2_orig', 'iso2_des']
        ]
    )
    paises_max_migra = f'{max_orig} → {max_des}'
    
    red = nx.DiGraph()    
    for _, fila in df_migras.iterrows():
        
        # Países        
        origen, destino = fila.iso2_orig, fila.iso2_des
        
        # Ubicaciones
        x_orig, y_orig = fila.lon_orig, fila.lat_orig
        x_des, y_des = fila.lon_des, fila.lat_des

        # Desarrollo
        destino_menos_desarr = fila.menos_desarr_des
        
        # Emigrantes 
        migrantes = fila.emigrantes / max_emig
        
        # Agregamos nodos y enlace a la red
        red.add_node(origen, pos=(x_orig, y_orig))          
        red.add_node(destino, pos=(x_des, y_des))
        red.add_edge(
            origen,
            destino,
            weight=migrantes,
            a_menos_desarr=destino_menos_desarr,
        )
    
    for n in red.nodes:      
        red.nodes[n]['inmigrantes'] = (
            df_migras.query("iso2_des == @n").emigrantes.sum() / tot_emig
        )
    

    # Visualización    
    dpi = args.get('dpi', 300)
    tam_figura = args.get('tam_figura', (20,10))  
    # Colores del mapa
    agua = args.get('agua','#e6e6e6')
    tierra = args.get('tierra', '#b0b0b0')
    fronteras = args.get('fronteras', '#dfdfdf')
    continentes = args.get('continentes', '#8a8a8a')   
    # Colores de la red
    color_nodos = args.get('color_nodos', '#3c5339')
    color_a_menos_desarr = args.get('color_a_menos_desarr', '#8c270e')
    color_a_desarr = args.get('color_a_desarr', '#183d44')
    color_etq_pais = args.get('color_etq_pais', '#101010')
    alfa_nodos = args.get('alfa_nodos', .3)
    alfa_aristas = args.get('alfa_aristas', .7)
    alfa_etiquetas = args.get('alfa_etiquetas', .8)
    # Tamaños textos
    tam_tex_etq = args.get('tam_tex_etq', 11) # Códigos de países
    tam_tex_ref = args.get('tam_tex_ref', 10) # Referencias
    # Márgenes que permiten regular el zoom sobre el mapa
    enfocar = args.get('enfocar', False)
    margen_izq = args.get('margen_izq', 0)
    margen_sup = args.get('margen_sup', 0)    
    margen_der = args.get('margen_der', 0)
    margen_inf = args.get('margen_inf', 0)
    # Ubicación y fondo de las referencias
    ubic_ref = args.get('ubic_ref', 'lower left')
    fondo_ref = args.get('fondo_ref', False)
    # Otros
    grosor_bordes_paises = args.get('grosor_bordes_paises', .6)
    grosor_bordes_continentes = args.get('grosor_bordes_continentes', .7)

    # FIGURA
    fig, eje = plt.subplots(
        figsize=tam_figura, 
        dpi=dpi,
        subplot_kw={'projection': ccrs.Robinson()}
    )    
    fig.set_facecolor('white')
    eje.set_facecolor(agua)

    # MAPA
    eje.add_feature(cfeature.LAND, facecolor=tierra)
    eje.add_feature(cfeature.OCEAN, facecolor=agua)
    eje.add_feature(
        cfeature.COASTLINE,
        edgecolor=continentes,
        linewidth=grosor_bordes_continentes,
        zorder=1
    )
    eje.add_feature(
        cfeature.BORDERS,
        edgecolor=fronteras,
        linewidth=grosor_bordes_paises,
        zorder=1
    )
   
    # COORDENADAS Y ENFOQUE
    pos_nodos = nx.get_node_attributes(red, 'pos')
    pos_proj = {}
    for n, (lon, lat) in pos_nodos.items():
        x, y = ccrs.Robinson().transform_point(lon, lat, ccrs.PlateCarree())
        pos_proj[n] = (x, y)
    # Para ajustar la región del mapa donde hacemos foco
    if enfocar:
        lons = [pos[0] for pos in pos_nodos.values()]
        lats = [pos[1] for pos in pos_nodos.values()]     
        eje.set_extent([
            min(lons) - margen_der,
            max(lons) + margen_izq,
            min(lats) - margen_inf,
            max(lats) + margen_sup
        ], crs=ccrs.PlateCarree())

    
    # NODOS
    pesos_nodos = nx.get_node_attributes(red, 'inmigrantes')
    tamaños = [(pesos_nodos[n]*2e4) for n in red.nodes()]    
    nx.draw_networkx_nodes(
        red,
        pos_proj,
        node_size=tamaños,
        node_color=color_nodos,
        edgecolors='none',
        alpha=alfa_nodos,
        ax=eje,
    )

    # ETIQUETAS
    for nodo in red.nodes():
        nx.draw_networkx_labels(
            red,
            pos_proj,
            labels={nodo: nodo},
            font_color=color_etq_pais,
            font_weight='bold',
            alpha=alfa_etiquetas,
            font_size=tam_tex_etq,
            ax=eje,
        )    

    # ARISTAS
    pesos_aristas = [float(red[u][v]['weight'])*1e1 for u,v in red.edges()]
    direccion_desarr = [red[u][v]['a_menos_desarr'] for u,v in red.edges()]

    for i, (orig, des) in enumerate(red.edges()):
        if direccion_desarr[i]:
            color_aris = color_a_menos_desarr
        else:
            color_aris = color_a_desarr

        nx.draw_networkx_edges(
            red,
            pos_proj,
            edgelist=[(orig, des)],
            width=pesos_aristas[i],
            edge_color=color_aris,
            alpha=alfa_aristas,
            connectionstyle='arc3,rad=0.25',
            style='solid',
            arrowstyle='->',
            arrowsize=max(10,pesos_aristas[i]*5),
            arrows=True,
            ax=eje,
        )

    
    # REFERENCIAS
    ref_nodo = mpatches.Patch(
        color=to_rgba(color_nodos, alpha=alfa_nodos),
        label='Tamaño nodo según inmigrantes'
    )
    ref_a_menos_desarr = mpatches.Patch(
        color=to_rgba(color_a_menos_desarr, alpha=alfa_aristas),
        label='Emigración a país menos desarrollado'
    )
    ref_a_desarr = mpatches.Patch(
        color=to_rgba(color_a_desarr, alpha=alfa_aristas),
        label='Emigración a país desarrollado'
    )
    
    ref_max_mig = mpatches.Patch(
        facecolor='none',
        label=f'Máx. emigrantes: {convertir_valor(max_emig)} ({paises_max_migra})'
    )
   
    lista_ref = [ref_nodo, ref_a_menos_desarr, ref_a_desarr, ref_max_mig]
    ref = eje.legend(
        title=str(año),
        handles=lista_ref,
        handlelength=2,
        handleheight=.7,
        loc='lower left',
        fontsize=tam_tex_ref,
        frameon=True,
        facecolor='none',
        framealpha=.9,
        edgecolor='none',
        alignment='left',
    )
    ref.get_title().set_fontweight('bold')
    ref.get_title().set_fontsize(12)
    ref.get_title().set_ha('left')
    # Color del texto de los ítems
    for text in ref.get_texts():
        text.set_color(color_etq_pais)
    eje.add_artist(ref)
    
    fig.tight_layout()
    plt.savefig(f'resultados/red_migra_africa_{año}.png', bbox_inches='tight', dpi=300)        
    plt.close()
   
    return fig

















def migracion_argentina(
    red: nx.DiGraph,
    max_migrantes: int,
    pais_max_migrantes: str,
    min_migrantes: int,
    año: int, 
    **args
) -> Figure | Axes:
   
    # Configuración de la visualización    
    # Tamaño del gráfico
    tam_figura = (20,10)  
    # Márgenes que permiten regular el zoom sobre el mapa
    margen_lon = 7
    margen_lat = 20
    # Colores del mapa
    agua = args.get('agua','#e6e6e6')
    tierra = args.get('tierra', '#b0b0b0')
    fronteras = args.get('fronteras', '#dfdfdf')
    continentes = args.get('continentes', '#8a8a8a')   
    # Colores del grafo
    color_titulo = '#ffffff'
    color_nodos = '#2cffb2'
    color_emigracion = '#ff2f32'
    color_inmigracion = '#2600ff'
    color_etq_pais = '#101010'
    alfa_nodos = .5
    alfa_aristas = .7
    alfa_etiquetas = .7 
    # Tamaños de fuentes
    tam_tex_etq = 15 # nodos
    tam_tex_ref = 13 # referencias
        
    fig, eje = plt.subplots(
        figsize=tam_figura, 
        dpi=300,
        subplot_kw={'projection': ccrs.Robinson()}
    )

    fig.set_facecolor('white')
    eje.set_facecolor(agua) 
    # eje.axis('off') 
        
    # Elementos del mapa
    eje.add_feature(cfeature.LAND, facecolor=tierra)
    eje.add_feature(cfeature.OCEAN, facecolor=agua)
    eje.add_feature(cfeature.COASTLINE, edgecolor=continentes, linewidth=0.7, zorder=1)
    eje.add_feature(cfeature.BORDERS, edgecolor=fronteras, linewidth=0.6, zorder=1)   
    
    # Coordenadas
    pos_nodos = nx.get_node_attributes(red, 'pos')
    pos_proj = {}
    for n, (lon, lat) in pos_nodos.items():
        x, y = ccrs.Robinson().transform_point(lon, lat, ccrs.PlateCarree())
        pos_proj[n] = (x, y)
    
    # NODOS
    pesos_nodos = nx.get_node_attributes(red, 'poblacion')
    tamaños = [(pesos_nodos[n]*2e4) for n in red.nodes()]    
    nx.draw_networkx_nodes(
        red,
        pos_proj,
        node_size=tamaños,
        node_color=color_nodos,
        edgecolors='none',
        alpha=alfa_nodos,
        ax=eje,
    )
    
    # ETIQUETAS
    for nodo in red.nodes():
        nx.draw_networkx_labels(
            red,
            pos_proj,
            labels={nodo: nodo},
            font_color=color_etq_pais,
            font_weight='bold',
            alpha=alfa_etiquetas,
            font_size=tam_tex_etq,
            ax=eje,
        )    
            
    # ARISTAS
    pesos_aristas = [float(red[u][v]['weight'])*2e1 for u,v in red.edges()]       
    for i, (orig, des) in enumerate(red.edges()):
        if orig == 'AR':
            color_aris = color_emigracion
        else:
            color_aris = color_inmigracion
        nx.draw_networkx_edges(
            red,
            pos_proj,
            edgelist=[(orig, des)],
            width=pesos_aristas[i],
            edge_color=color_aris,
            alpha=alfa_aristas,
            connectionstyle='arc3,rad=0.3',            
            arrowstyle='-',
            arrows=True,
            ax=eje,
        )    
        
    # REFERENCIAS
    ref_nodo = mpatches.Patch(color=to_rgba(color_nodos, alpha=alfa_nodos), label='Población')
    ref_emig = mpatches.Patch(color=to_rgba(color_emigracion, alpha=alfa_aristas), label='Emigrantes')
    ref_inmig = mpatches.Patch(color=to_rgba(color_inmigracion, alpha=alfa_aristas), label='Inmigrantes')
    ref_min_mig = mpatches.Patch(
        color=to_rgba(color_inmigracion, alpha=0), 
        label=f'Mín. migrantes: {min_migrantes}'
    )        
    ref_max_mig = mpatches.Patch(
        color=to_rgba(color_inmigracion, alpha=0), 
        label=f'Máx. migrantes: {max_migrantes} ({pais_max_migrantes})'
    )

    lista_ref = [ref_nodo, ref_emig, ref_inmig, ref_min_mig, ref_max_mig]
    ref = eje.legend(
        handles=lista_ref,
        handlelength=2,
        handleheight=.7,
        loc='lower left',
        fontsize=tam_tex_ref,
        frameon=True,
        facecolor='none',
        framealpha=.9,
        edgecolor='none',
    )
    # Color del texto de los ítems
    for text in ref.get_texts():
        text.set_color(color_etq_pais)
    eje.add_artist(ref)
        
    fig.tight_layout()
    plt.savefig(f'resultados/red_migra_argentina_{año}.png', bbox_inches='tight', dpi=300) 
    plt.close()
    return fig







def red_ego_pais(
    dicc_codigos: dict[str, str],
    pct_datos: int,
    dicc_migras_econ: dict[int, pd.DataFrame],
    pais: str,
    año: int, 
    df_idh: pd.DataFrame,
    idh: bool=False,
    **args
) -> Figure:
    
    # Obtenemos los datos del país
    df = dicc_migras_econ[año].copy()
    df = df.query('iso2_orig == @pais | iso2_des == @pais')
    
    # Puntajes de países involucrados (para colorear el mapa)
    dicc_orig = {c:v for c,v in zip(list(df.iso3_orig.values), list(df.puntaje_orig.values))}
    dicc_des = {c:v for c,v in zip(list(df.iso3_des.values), list(df.puntaje_des.values))}
    dicc_paises_involucrados = dicc_orig | dicc_des
    
    # Valores para normalizar grosor aristas y tamaño nodos
    migra_max = df.migrantes.max()       
    max_orig, max_des = df.loc[df['migrantes'].idxmax(), ['iso2_orig', 'iso2_des']]
    paises_max_migra = f'{max_orig} → {max_des}'
    migra_min = df.migrantes.min()    
    min_orig, min_des = df.loc[df['migrantes'].idxmin(), ['iso2_orig', 'iso2_des']]
    paises_min_migra = f'{min_orig} → {min_des}'

    # Creo un dicc con los valores del idh de cada país involucrado
    if idh:
        df_idh = df_idh[df_idh.año == año]
        dicc_idh = {
            c:v 
            for c,v in zip(
                list(df_idh.iso3_econ.values),
                list(df_idh.hdi.values)
            )
        }

    # Construimos la red de migraciones
    red = nx.DiGraph()    
    for _, fila in df.iterrows():
        
        # Países        
        origen = fila.iso2_orig
        destino = fila.iso2_des
        
        # Ubicaciones
        x_orig, y_orig = fila.lon_orig, fila.lat_orig
        x_des, y_des = fila.lon_des, fila.lat_des
        
        # Migrantes ( normalización grosor aristas)
        migrantes = fila.migrantes / migra_max    
        
        # Puntajes
        puntaje_orig = fila.puntaje_orig
        puntaje_des = fila.puntaje_des
        dif_puntaje = fila.dif_puntaje
        
        # Agregamos nodos y enlace a la red
        red.add_node(
            origen, 
            pos=(x_orig, y_orig),
            puntaje=puntaje_orig,
        )
        red.add_node(
            destino,
            pos=(x_des, y_des),
            puntaje=puntaje_des,
        )
        red.add_edge(
            origen,
            destino,
            weight=migrantes,
            dif_puntaje=dif_puntaje,
        )

    # CONFIGURACIÓN GRAL. DE LA VISUALIZACIÓN
    dpi = args.get('dpi', 300)
    tam_figura = args.get('tam_figura', (20,10))  
    # Colores del mapa
    agua = args.get('agua','#e6e6e6')
    tierra = args.get('tierra', '#b0b0b0')
    fronteras = args.get('fronteras', '#dfdfdf')
    continentes = args.get('continentes', '#8a8a8a')   
    # Colores de la red
    color_emigracion = args.get('color_emigracion', '#ff9d00')
    color_inmigracion = args.get('color_inmigracion', '#3564ff')#1f218a
    color_etq_pais = args.get('color_etq_pais', '#101010')
    alfa_aristas = args.get('alfa_aristas', .9)
    alfa_etiquetas = args.get('alfa_etiquetas', .8)
    # Tamaños textos
    tam_tex_etq = args.get('tam_tex_etq', 13) # Códigos de países
    tam_tex_ref = args.get('tam_tex_ref', 12) # Referencias
    # Márgenes que permiten regular el zoom sobre el mapa
    enfocar = args.get('enfocar', False)
    margen_izq = args.get('margen_izq', 0)
    margen_sup = args.get('margen_sup', 0)    
    margen_der = args.get('margen_der', 0)
    margen_inf = args.get('margen_inf', 0)
    # Ubicación y fondo de las referencias
    ubic_ref = args.get('ubic_ref', 'lower left')
    fondo_ref = args.get('fondo_ref', False)
    # Otros
    grosor_bordes_paises = args.get('grosor_bordes_paises', .6)
    grosor_bordes_continentes = args.get('grosor_bordes_continentes', .7)
    tam_tex_barra = args.get('tam_tex_barra', 13)
    aspecto_barra = args.get(
        'aspecto_barra',{'fraction': 0.01, 'aspect': 70, 'pad': 0.02}
    )

    
    fig, eje = plt.subplots(
        figsize=tam_figura, 
        dpi=dpi,
        subplot_kw={'projection': ccrs.Robinson()}
    )    
    fig.set_facecolor('white')
    eje.set_facecolor(agua) 
    eje.add_feature(cfeature.LAND, facecolor=tierra)
    eje.add_feature(cfeature.OCEAN, facecolor=agua)
    eje.add_feature(
        cfeature.COASTLINE,
        edgecolor=continentes,
        linewidth=grosor_bordes_continentes,
        zorder=1
    )
    eje.add_feature(
        cfeature.BORDERS,
        edgecolor=fronteras,
        linewidth=grosor_bordes_paises,
        zorder=1
    )
    
    # DATOS ECONÓMICOS DE LOS PAÍSES INVOLUCRADOS     
    transicion = LinearSegmentedColormap.from_list( # Mapa de color
        'rv', ['#ff4343', '#00ef93']
    )

    forma_paises = shpreader.natural_earth(
        resolution='110m',
        category='cultural',
        name='admin_0_countries'
    )
    lector = shpreader.Reader(forma_paises)


    for datos_pais in lector.records():
        iso3 = datos_pais.attributes['ISO_A3']
        nombre = datos_pais.attributes['NAME']  

        if nombre == 'France': # Ir agregando si descubrimos más que dan problemas
            iso3 = 'FRA'
        elif nombre == 'Norway':
            iso3 = 'NOR'
            
        if iso3 in dicc_paises_involucrados.keys():
            poligono_pais = datos_pais.geometry

            if not idh:
                valor = dicc_paises_involucrados[iso3]
            else:
                valor = dicc_idh[iso3]

            if (valor != 0.0 and not pd.isna(valor)): # El país tiene dato económico
                eje.add_geometries(
                    [poligono_pais],
                    crs=ccrs.PlateCarree(),
                    edgecolor='black',
                    linewidth=grosor_bordes_paises,
                    facecolor=transicion(valor),
                    alpha=1,
                    zorder=1,
                )
            else: # El país no tiene dato economico
                eje.add_geometries(
                    [poligono_pais],
                    crs=ccrs.PlateCarree(),
                    edgecolor=continentes,
                    linewidth=grosor_bordes_paises,
                    facecolor='white',
                    alpha=1,
                    hatch='///////',
                    zorder=1
                )    

    # Texto bajo la barra de color
    if not idh:       
        tex_barra = 'Puntaje económico'
    else:
        tex_barra = 'Índice de Desarrollo Humano'
    rango_barra = Normalize(vmin=0, vmax=1)
    rango_a_color = plt.cm.ScalarMappable(cmap=transicion, norm=rango_barra)
    rango_a_color.set_array([])
    barra_color = plt.colorbar(
        rango_a_color,
        ax=eje,
        # label=tex_barra,
        orientation='horizontal',
        **aspecto_barra
    )
    barra_color.set_label(tex_barra, fontsize=tam_tex_barra)

    # RED 
    pos_nodos = nx.get_node_attributes(red, 'pos')
    pos_proj = {}
    for n, (lon, lat) in pos_nodos.items():
        x, y = ccrs.Robinson().transform_point(lon, lat, ccrs.PlateCarree())
        pos_proj[n] = (x, y)
    # Para ajustar la región del mapa donde hacemos foco
    if enfocar:
        lons = [pos[0] for pos in pos_nodos.values()]
        lats = [pos[1] for pos in pos_nodos.values()]     
        eje.set_extent([
            min(lons) - margen_der,
            max(lons) + margen_izq,
            min(lats) - margen_inf,
            max(lats) + margen_sup
        ], crs=ccrs.PlateCarree())

    # ETIQUETAS
    for nodo in red.nodes():
        nx.draw_networkx_labels(
            red,
            pos_proj,
            labels={nodo: nodo},
            font_color=color_etq_pais,
            font_weight='bold',
            alpha=alfa_etiquetas,
            font_size=tam_tex_etq,
            ax=eje,
        )    

    # ARISTAS
    pesos_aristas = [float(red[u][v]['weight'])*1e1 for u,v in red.edges()]
    direccion_econ = [red[u][v]['dif_puntaje'] for u,v in red.edges()]

    for i, (orig, des) in enumerate(red.edges()):
        if orig == pais:
            color_aris = color_emigracion
        else:
            color_aris = color_inmigracion
        if not idh:
            if direccion_econ[i] < 0:
                estilo = (0, (5, 5))
            else:
                estilo = 'solid'
        else:
            if dicc_idh[dicc_codigos[des]] - dicc_idh[dicc_codigos[orig]] < 0:                
                estilo = (0, (5, 5))
            else:
                estilo = 'solid'
        nx.draw_networkx_edges(
            red,
            pos_proj,
            edgelist=[(orig, des)],
            width=pesos_aristas[i],
            edge_color=color_aris,
            alpha=alfa_aristas,
            connectionstyle='arc3,rad=0.25',
            style=estilo,
            arrowstyle='-',
            arrows=True,
            ax=eje,
        )    
    # REFERENCIAS
    ref_pais_sin_dato = mpatches.Patch(
        # color=to_rgba(color_nodos, alpha=.8),
        label='Sin dato económico',
        edgecolor=continentes,                    
        facecolor='white',
        alpha=1,
        hatch='///////',
    )
    ref_emig = mpatches.Patch(
        color=to_rgba(color_emigracion, alpha=alfa_aristas),
        label='Emigración ↑Econ.'
    )    
    ref_emig_no_econ = Line2D(
        [0], [0],
        color=to_rgba(color_emigracion, alpha=alfa_aristas),
        linestyle='--',
        linewidth=2.5,
        label='Emigración ↓Econ.'
    )
    ref_inmig = mpatches.Patch(
        color=to_rgba(color_inmigracion, alpha=alfa_aristas), 
        label='Inmigración ↑Econ.'
    )    
    ref_inmig_no_econ = Line2D(
        [0], [0],
        color=to_rgba(color_inmigracion, alpha=alfa_aristas),
        linestyle='--',
        linewidth=2.5,
        label='Inmigración ↓Econ.'
    )
    ref_min_mig = mpatches.Patch(
        facecolor='none',
        label=f'• Mín. migrantes:\n   {migra_min} [{paises_min_migra}]'
    )        
    ref_max_mig = mpatches.Patch(
        facecolor='none',
        label=f'• Máx. migrantes:\n   {migra_max} [{paises_max_migra}]'
    )
    ref_pct_mig = mpatches.Patch(
        facecolor='none',
        label=f'• Datos incluidos: {pct_datos-1}%'
    )    
    ref_nodos = mpatches.Patch(
        facecolor='none',
        label=f'• Nodos: {len(pos_nodos)}'
    )    
    ref_enlaces = mpatches.Patch(
        facecolor='none',
        label=f'• Enlaces: {len(pesos_aristas)}'
    )
    lista_ref = [
        ref_pais_sin_dato,
        ref_emig,
        ref_emig_no_econ,
        ref_inmig,
        ref_inmig_no_econ,
        ref_min_mig,
        ref_max_mig,
        ref_pct_mig,
        ref_nodos,
        ref_enlaces,        
    ]
    if fondo_ref:
        color_fondo = 'white'
        color_borde = 'black'
        alfa_ref = .5
    else:        
        color_fondo = 'none'
        color_borde = 'none'
        alfa_ref = 0
        
    ref = eje.legend(
        title=f'{pais} {año}\nRed ego de primer orden',
        handles=lista_ref,
        handlelength=2,
        handleheight=.7,
        loc=ubic_ref,
        fontsize=tam_tex_ref,
        frameon=True,
        facecolor=color_fondo,
        framealpha=alfa_ref,
        edgecolor=color_borde,
        alignment='left',
    )    
    ref.get_title().set_fontweight('bold')
    ref.get_title().set_fontsize(13)
    ref.get_title().set_ha('left')
    for text in ref.get_texts():
        text.set_color(color_etq_pais)
    eje.add_artist(ref)    
    
    fig.tight_layout()
    plt.close()
    
    return fig





def red_ego_pais2(
    dicc_codigos: dict[str, str],
    pct_datos: int,
    dicc_migras_econ: dict[int, pd.DataFrame],
    pais: str,
    año: int, 
    **args
) -> Figure:
    
    # Obtenemos los datos del país
    df = dicc_migras_econ[año].copy()
    df = df.query('iso2_orig == @pais | iso2_des == @pais')
    
    # Países involucrados (para colorear el mapa)
    paises_involucrados = set(df.iso3_orig.values) | set(df.iso3_des.values)

    # Balance migratorio (entrada - salida)
    tot_emig = df.query('iso2_orig == @pais').migrantes.sum()
    tot_inmig = df.query('iso2_des == @pais').migrantes.sum()
    balance_mig = tot_inmig - tot_emig
    
    # Valores para normalizar grosor aristas y tamaño nodos
    migra_max = df.migrantes.max()       
    max_orig, max_des = df.loc[df['migrantes'].idxmax(), ['iso2_orig', 'iso2_des']]
    paises_max_migra = f'{max_orig} → {max_des}'
    migra_min = df.migrantes.min()    
    min_orig, min_des = df.loc[df['migrantes'].idxmin(), ['iso2_orig', 'iso2_des']]
    paises_min_migra = f'{min_orig} → {min_des}'

    # Construimos la red de migraciones
    red = nx.DiGraph()    
    for _, fila in df.iterrows():
        
        # Países        
        origen = fila.iso2_orig
        destino = fila.iso2_des
        
        # Ubicaciones
        x_orig, y_orig = fila.lon_orig, fila.lat_orig
        x_des, y_des = fila.lon_des, fila.lat_des
        
        # Migrantes ( normalización grosor aristas)
        migrantes = fila.migrantes / migra_max    
               
        # Agregamos nodos y enlace a la red
        red.add_node(
            origen, 
            pos=(x_orig, y_orig),
        )
        red.add_node(
            destino,
            pos=(x_des, y_des),
        )
        red.add_edge(
            origen,
            destino,
            weight=migrantes,
        )

    # CONFIGURACIÓN GRAL. DE LA VISUALIZACIÓN
    dpi = args.get('dpi', 300)
    tam_figura = args.get('tam_figura', (20,10))  
    # Colores del mapa
    agua = args.get('agua','#e6e6e6')
    tierra = args.get('tierra', '#b0b0b0')
    fronteras = args.get('fronteras', '#dfdfdf')
    continentes = args.get('continentes', '#8a8a8a')   
    # Colores de la red
    color_paises = args.get('color_paises', '#486155')
    color_borde_pais = args.get('color_borde_pais', '#27352f')
    color_emigracion = args.get('color_emigracion', '#ff0000')
    color_inmigracion = args.get('color_inmigracion', '#00ff73')
    color_etq_pais = args.get('color_etq_pais', '#101010')
    alfa_paises = args.get('alfa_paises', .6)
    alfa_aristas = args.get('alfa_aristas', .8)
    alfa_etiquetas = args.get('alfa_etiquetas', .8)
    # Tamaños textos
    tam_tex_etq = args.get('tam_tex_etq', 13) # Códigos de países
    tam_tex_ref = args.get('tam_tex_ref', 12) # Referencias
    # Márgenes que permiten regular el zoom sobre el mapa
    enfocar = args.get('enfocar', False)
    margen_izq = args.get('margen_izq', 0)
    margen_sup = args.get('margen_sup', 0)    
    margen_der = args.get('margen_der', 0)
    margen_inf = args.get('margen_inf', 0)
    # Ubicación y fondo de las referencias
    ubic_ref = args.get('ubic_ref', 'lower left')
    fondo_ref = args.get('fondo_ref', False)
    # Otros
    grosor_bordes_paises = args.get('grosor_bordes_paises', .6)
    grosor_bordes_continentes = args.get('grosor_bordes_continentes', .7)
        
    fig, eje = plt.subplots(
        figsize=tam_figura, 
        dpi=dpi,
        subplot_kw={'projection': ccrs.Robinson()}
    )    
    fig.set_facecolor('white')
    eje.set_facecolor(agua) 
    eje.add_feature(cfeature.LAND, facecolor=tierra)
    eje.add_feature(cfeature.OCEAN, facecolor=agua)
    eje.add_feature(
        cfeature.COASTLINE,
        edgecolor=continentes,
        linewidth=grosor_bordes_continentes,
        zorder=1
    )
    eje.add_feature(
        cfeature.BORDERS,
        edgecolor=fronteras,
        linewidth=grosor_bordes_paises,
        zorder=1
    )
    
  

    forma_paises = shpreader.natural_earth(
        resolution='110m',
        category='cultural',
        name='admin_0_countries'
    )
    lector = shpreader.Reader(forma_paises)

    for datos_pais in lector.records():
        iso3 = datos_pais.attributes['ISO_A3']
        nombre = datos_pais.attributes['NAME']  

        if nombre == 'France': # Ir agregando si descubrimos más que dan problemas
            iso3 = 'FRA'
        elif nombre == 'Norway':
            iso3 = 'NOR'
            
        if iso3 in paises_involucrados:
            poligono_pais = datos_pais.geometry
            eje.add_geometries(
                [poligono_pais],
                crs=ccrs.PlateCarree(),
                edgecolor=color_borde_pais,
                linewidth=grosor_bordes_paises,
                facecolor=color_paises,
                alpha=alfa_paises,
                zorder=1,
            )


    # RED 
    pos_nodos = nx.get_node_attributes(red, 'pos')
    pos_proj = {}
    for n, (lon, lat) in pos_nodos.items():
        x, y = ccrs.Robinson().transform_point(lon, lat, ccrs.PlateCarree())
        pos_proj[n] = (x, y)
    # Para ajustar la región del mapa donde hacemos foco
    if enfocar:
        lons = [pos[0] for pos in pos_nodos.values()]
        lats = [pos[1] for pos in pos_nodos.values()]     
        eje.set_extent([
            min(lons) - margen_der,
            max(lons) + margen_izq,
            min(lats) - margen_inf,
            max(lats) + margen_sup
        ], crs=ccrs.PlateCarree())

    # ETIQUETAS
    for nodo in red.nodes():
        nx.draw_networkx_labels(
            red,
            pos_proj,
            labels={nodo: nodo},
            font_color=color_etq_pais,
            font_weight='bold',
            alpha=alfa_etiquetas,
            font_size=tam_tex_etq,
            ax=eje,
        )    

    # ARISTAS
    pesos_aristas = [float(red[u][v]['weight'])*1e1 for u,v in red.edges()]
    for i, (orig, des) in enumerate(red.edges()):
        if orig == pais:
            color_aris = color_emigracion
        else:
            color_aris = color_inmigracion
        nx.draw_networkx_edges(
            red,
            pos_proj,
            edgelist=[(orig, des)],
            width=pesos_aristas[i],
            edge_color=color_aris,
            alpha=alfa_aristas,
            connectionstyle='arc3,rad=0.25',
            style='solid',
            arrowstyle='->',
            arrowsize=max(10,pesos_aristas[i]*5),
            arrows=True,
            ax=eje,
        )    
        
    # REFERENCIAS
    ref_emig = mpatches.Patch(
        color=to_rgba(color_emigracion, alpha=alfa_aristas),
        label='Emigración'
    )    
    ref_inmig = mpatches.Patch(
        color=to_rgba(color_inmigracion, alpha=alfa_aristas), 
        label='Inmigración'
    )    
    
    ref_balance = mpatches.Patch(
        facecolor='none',
        label=f'• Balance migratorio: {convertir_valor(balance_mig, 1)}'
    )              
    ref_max_mig = mpatches.Patch(
        facecolor='none',
        label=f'• Máx. migrantes: {paises_max_migra} {convertir_valor(migra_max, 1)} '
    )
    
    lista_ref = [
        ref_emig,
        ref_inmig,
        ref_balance,
        ref_max_mig,
    ]
    if fondo_ref:
        color_fondo = 'white'
        color_borde = 'black'
        alfa_ref = .5
    else:        
        color_fondo = 'none'
        color_borde = 'none'
        alfa_ref = 0
        
    ref = eje.legend(
        title=f'{pais} {año}',
        handles=lista_ref,
        handlelength=2,
        handleheight=.7,
        loc=ubic_ref,
        fontsize=tam_tex_ref,
        frameon=True,
        facecolor=color_fondo,
        framealpha=alfa_ref,
        edgecolor=color_borde,
        alignment='left',
    )    
    ref.get_title().set_fontweight('bold')
    ref.get_title().set_fontsize(13)
    for text in ref.get_texts():
        text.set_color(color_etq_pais)
    eje.add_artist(ref)    
    
    fig.tight_layout()    
    plt.savefig(f'resultados/red_{pais}_{año}.png', bbox_inches='tight', dpi=300) 
    
    plt.close()
    
    return fig


















def obtener_df_pais(
    cod: str, df: pd.DataFrame, años: list[int], cols: list[str]
) -> pd.DataFrame:
    
    df_res = df[(df.iso2_orig == cod) & df.año.isin(años)].copy()
    df_res = (
        df_res.sort_values(['año', 'migrantes'], ascending=[True, False])
        .reset_index(drop=True)
    )[cols]

    return df_res


def calcular_emigraciones(
    origen: str, 
    año: int, 
    df: pd.DataFrame,
    dicc_vecinos: dict[str, set[str]],
    umbral_emig: int
) -> int:
    
    df = df[df.año == año].copy()
    
    # Total de emigrantes    
    total_emig = df.migrantes.sum() 

    # Población
    pobla = int(df['poblacion_orig'].iloc[0])
    
    # Porcentaje de emigrantes (respecto a la población)
    pct_pobla_emig = round(100 * total_emig / pobla, 1)
        
    # Distribución de la emigración: países que concentran el 90%
    df['pct_aporte'] = 100 * df.migrantes / total_emig
    df['pct_aporte_acum'] = df['pct_aporte'].cumsum()
    
    df_distri = df[df.pct_aporte_acum < umbral_emig]
    lista_distri_emig = [
        (des, f'{round(pct, 1)}%') 
        for des, pct 
        in zip(df_distri.iso2_des.values, df_distri.pct_aporte.values)
    ]    
    # Porcentaje de emigrantes en países limítrofes    
    df['a_limitrofe'] = df.iso2_des.isin(dicc_vecinos[origen])
    pct_en_limitrofe = round(100 * df[df.a_limitrofe].migrantes.sum() / total_emig, 1)

    return pobla, total_emig, pct_pobla_emig, pct_en_limitrofe, lista_distri_emig



def obtener_df_crisis(
    pais: str,
    df: pd.DataFrame,
    años: list[int],
    cols: list[str],
    dicc_vecinos: dict[str, set[str]],
    umbral_emig: int,
) -> pd.DataFrame:
    
    df_pais = obtener_df_pais(pais, df, años, cols)

    df_res = pd.DataFrame()
    for año in años:
        pobla, tot_emig, pct_emig, pct_limit, distri_emig = (
            calcular_emigraciones(pais, año, df_pais, dicc_vecinos, umbral_emig)
        )
        fila = pd.DataFrame(
            {
                'pais': [pais],
                'año': [año],
                'poblacion': [pobla],
                'emigrantes': [tot_emig],
                'pct_pobla_emigrante': [pct_emig],
                'pct_emig_limitrofe': [pct_limit],
                f'distri_emig_{umbral_emig-1}%': [distri_emig]
            }
        )
        df_res = pd.concat([df_res, fila])

    return df_res.reset_index(drop=True)







def preparar_gephi(df, año):
    df_year = df[df["año"] == año].copy()
    
    # Definimos las aristas
    aristas = (
        df_year.groupby(["iso3_orig", "iso3_des"], as_index=False).agg({"migrantes": "sum"})
        .rename(columns={
            "iso3_orig": "Source",
            "iso3_des": "Target",
            "migrantes": "Weight"
        })
    )
    
    # Definimos los nodos
    nodos_orig = df_year[["iso3_orig", "origen_ES", "poblacion_orig"]]\
        .rename(columns={
            "iso3_orig": "Id",
            "origen_ES": "Label",
            "poblacion_orig": "Population"
        })
    nodos_des = df_year[["iso3_des", "destino_ES", "poblacion_des"]]\
        .rename(columns={
            "iso3_des": "Id",
            "destino_ES": "Label",
            "poblacion_des": "Population"
        })

    nodos = (
        pd.concat([nodos_orig, nodos_des])
        .drop_duplicates(subset="Id")
    )
    
    return nodos, aristas





def format_combined(val, pct):
    if pd.isna(val) or pd.isna(pct) or val == 0:
        return ""
    
    if val >= 1_000_000:
        val_str = f"{val/1_000_000:.1f}M"
    elif val >= 1_000:
        val_str = f"{val/1_000:.1f}k"
    else:
        val_str = f"{int(val)}"
    
    return f"{pct:.1f}%\n{val_str}"

def graficar_limitrofes(tabla_vals,df_pct):

    annot_labels = pd.DataFrame(index=tabla_vals.index, columns=tabla_vals.columns)
    
    for i in tabla_vals.index:
        for j in tabla_vals.columns:
            annot_labels.loc[i, j] = format_combined(
                tabla_vals.loc[i, j],
                df_pct.loc[i, j]
            )
    
    sns.set_context("paper", font_scale=1.4)
    fig, ax = plt.subplots(figsize=(17, 5), dpi=120)  
    
    sns.heatmap(
        df_pct,
        annot=annot_labels,
        fmt="",
        cmap="rocket_r",
        linewidths=0,
        cbar_kws={'label': "Porcentaje de migración limítrofe",'shrink': 0.4,'pad': 0.05},
        annot_kws={"size": 13.4, "alpha": 0.95},
        ax=ax
    )
    
    for i in range(df_pct.shape[0] + 1):
        ax.axhline(i, color='white', lw=7, alpha=0.9)
    
    for j in range(df_pct.shape[1] + 1):
        ax.axvline(j, color='white', lw=0.2, alpha=0.3)
    
    ax.set_xticks(np.arange(len(df_pct.columns)) + 0.5)
    ax.set_xticklabels(df_pct.columns, rotation=0, fontsize=9)
    ax.set_yticklabels(df_pct.index, rotation=0, fontsize=10)
    
    ax.tick_params(axis='x', bottom=True, length=4, width=0.8, color='gray')
    ax.tick_params(axis='y', left=True, length=4, width=0.8, color='black')
    
    ax.set_xlabel(None)
    ax.set_ylabel(None)
    
    from matplotlib.patches import Rectangle
    for i in range(df_pct.shape[0]):
        rect = Rectangle((0, i),df_pct.shape[1],7,fill=False,edgecolor='lightgray',linewidth=7)
        ax.add_patch(rect)
    
    
    ax.tick_params(axis='x', labelsize=14)
    ax.tick_params(axis='y', labelsize=14)
    
    plt.tight_layout()
    #plt.savefig("heatmap_migracion.png", dpi=130, bbox_inches='tight')
    plt.show()



def plot_balance_migratorio(año, df, otro=False):
    """año = año para el que se quiere el balance migratorio
    df = dataframe con datos de migración
    otro = año para comparar (opcional)"""

    # Tomamos todos los ISO3 que aparezcan como origen o destino
    paises = set(df['iso3_orig'].dropna()) | set(df['iso3_des'].dropna())

    # Eliminar código inválido
    paises.discard("ZZZ")

    balance_dict = {pais: 0 for pais in paises}
    balance_dict_otro = {pais: 0 for pais in paises}
    for _, row in df.iterrows():
        if row['año'] == año: 
            iso_orig = row['iso3_orig']
            iso_dest = row['iso3_des']
            migrantes = row['migrantes']
            if pd.isna(migrantes):
                continue
            if iso_orig != "ZZZ" and iso_orig in balance_dict:
                balance_dict[iso_orig] -= migrantes
            if iso_dest != "ZZZ" and iso_dest in balance_dict:
                balance_dict[iso_dest] += migrantes
        elif otro is not False and row['año'] == otro:
            iso_orig = row['iso3_orig']
            iso_dest = row['iso3_des']
            migrantes = row['migrantes']
            if pd.isna(migrantes):
                continue
            if iso_orig != "ZZZ" and iso_orig in balance_dict:
                balance_dict_otro[iso_orig] -= migrantes
            if iso_dest != "ZZZ" and iso_dest in balance_dict:
                balance_dict_otro[iso_dest] += migrantes
    if otro is False:
        balance_dict_otro = balance_dict

    # Colores para barra
    colores = [
        (0.0, "#4d0b0b"),   # rojo oscuro (negativos)
        (0.45, "#ec5959"),  # transición
        (0.5, "#ecec9b"),   # 0
        (0.55, "#7ccead"),  # transición
        (1.0, "#104632")    # verde oscuro (positivos)
    ]
    cmap_alto_contraste = LinearSegmentedColormap.from_list("custom", colores)

    #Preparar mapa
    fig = plt.figure(figsize=(20,12))
    ax = plt.axes(projection=ccrs.Robinson())
    ax.set_global()
    ax.set_facecolor("#f0f0f0")
    ax.coastlines(linewidth=0.5)
    ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.4)
    # cmap = plt.cm.RdYlGn

    # Normalización para compara entre dos fechas
    vmin = min(min(balance_dict.values()), min(balance_dict_otro.values()))
    vmax = max(max(balance_dict.values()), max(balance_dict_otro.values()))
    abs_max = max(abs(vmin), abs(vmax))
    norm = TwoSlopeNorm(vmin=-abs_max, vcenter=0, vmax=abs_max)
    # norm = TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)
    # cmap = plt.cm.RdYlGn

    #Leer shapefile Natural Earth
    shapefile = shpreader.natural_earth(
        resolution='110m',
        category='cultural',
        name='admin_0_countries'
    )

    #Dibujar países
    reader = shpreader.Reader(shapefile)
    for country in reader.records():
        iso3 = country.attributes['ISO_A3']
        nombre = country.attributes['NAME']

        if nombre == 'France': # Ir agregando si descubrimos más que dan problemas
            iso3 = 'FRA'
        elif nombre == 'Norway':
            iso3 = 'NOR'
        elif nombre == 'Greenland':
            iso3 = 'DNK'
            
        geom = country.geometry
        if iso3 == "-99":
            continue
        value = balance_dict.get(iso3)
        if value is not None:
            facecolor = cmap_alto_contraste(norm(value))
        else:
            facecolor = "#d3d3d3" 
        ax.add_geometries(
            [geom],
            ccrs.PlateCarree(),
            facecolor=facecolor,
            edgecolor="black",
            linewidth=0.2
        )
    sm = plt.cm.ScalarMappable(cmap=cmap_alto_contraste, norm=norm)
    sm.set_array([])

    cbar = plt.colorbar(sm, ax=ax, orientation='vertical', fraction=0.05, pad=0.02,shrink=0.8)
    cbar.ax.tick_params(labelsize=38)
    cbar.ax.yaxis.get_offset_text().set_fontsize(40)
    # cbar.ax.set_position([0.80, 0.23, 0.02, 0.52])
    #cbar.set_label("Migrantes (1990)", fontsize=12)

    plt.title(f"Migrantes por país de origen ({año})", fontsize=18)
    plt.savefig(
        f"resultados/balance_migratorio_{año}.png",
        dpi=100,                 # calidad alta para impresión
        bbox_inches="tight",     # elimina márgenes blancos
        pad_inches=0.1,
        facecolor=fig.get_facecolor()
    )
    print(f"Mapa guardado como: resultados/balance_migratorio_{año}.png")
    plt.show()