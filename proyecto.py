
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import folium
import streamlit as st
import plotly.express as px
from numerize.numerize import numerize
from decimal import Decimal
import streamlit_folium


st.set_page_config(page_title='CATALOGO SISMICO 1960-2021 (IGP)',
                   layout='wide',
                   initial_sidebar_state='collapsed')

@st.cache_data()
def get_data():
    df = pd.read_excel('data/Terremotos.xlsx')
    df['FECHA_UTC'] = pd.to_datetime(df['FECHA_UTC'], format='%Y%m%d')
    df['FECHA_UTC'] = df['FECHA_UTC'].dt.strftime('%Y-%m-%d')
    df['HORA_UTC'] = pd.to_datetime(df['HORA_UTC'].astype(str).str.zfill(6), format='%H%M%S').dt.strftime('%H:%M:%S')
    df = df.drop(columns=['FECHA_CORTE'])
    return df

df = get_data()

header_left, header_mid, header_right = st.columns([1, 2, 1], gap='large')

with header_mid:
     st.title('CATALOGO SISMICO 1960-2021 (IGP)')

magnitudes_ordenadas = df['MAGNITUD'].sort_values().unique()
horas_del_dia = [str(h).zfill(2) for h in range(24)]


# Convertir las columnas de latitud y longitud a objetos Point de shapely
geometry = [Point(lon, lat) for lon, lat in zip(df['LONGITUD'], df['LATITUD'])]

# Crear un GeoDataFrame a partir del DataFrame 'df'
gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')

# Cargar el archivo GeoJSON o Shapefile que contiene los límites de los departamentos
departamentos = gpd.read_file('data/peru_departamental_simple.geojson')

# Asegurarse de que la columna 'NOMBDEP' en 'departamentos' sea el índice
departamentos.set_index('NOMBDEP', inplace=True)

# Realizar una fusión espacial para obtener el departamento correspondiente a cada punto
gdf = gpd.sjoin(gdf, departamentos, how='left', op='within')

gdf.rename(columns={'index_right': 'DEPARTAMENTO'}, inplace=True)

gdf.dropna(subset=['DEPARTAMENTO'], inplace=True)
gdf.dropna(subset=['DEPARTAMENTO'], inplace=True)

departamentos_unicos = gdf['DEPARTAMENTO'].unique()

with st.sidebar:
    st.sidebar.markdown('<h3 style="color: white; font-size: 24px;">Seleccione Departamento:</h3>', unsafe_allow_html=True)
    Departamento_filter = st.multiselect(label=' ',
                                   options=departamentos_unicos, default = departamentos_unicos)
#Filtra solo las columnas numérica

# Calcular la cantidad de terremotos por departamento
terremotos_por_departamento = gdf['DEPARTAMENTO'].value_counts()

# Obtener el departamento con mayor cantidad de terremotos
departamento_max_terremotos = terremotos_por_departamento.idxmax()
cantidad_max_terremotos = terremotos_por_departamento.max()

# Obtener el departamento con menor cantidad de terremotos
departamento_min_terremotos = terremotos_por_departamento.idxmin()
cantidad_min_terremotos = terremotos_por_departamento.min()

# Encontrar el índice del sismo con la mayor profundidad
indice_sismo_mayor_profundidad = gdf['PROFUNDIDAD'].idxmax()

# Obtener los datos del sismo con mayor profundidad
sismo_mayor_profundidad = gdf.loc[indice_sismo_mayor_profundidad]

# Filtrar los registros que no tienen valor NaN en la columna de magnitud
df_sin_nan_magnitud = gdf.dropna(subset=['MAGNITUD'])

# Verificar si hay registros después de filtrar los NaN
if df_sin_nan_magnitud.empty:
    st.write("No hay sismos con magnitud registrada.")
else:
    # Agrupar los datos por departamento y calcular la magnitud máxima para cada grupo
    magnitud_maxima_por_departamento = df_sin_nan_magnitud.groupby('DEPARTAMENTO')['MAGNITUD'].max()

    # Encontrar el departamento con la mayor magnitud máxima
    departamento_max_magnitud = magnitud_maxima_por_departamento.idxmax()
    magnitud_maxima = magnitud_maxima_por_departamento.max()

#Calcula las sumas de las columnas numéricas y convierte a float
total_terremotos = terremotos_por_departamento.sum()
total_clicks = cantidad_max_terremotos
total_spent = cantidad_min_terremotos
total_conversions = sismo_mayor_profundidad['PROFUNDIDAD']
total_approved_conversions = magnitud_maxima

# Convierte los valores float a objetos Decimal
total_terremotos = Decimal(str(total_terremotos))
total_clicks = Decimal(str(total_clicks))
total_spent = Decimal(str(cantidad_min_terremotos))
total_conversions = Decimal(str(total_conversions))
total_approved_conversions = Decimal(str(total_approved_conversions))

total1, total2, total3, total4, total5 = st.columns(5, gap='large')

with total1:
    st.image('images/impression.png',use_column_width='Auto')
    st.metric(label = 'Total Terremotos', value= numerize(total_terremotos))
    
with total2:
    st.image('images/tap.png',use_column_width='Auto')
    st.metric(label=f"Terremoto Máximo: {departamento_max_terremotos}", value=numerize(total_clicks))

with total3:
    st.image('images/hand.png',use_column_width='Auto')
    st.metric(label= f'Terremoto Minímo: {departamento_min_terremotos}',value=numerize(total_spent,2))

with total4:
    st.image('images/conversion.png',use_column_width='Auto')
    st.metric(label=f"Terremoto con Mayor Profundidad: {sismo_mayor_profundidad['DEPARTAMENTO']}",value=numerize(total_conversions))

