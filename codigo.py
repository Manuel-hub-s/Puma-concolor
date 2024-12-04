# %% [markdown]
# # Puma concolor: Costa Rica

# %%
import streamlit as st
import pandas as pd
import plotly.express as px
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from folium import plugins
from folium import Map

# %%
# Rutas de los datos
Puma_concolor = 'Puma/puma_concolor.csv'  # CSV de Puma concolor
lim_provincias = 'Puma/provincias.gpkg'  # Archivo de límites provinciales

# %% [markdown]
st.title('Puma concolor en Costa Rica')
st.subheader('Manuel Peralta Reyes')

# %% [markdown]
# ## Función para cargar y procesar datos

@st.cache_data
def cargar_Puma_concolor():
    try:
        # Cargar datos del CSV
        Pumaconcolor = pd.read_csv(Puma_concolor, delimiter="\t")
        # Limpiar nombres de columnas
        Pumaconcolor.columns = Pumaconcolor.columns.str.strip()
        # Corrección de nombres de provincias
        if 'Provincia' in Pumaconcolor.columns:
            Pumaconcolor['Provincia'] = Pumaconcolor['Provincia'].replace({
                "Limon": "Limón",
                "San Jose": "San José"
            })
        return Pumaconcolor
    except Exception as e:
        st.error(f"Error al cargar el archivo CSV: {e}")
        return None

# %% [markdown]
# ## Función para cargar datos geoespaciales

@st.cache_data
def cargar_lim_provincias():
    try:
        provincias = gpd.read_file(lim_provincias)
        # Verificar y configurar CRS
        if provincias.crs is None:
            provincias.set_crs("EPSG:4326", inplace=True)
        return provincias
    except Exception as e:
        st.error(f"Error al cargar los datos geoespaciales: {e}")
        return None

# %% [markdown]
# ## Función para agrupar por provincia y especie

@st.cache_data
def agrupar_por_provincia_y_especie(Pumaconcolor):
    try:
        # Agrupar datos por provincia y especie
        agrupado = Pumaconcolor.groupby(['Provincia', 'Especie'])['Cuenta individual'].sum().reset_index()
        agrupado.rename(columns={'Cuenta individual': 'Total avistamientos'}, inplace=True)
        return agrupado
    except KeyError:
        st.error("No se encontraron las columnas necesarias en los datos.")
        return None

# %% [markdown]
# ## Cargar los datos

# Cargar datos de Puma concolor
Pumaconcolor = cargar_Puma_concolor()

# Verificar si los datos fueron cargados correctamente
if Pumaconcolor is None:
    st.stop()

# Cargar datos geoespaciales de las provincias
provincias = cargar_lim_provincias()

# Verificar si los datos geoespaciales fueron cargados correctamente
if provincias is None:
    st.stop()

# %% [markdown]
# ## Agrupamiento por provincia y especie

# Agrupar datos por provincia y especie
agrupado_Pumaconcolor = agrupar_por_provincia_y_especie(Pumaconcolor)

if agrupado_Pumaconcolor is None:
    st.stop()

# %% [markdown]
# ## Seleccionador por Provincia

# Crear lista de provincias para el selector
provincias_lista = agrupado_Pumaconcolor['Provincia'].unique().tolist()
provincias_lista.sort()
opciones_provincias = ['Todas'] + provincias_lista

provincia_seleccionada = st.sidebar.selectbox(
    'Selecciona una provincia:',
    opciones_provincias
)

# Filtrar los datos según la provincia seleccionada
if provincia_seleccionada != 'Todas':
    datos_filtrados = Pumaconcolor[Pumaconcolor['Provincia'] == provincia_seleccionada]
    datos_filtrados_agrupados = agrupado_Pumaconcolor[agrupado_Pumaconcolor['Provincia'] == provincia_seleccionada]
else:
    datos_filtrados = Pumaconcolor.copy()
    datos_filtrados_agrupados = agrupado_Pumaconcolor.copy()

# Mostrar los datos filtrados
st.subheader(f'Datos para la provincia {provincia_seleccionada}')
st.dataframe(datos_filtrados)

# %% [markdown]
# ## Gráfico de Totales por Provincia y Especie

# Colores
colores_hex = [
    "#fff7ec",
    "#fee8c8",
    "#fdd49e",
    "#fdbb84",
    "#fc8d59",
    "#ef6548",
    "#d7301f",
    "#b30000",
    "#7f0000"
]

graf = px.bar(
    datos_filtrados_agrupados,
    x='Especie',
    y='Total avistamientos',
    title=f'Totales de avistamientos en {provincia_seleccionada}',
    labels={'Especie': 'Especie', 'Total avistamientos': 'Total de avistamientos'},
    color='Provincia',
    color_discrete_sequence=colores_hex
)
st.plotly_chart(graf)

# %% [markdown]
# ## Mapa de Totales por Provincia

if provincias is not None:
    # Vincular los datos con el GeoDataFrame
    provincias['Total avistamientos'] = provincias['provincia'].map(
        datos_filtrados_agrupados.groupby('Provincia')['Total avistamientos'].sum()
    ).fillna(0)

    try:
        # Crear el mapa base inicial (OpenStreetMap)
        mapa = folium.Map(location=[9.7489, -83.7534], zoom_start=7, tiles="openstreetmap")
        
        # Crear capas de mapas base adicionales
        folium.TileLayer('cartodb positron').add_to(mapa)
        folium.TileLayer('cartodb dark_matter').add_to(mapa)
        folium.TileLayer('Stamen Terrain').add_to(mapa)
        folium.TileLayer('Stamen Toner').add_to(mapa)
        folium.TileLayer('Stamen Watercolor').add_to(mapa)

        # Añadir la capa de mapa base de OpenStreetMap como predeterminada
        folium.TileLayer('openstreetmap').add_to(mapa)
        
        # Añadir control de capas (permitiendo cambiar de mapa base)
        folium.LayerControl().add_to(mapa)
        
        # Agregar los datos de provincias con los valores de avistamientos
        folium.Choropleth(
            geo_data=provincias,
            name='Total avistamientos',
            data=provincias,
            columns=['provincia', 'Total avistamientos'],
            key_on='feature.properties.provincia',  # Asegúrate de que el nombre de la provincia coincida en tus datos
            fill_color='OrRd',
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name='Total de Avistamientos'
        ).add_to(mapa)

        # Mostrar el mapa interactivo
        st.subheader(f'Total de avistamientos de Puma concolor en {provincia_seleccionada if provincia_seleccionada != "Todas" else "Costa Rica"}')
        st_folium(mapa, width=700, height=600)

    except Exception as e:
        st.error(f"Error al generar el mapa interactivo: {e}")
else:
    st.error("No se pudieron cargar los datos geoespaciales.")
