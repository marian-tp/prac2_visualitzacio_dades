import streamlit as st
import pandas as pd
import folium
import geopandas as gpd
from streamlit_folium import folium_static
import plotly.express as px
import plotly.graph_objects as go

# Configuración de pandas para mostrar todas las columnas y filas
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

# Carga de datos
df_lloguer = pd.read_excel('conjunt_dades.xlsx', sheet_name='Lloguer_BCN_districte')
df_inflacio = pd.read_excel('conjunt_dades.xlsx', sheet_name='inflacio')
df_lloguer_barri = pd.read_excel('conjunt_dades.xlsx', sheet_name='Lloguer_BCN_barri')
df_compra = pd.read_excel('conjunt_dades.xlsx', sheet_name='Compra_BCN_districte')
df_compra_barri = pd.read_excel('conjunt_dades.xlsx', sheet_name='Compra_BCN_barri')
df_habitatges_turistic = pd.read_csv('habitatges_us_turistic.csv', delimiter=',')
df_renda_lloguer = pd.read_excel('conjunt_dades.xlsx', sheet_name='renda_lloguer_BCN')
df_padro_obra_nova = pd.read_excel('conjunt_dades.xlsx', sheet_name='padro_obra_nova')
df_padro_obra_nova_districtes = df_padro_obra_nova.groupby(['any', 'districtes municipals']).sum().reset_index()

# Preprocesamiento de datos
df_habitatges_turistic = df_habitatges_turistic.dropna(subset=['LATITUD_Y', 'LONGITUD_X'])
df_habitatges_turistic = df_habitatges_turistic[
    (df_habitatges_turistic['LATITUD_Y'] != '') & 
    (df_habitatges_turistic['LONGITUD_X'] != '') & 
    (df_habitatges_turistic['LATITUD_Y'].apply(lambda x: isinstance(x, (int, float)))) &
    (df_habitatges_turistic['LONGITUD_X'].apply(lambda x: isinstance(x, (int, float))))
]

# Cálculo de los cuartiles y el índice acumulado de inflación
df_quantils = df_lloguer.groupby('any')['lloguer'].quantile([0.25, 0.5, 0.75]).unstack()
df_quantils.columns = ['Q1', 'mediana/Q2', 'Q3']
df_quantils = df_quantils.reset_index()

df_inflacio['index_acumulat'] = 100  # Índice base 100 para 2013
for i in range(1, len(df_inflacio)):
    df_inflacio.loc[i, 'index_acumulat'] = df_inflacio.loc[i-1, 'index_acumulat'] * (1 + df_inflacio.loc[i, 'variacio_IPC'] / 100)

df_lloguer_inflacio = pd.merge(df_quantils, df_inflacio, on='any')
df_lloguer_inflacio['Q1_ajustat'] = df_lloguer_inflacio['Q1'] * 100 / df_lloguer_inflacio['index_acumulat']
df_lloguer_inflacio['mediana/Q2_ajustat'] = df_lloguer_inflacio['mediana/Q2'] * 100 / df_lloguer_inflacio['index_acumulat']
df_lloguer_inflacio['Q3_ajustat'] = df_lloguer_inflacio['Q3'] * 100 / df_lloguer_inflacio['index_acumulat']

# Creación de los mapas con Folium
def crear_mapa_districtes(any, compra_lloguer, habitatges_turistics):
    colors = {'rang baix': 'green', 'rang mitjà': 'yellow', 'rang alt': 'red'}
    mapa = folium.Map(location=[41.3851, 2.1734], zoom_start=11)

    if compra_lloguer == 'Lloguer':
        gdf_districtes_mapa = gdf_lloguer_districtes[gdf_lloguer_districtes['any'] == any]
    else:
        gdf_districtes_mapa = gdf_compra_districtes[gdf_compra_districtes['any'] == any]

    folium.GeoJson(
        gdf_districtes_mapa,
        style_function=lambda feature: {
            'fillColor': colors.get(feature['properties'].get('categoria', 'grey'), 'grey'),
            'color': 'black',
            'weight': 2,
            'fillOpacity': 0.5
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['NOM'],
            aliases=['Barri:'],
            localize=True,
        ),
        popup=folium.GeoJsonPopup(
            fields=['NOM', 'lloguer'],
            aliases=['Barri:', 'Lloguer mitjà:'],
            localize=True
        ),
        highlight_function=lambda x: {'weight': 3, 'color': 'blue'}
    ).add_to(mapa)

    if habitatges_turistics:
        fol = folium.FeatureGroup(name='Habitatges turístics')
        for id, fila in df_habitatges_turistic.iterrows():
            folium.CircleMarker(
                location=[fila['LATITUD_Y'], fila['LONGITUD_X']],
                radius=0.05,
                color='blue',
                fill=True,
                fill_color='blue',
                fill_opacity=0.6,
                popup=fila.get('CARRER', 'No hi ha adressa') 
            ).add_to(fol)
        fol.add_to(mapa)
        folium.LayerControl().add_to(mapa)
    return mapa