with total5:
    st.image('images/app_conversion.png',use_column_width='Auto')
    st.metric(label=f"Terremoto con Mayor Magnitud: {departamento_max_magnitud}",value=numerize(total_approved_conversions))

Q1,Q2 = st.columns(2)

with Q1:

    # Eliminar los valores NaN de la columna 'MAGNITUD'
    df_sin_nan_magnitud = gdf.dropna(subset=['MAGNITUD'])

    # Filtrar los datos según los departamentos seleccionados en el filtro
    df_filtrado = df_sin_nan_magnitud[df_sin_nan_magnitud['DEPARTAMENTO'].isin(Departamento_filter)]

    # Calcular la cantidad de terremotos por departamento
    terremotos_por_departamento = df_filtrado['DEPARTAMENTO'].value_counts().reset_index()
    terremotos_por_departamento.columns = ['DEPARTAMENTO', 'Cantidad']

    # Ordenar el DataFrame por la cantidad de terremotos de mayor a menor
    terremotos_por_departamento = terremotos_por_departamento.sort_values(by='Cantidad', ascending=False)

    # Crear el gráfico de barras con Plotly Express
    fig = px.bar(terremotos_por_departamento, x='DEPARTAMENTO', y='Cantidad', 
                title='Cantidad de Terremotos por Departamento (Ordenado de Mayor a Menor)',
                labels={'DEPARTAMENTO': 'Departamento', 'Cantidad': 'Cantidad de Terremotos'})

    # Mostrar el gráfico de barras en el dashboard
    st.plotly_chart(fig)

with Q2:
    # Obtener la cantidad de terremotos por departamento
    terremotos_por_departamento = gdf['DEPARTAMENTO'].value_counts()
    # Seleccionar los 5 departamentos con mayor cantidad de terremotos
    top5_departamentos = terremotos_por_departamento.nlargest(5)

    # Crear un DataFrame con los datos del top 5
    top5_df = pd.DataFrame({'Departamento': top5_departamentos.index, 'Cantidad de Terremotos': top5_departamentos.values})

    # Crear el gráfico de pastel con Plotly Express
    fig = px.pie(top5_df, names='Departamento', values='Cantidad de Terremotos',
                title='Top 5 Departamentos con Mayor Cantidad de Terremotos',
                labels={'Cantidad de Terremotos': 'Cantidad de Terremotos'})

    # Mostrar el gráfico de pastel en el dashboard
    st.plotly_chart(fig)

# Convertir la columna 'FECHA_UTC' a formato de fecha
gdf['FECHA_UTC'] = pd.to_datetime(gdf['FECHA_UTC'])

# Obtener el año de cada terremoto
gdf['AÑO'] = gdf['FECHA_UTC'].dt.year

# Filtrar los datos según los departamentos seleccionados en el filtro
if Departamento_filter:
    gdf_filtrado = gdf[gdf['DEPARTAMENTO'].isin(Departamento_filter)]
else:
    gdf_filtrado = gdf

# Obtener la cantidad de terremotos por año
terremotos_por_año = gdf_filtrado['AÑO'].value_counts()

# Crear un DataFrame con los datos de la cantidad de terremotos por año
terremotos_por_año_df = pd.DataFrame({'Año': terremotos_por_año.index, 'Cantidad de Terremotos': terremotos_por_año.values})

# Ordenar los datos por año
terremotos_por_año_df = terremotos_por_año_df.sort_values(by='Año')

# Crear el gráfico de barras con Plotly Express
fig = px.bar(terremotos_por_año_df, x='Año', y='Cantidad de Terremotos',
            title='Cantidad de Terremotos por Año',
            labels={'Año': 'Año', 'Cantidad de Terremotos': 'Cantidad de Terremotos'})

# Mostrar el gráfico de barras en el dashboard con el argumento use_container_width=True
st.plotly_chart(fig, use_container_width=True)

############################
# Leer el archivo shapefile de los departamentos de Perú
shapefile_path = 'Peru/per_admbnda_adm1_ign_20200714.shp'
departamento = gpd.read_file(shapefile_path)

df1 = gdf.drop(columns='geometry')


  # Unir los datos del shapefile con el DataFrame df
departamentos1 = departamento.merge(df1, left_on='ADM1_ES', right_on='DEPARTAMENTO', how='left')

departamentos1 = departamentos1.dropna(subset=['LATITUD', 'LONGITUD'])

# Crear la aplicación de Streamlit
def main():
    st.title("Visualización de Terremotos por Departamento")

    # Mostrar los primeros registros del DataFrame de terremotos
    st.subheader("Primeros registros de terremotos:")
    st.dataframe(df.head())

    # Crear el mapa de departamentos con colores según la magnitud
    st.subheader("Mapa de Departamentos con Magnitud de Terremotos")
    mapa_departamentos = folium.Map(location=[-9.19, -75.015], zoom_start=5)

    for index, row in departamentos1.iterrows():
        folium.Marker(
            location=[row['LATITUD'], row['LONGITUD']],
            popup=f"Departamento: {row['DEPARTAMENTO']}<br>Magnitud: {row['MAGNITUD']}",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(mapa_departamentos)

    st.write(mapa_departamentos)

    # Crear un gráfico de barras para mostrar la magnitud promedio por departamento
    st.subheader("Magnitud Promedio por Departamento")
    magnitudes_promedio = departamentos1.groupby('DEPARTAMENTO')['MAGNITUD'].mean()
    st.bar_chart(magnitudes_promedio)

    # Puedes seguir agregando más visualizaciones según tus necesidades

if __name__ == "__main__":
    main()


