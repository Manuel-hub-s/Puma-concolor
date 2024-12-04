# %% [markdown]
# # Puma concolor: Costa Rica

# %%
import streamlit as st
import pandas as pd
import plotly.express as px
import geopandas as gpd
import matplotlib.pyplot as plt
from streamlit_folium import folium_static, st_folium

# %%
# Rutas de los datos
Puma_concolor = 'Puma/puma_concolor.csv'  # CSV de Puma concolor
lim_provincias = 'Puma/provincias.gpkg'  # Archivo de límites provinciales

# %% [markdown]
st.title('Puma concolor: Costa Rica')
st.subheader('Manuel Peralta Reyes')

# %% [markdown]
# ## Función para cargar y procesar datos

@st.cache_data
def cargar_Puma_concolor():
    try:
        # Cargar el archivo CSV con tabulaciones como delimitador
        Pumaconcolor = pd.read_csv(Puma_concolor, delimiter="\t")
        
        # Eliminar espacios adicionales de los nombres de las columnas
        Pumaconcolor.columns = Pumaconcolor.columns.str.strip()
        
        # Reemplazar nombres de provincias para corregir inconsistencias
        if 'Provincia' in Pumaconcolor.columns:
            Pumaconcolor['Provincia'] = Pumaconcolor['Provincia'].replace({
                "Limon": "Limón",
                "San Jose": "San José"
            })
        

# %% [markdown]
# ## Función para cargar datos geoespaciales

@st.cache_data
def cargar_lim_provincias():
    try:
        provincias = gpd.read_file(lim_provincias)
        # Verificar y configurar CRS si es necesario
        if provincias.crs is None:
            provincias.set_crs("EPSG:4326", inplace=True)
        return provincias
    except Exception as e:
        st.error(f"Error al cargar los datos geoespaciales: {e}")
        return None

# %% [markdown]
# ## Cargar los datos

# Cargar datos de Ara ambiguus
MacaoAmbiguus_CR = cargar_Ara_MacaoAmbiguus()

#if MacaoAmbiguus_CR is not None:
    #st.write("Datos filtrados (Ara ambiguus) cargados con éxito.")
    #st.dataframe(MacaoAmbiguus_CR.head())  # Mostrar primeras filas
#else:
    #st.error("No se pudieron cargar los datos.")
    #st.stop()

# Cargar datos geoespaciales de las provincias
#carga_provinciasCR = st.text('Cargando datos de los límites de las provincias...')
provinciasCR = cargar_lim_provincias()
#carga_provinciasCR.text('Los límites de las provincias han sido cargados.')

#if provinciasCR is not None:
    #st.write("Columnas disponibles en provinciasCR:", provinciasCR.columns.tolist())
#else:
    #st.error("No se pudieron cargar las provincias.")
    #st.stop()

# %% [markdown]
# ## Agrupamiento por provincia

@st.cache_data
def agrupar_por_provincia(MacaoAmbiguus_CR):
    agrupado = MacaoAmbiguus_CR.groupby('Provincia')['Cuenta Individual'].sum().reset_index()
    agrupado.rename(columns={'Cuenta Individual': 'Total Cuenta Individual'}, inplace=True)
    return agrupado

# Agrupamiento por provincia
agrupado_MacaoAmbiguus_CR = agrupar_por_provincia(MacaoAmbiguus_CR)

# Mostrar los totales por provincia
#st.subheader('Totales por provincia (Ara ambiguus)')
#st.dataframe(agrupado_MacaoAmbiguus_CR)

# %% [markdown]
# ## Seleccionador por Provincia

# Generar la lista de provincias y agregar "Todas"
MacAmb_prov = agrupado_MacaoAmbiguus_CR['Provincia'].tolist()
MacAmb_prov.sort()
opciones_provincias = ['Todas'] + MacAmb_prov

provincia_seleccionada = st.sidebar.selectbox(
    'Selecciona una provincia:',
    opciones_provincias
)

# Filtrar los datos según la selección
if provincia_seleccionada != 'Todas':
    datos_filtrados = MacaoAmbiguus_CR[MacaoAmbiguus_CR['Provincia'] == provincia_seleccionada]
    datos_filtrados_agrupados = agrupado_MacaoAmbiguus_CR[
        agrupado_MacaoAmbiguus_CR['Provincia'] == provincia_seleccionada
    ]
else:
    datos_filtrados = MacaoAmbiguus_CR.copy()
    datos_filtrados_agrupados = agrupado_MacaoAmbiguus_CR.copy()

# Mostrar los datos filtrados
st.subheader(f'Datos filtrados para: {provincia_seleccionada}')
st.dataframe(datos_filtrados)

# %% [markdown]
# ## Gráfico de Totales por Provincia

fig_totales = px.bar(
    datos_filtrados_agrupados,
    x='Provincia',
    y='Total Cuenta Individual',
    title=f'Totales de Ara ambiguus para {provincia_seleccionada}',
    labels={'Provincia': 'Provincia', 'Total Cuenta Individual': 'Total Cuenta Individual'},
    color='Provincia'
)
st.plotly_chart(fig_totales)

# %% [markdown]
# ## Mapa de Totales por Provincia

if provinciasCR is not None:
    provinciasCR['Total Cuenta Individual'] = provinciasCR['provincia'].map(
        datos_filtrados_agrupados.set_index('Provincia')['Total Cuenta Individual']
    ).fillna(0)

    try:
        # Crear el mapa cloroplético
        m_totales = provinciasCR.explore(
            column='Total Cuenta Individual',
            name='Total Cuenta Individual',
            cmap='YlGn',
            tooltip=['provincia', 'Total Cuenta Individual'],
            legend=True,
            legend_kwds={
                'caption': f"Totales de Ara ambiguus para {provincia_seleccionada}",
                'orientation': "horizontal"
            }
        )
        st.subheader(f'Totales de Ara ambiguus en {provincia_seleccionada if provincia_seleccionada != "Todas" else "Costa Rica"}')
        st_folium(m_totales, width=700, height=600)
    except Exception as e:
        st.error(f"Error al generar el mapa interactivo: {e}")
else:
    st.error("No se pudieron cargar los datos de provincias.")