# Creación de los mapas por barrios
def crear_mapa_barris(any, compra_lloguer, habitatges_turistics):
    colors = {'rang baix': 'green', 'rang mitjà': 'yellow', 'rang alt': 'red'}
    mapa = folium.Map(location=[41.3851, 2.1734], zoom_start=11)

    if compra_lloguer == 'Lloguer':
        gdf_barris_mapa = gdf_lloguer_barris[gdf_lloguer_barris['any'] == any]
    else:
        gdf_barris_mapa = gdf_compra_barris[gdf_compra_barris['any'] == any]

    folium.GeoJson(
        gdf_barris_mapa,
        style_function=lambda feature: {
            'fillColor': colors.get(feature['properties'].get('categoria', 'grey'), 'grey'),
            'color': 'black',
            'weight': 2,
            'fillOpacity': 0.5
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['NOM'],
            aliases=['Barri:'],
            localize=True,
        ),
        popup=folium.GeoJsonPopup(
            fields=['NOM', 'lloguer'],
            aliases=['Barri:', 'Lloguer mitjà:'],
            localize=True
        ),
        highlight_function=lambda x: {'weight': 3, 'color': 'blue'}
    ).add_to(mapa)

    if habitatges_turistics:
        fol = folium.FeatureGroup(name='Habitatges turístics')
        for id, fila in df_habitatges_turistic.iterrows():
            folium.CircleMarker(
                location=[fila['LATITUD_Y'], fila['LONGITUD_X']],
                radius=0.05,
                color='blue',
                fill=True,
                fill_color='blue',
                fill_opacity=0.6,
                popup=fila.get('CARRER', 'No hi ha adressa') 
            ).add_to(fol)
        fol.add_to(mapa)
        folium.LayerControl().add_to(mapa)
    return mapa

# Interfaz de Streamlit
st.title("Sector de l'habitatge a Barcelona")

opcio_barris_districtes = st.radio("Selecciona mapa:", ['Mapa de Barris', 'Mapa de Districtes'])
opcio_compra_lloguer = st.radio("Selecciona entre les opcions compra i lloguer:", ['Compra', 'Lloguer'])
opcio_any = st.selectbox("Selecciona l'any:", range(2013, 2024))
opcio_habitatges_turistics = st.checkbox('Mostrar habitatges turístics')

if opcio_barris_districtes == 'Mapa de Barris':
    mapa = crear_mapa_barris(opcio_any, opcio_compra_lloguer, opcio_habitatges_turistics)
else:
    mapa = crear_mapa_districtes(opcio_any, opcio_compra_lloguer, opcio_habitatges_turistics)

folium_static(mapa)

st.header("Lloguer i renda per districtes del 2015 al 2021")
opcio_districte = st.multiselect(
    "Selecciona districtes:",
    df_renda_lloguer['Districtes municipals'].unique(),
    default=['Barcelona']
)

st.header("Evolució de l'obra nova i el padró a Barcelona")
opcio_grafic_barres = st.selectbox("Selecciona l'any:", df_padro_obra_nova_districtes['any'].unique())

# Ejemplo de gráficos con Plotly
# Lloguer i renda per districtes
df_compra_seleccio = df_renda_lloguer[df_renda_lloguer['Districtes municipals'].isin(opcio_districte)]

fig_lloguer = px.line(df_compra_seleccio, x='Any', y='mitjana_preu_lloguer', color='Districtes municipals',
                  labels={'mitjana_preu_lloguer': 'Mitjana Preu Lloguer'}, title="Mitjana Preu Lloguer")
fig_renda = px.line(df_compra_seleccio, x='Any', y='renda_mitjana_mensual', color='Districtes municipals',
                   labels={'renda_mitjana_mensual': 'Renda Mitjana Mensual'}, title="Renda Mitjana Mensual")

for trace in fig_renda.data:
    trace.update(line=dict(dash='dash'))
    fig_lloguer.add_trace(trace)

fig_lloguer.update_layout(
    xaxis_title="Any",
    yaxis_title="Cantidad",
    legend_title="Districtes municipals",
    template="plotly_white"
)
fig_lloguer.update_traces(mode='lines+markers')
fig_lloguer.update_yaxes(title_text="Mitjana preu lloguer / Renda mitjana mensual")

st.plotly_chart(fig_lloguer)

# Evolució de l'obra nova i el padró
df_any = df_padro_obra_nova_districtes[df_padro_obra_nova_districtes['any'] == opcio_grafic_barres]
fig_bars = go.Figure(data=[
    go.Bar(name='Obra Nova', x=df_any['districtes municipals'], y=df_any['obra_nova']),
    go.Bar(name='Evolució del Padró', x=df_any['districtes municipals'], y=df_any['evolucio_padro'], marker_pattern_shape="/")
])
fig_bars.update_layout(
    title=f"Evolució de l'obra nova i el padró a Barcelona - {opcio_grafic_barres}",
    xaxis_title="Districtes",
    yaxis_title="Valor",
    barmode='group',
    xaxis_tickangle=-45,
    yaxis=dict(range=[-25000, 25000])
)

st.plotly_chart(fig_bars)
