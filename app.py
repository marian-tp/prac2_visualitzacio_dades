import pandas as pd
import folium
from scipy.spatial import Voronoi
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import folium
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import os




pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)


df_lloguer = pd.read_excel('conjunt_dades.xlsx', sheet_name='Lloguer_BCN_districte')
df_inflacio = pd.read_excel('conjunt_dades.xlsx', sheet_name = 'inflacio')
df_lloguer_barri = pd.read_excel('conjunt_dades.xlsx', sheet_name = 'Lloguer_BCN_barri')
df_compra = pd.read_excel('conjunt_dades.xlsx', sheet_name = 'Compra_BCN_districte')
df_compra_barri = pd.read_excel('conjunt_dades.xlsx', sheet_name = 'Compra_BCN_barri')

df_habitatges_turistic = pd.read_csv('habitatges_us_turistic.csv', delimiter=',')

df_habitatges_turistic = df_habitatges_turistic.dropna(subset=['LATITUD_Y', 'LONGITUD_X'])

df_habitatges_turistic = df_habitatges_turistic[
    (df_habitatges_turistic['LATITUD_Y'] != '') & 
    (df_habitatges_turistic['LONGITUD_X'] != '') & 
    (df_habitatges_turistic['LATITUD_Y'].apply(lambda x: isinstance(x, (int, float)))) &
    (df_habitatges_turistic['LONGITUD_X'].apply(lambda x: isinstance(x, (int, float))))
]



df_renda_lloguer = pd.read_excel('conjunt_dades.xlsx', sheet_name = 'renda_lloguer_BCN')

df_padro_obra_nova = pd.read_excel('conjunt_dades.xlsx', sheet_name = 'padro_obra_nova')
df_padro_obra_nova_districtes = df_padro_obra_nova.groupby(['any', 'districtes municipals']).sum().reset_index()




# DISTRICTES

# CÀLCUL DELS QUANTILS

df_quantils = df_lloguer.groupby('any')['lloguer'].quantile([0.25, 0.5, 0.75]).unstack()
df_quantils.columns = ['Q1', 'mediana/Q2', 'Q3']
df_quantils = df_quantils.reset_index()


# CÀLCUL DE L'INDEX ACUMULAT

df_inflacio['index_acumulat'] = 100  # Índex base 100 pel 2013
for i in range(1, len(df_inflacio)):
    df_inflacio.loc[i, 'index_acumulat'] = df_inflacio.loc[i-1, 'index_acumulat'] * (1 + df_inflacio.loc[i, 'variacio_IPC'] / 100)
df_inflacio


# Es realitza un merge per obtenir un df combinat del 'df_alquiler' i 'df_inflacio'
df_lloguer_inflacio = pd.merge(df_quantils, df_inflacio, on='any')

# Es calculen els valors ajustats per les variacions de l'IPC
df_lloguer_inflacio['Q1_ajustat'] = df_lloguer_inflacio['Q1'] * 100 / df_lloguer_inflacio['index_acumulat']
df_lloguer_inflacio['mediana/Q2_ajustat'] = df_lloguer_inflacio['mediana/Q2'] * 100 / df_lloguer_inflacio['index_acumulat']
df_lloguer_inflacio['Q3_ajustat'] = df_lloguer_inflacio['Q3'] * 100 / df_lloguer_inflacio['index_acumulat']

df_lloguer_inflacio[['any', 'Q1_ajustat', 'mediana/Q2_ajustat', 'Q3_ajustat']]


lloguers_ajustats = pd.concat([df_lloguer_inflacio['Q1_ajustat'], df_lloguer_inflacio['mediana/Q2_ajustat'], df_lloguer_inflacio['Q3_ajustat']])

quantile_33 = lloguers_ajustats.quantile(0.3333)
quantile_66 = lloguers_ajustats.quantile(0.6667)


# CÀLCUL DELS LLOGUERS AMB LES VARIACIONS DE L'IPC DESCOMPTADES

df_lloguer_districte = df_lloguer[df_lloguer['districtes municipals'] != 'Barcelona']

df_inflacio['acumulacio'] = (1 + df_inflacio['variacio_IPC'] / 100).cumprod()

# Es normalitza de manera que l'any base 2013 té com a valor 1
df_inflacio['acumulacio'] /= df_inflacio.loc[df_inflacio['any'] == 2013, 'acumulacio'].values[0]


# S'uneixen els df en la columna 'any'
df_lloguer_mapa = pd.merge(df_lloguer_districte, df_inflacio[['any', 'acumulacio']], on='any', how='left')

# Es calcula el 'lloguer_ajustat'
df_lloguer_mapa['lloguer_ajustat'] = df_lloguer_mapa['lloguer'] / df_lloguer_mapa['acumulacio']

columnes = ['codi', 'districtes municipals', 'any', 'lloguer', 'lloguer_ajustat']
df_lloguer_mapa = df_lloguer_mapa[columnes]



# COMPRA DISTRICTES


# CÀLCUL DELS QUANTILS

df_quantils = df_compra.groupby('any')['lloguer'].quantile([0.25, 0.5, 0.75]).unstack()
df_quantils.columns = ['Q1', 'mediana/Q2', 'Q3']
df_quantils = df_quantils.reset_index()


# CÀLCUL DE L'INDEX ACUMULAT

df_inflacio['index_acumulat'] = 100  # Índex base 100 pel 2013
for i in range(1, len(df_inflacio)):
    df_inflacio.loc[i, 'index_acumulat'] = df_inflacio.loc[i-1, 'index_acumulat'] * (1 + df_inflacio.loc[i, 'variacio_IPC'] / 100)
df_inflacio


# Es realitza un merge per obtenir un df combinat del 'df_alquiler' i 'df_inflacio'
df_compra_inflacio = pd.merge(df_quantils, df_inflacio, on='any')

# Es calculen els valors ajustats per les variacions de l'IPC
df_compra_inflacio['Q1_ajustat'] = df_compra_inflacio['Q1'] * 100 / df_compra_inflacio['index_acumulat']
df_compra_inflacio['mediana/Q2_ajustat'] = df_compra_inflacio['mediana/Q2'] * 100 / df_compra_inflacio['index_acumulat']
df_compra_inflacio['Q3_ajustat'] = df_compra_inflacio['Q3'] * 100 / df_compra_inflacio['index_acumulat']

df_compra_inflacio[['any', 'Q1_ajustat', 'mediana/Q2_ajustat', 'Q3_ajustat']]



compra_ajustats = pd.concat([df_compra_inflacio['Q1_ajustat'], df_compra_inflacio['mediana/Q2_ajustat'], df_compra_inflacio['Q3_ajustat']])

quantile_33_compra = compra_ajustats.quantile(0.3333)
quantile_66_compra = compra_ajustats.quantile(0.6667)

# CÀLCUL DELS LLOGUERS AMB LES VARIACIONS DE L'IPC DESCOMPTADES

df_inflacio['acumulacio'] = (1 + df_inflacio['variacio_IPC'] / 100).cumprod()

# Es normalitza de manera que l'any base 2013 té com a valor 1
df_inflacio['acumulacio'] /= df_inflacio.loc[df_inflacio['any'] == 2013, 'acumulacio'].values[0]



# S'uneixen els df en la columna 'any'
df_compra_mapa = pd.merge(df_compra, df_inflacio[['any', 'acumulacio']], on='any', how='left')

# Es calcula el 'lloguer_ajustat'
df_compra_mapa['lloguer_ajustat'] = df_compra_mapa['lloguer'] / df_compra_mapa['acumulacio']

columnes = ['codi', 'districtes municipals', 'any', 'lloguer', 'lloguer_ajustat']
df_compra_mapa = df_compra_mapa[columnes]



# Càrrega de les dades dels districtes de l'arxiu GeoJSON
gdf_districtes = gpd.read_file('0301100100_UNITATS_ADM_POLIGONS.json')
gdf_districtes = gdf_districtes[gdf_districtes['TIPUS_UA'] == 'DISTRICTE']

gdf_compra_districtes = gdf_districtes.merge(df_compra_mapa, how='left', left_on=['FID'], right_on=['codi'])



# BARRIS

# CÀLCUL DELS LLOGUERS AMB LES VARIACIONS DE L'IPC DESCOMPTADES

df_inflacio['acumulacio'] = (1 + df_inflacio['variacio_IPC'] / 100).cumprod()

# Es normalitza de manera que l'any base 2013 té com a valor 1
df_inflacio['acumulacio'] /= df_inflacio.loc[df_inflacio['any'] == 2013, 'acumulacio'].values[0]


df_lloguer_mapa_barri = pd.merge(df_lloguer_barri, df_inflacio[['any', 'acumulacio']], on='any', how='left')

def calcular_lloguer_ajustat(row):
    try:
        return row['lloguer'] / row['acumulacio']
    except Exception:
        return 'nd'

df_lloguer_mapa_barri['lloguer_ajustat'] = df_lloguer_mapa_barri.apply(calcular_lloguer_ajustat, axis=1)


# Càrrega de les dades dels districtes de l'arxiu GeoJSON
gdf_barris = gpd.read_file('barris.geojson')
anys = pd.DataFrame({'any': range(2013, 2024)})
gdf_barris = gdf_barris.loc[gdf_barris.index.repeat(len(anys))].reset_index(drop=True)
gdf_barris['any'] = pd.concat([anys]*len(gdf_barris['BARRI'].unique()), ignore_index=True)


# Eliminar 0 a l'esquerra de la columna 'BARRI' i convertir a int
gdf_barris['BARRI'] = gdf_barris['BARRI'].str.lstrip('0').astype(int)
gdf_lloguer_barris = gdf_barris.merge(df_lloguer_mapa_barri, how='left', left_on=['BARRI'], right_on=['codi'])


# CÀLCUL DELS LLOGUERS AMB LES VARIACIONS DE L'IPC DESCOMPTADES

df_inflacio['acumulacio'] = (1 + df_inflacio['variacio_IPC'] / 100).cumprod()

# Es normalitza de manera que l'any base 2013 té com a valor 1
df_inflacio['acumulacio'] /= df_inflacio.loc[df_inflacio['any'] == 2013, 'acumulacio'].values[0]


df_compra_mapa_barri = pd.merge(df_compra_barri, df_inflacio[['any', 'acumulacio']], on='any', how='left')

def calcular_lloguer_ajustat(row):
    try:
        return row['lloguer'] / row['acumulacio']
    except Exception:
        return 'nd'

df_compra_mapa_barri['lloguer_ajustat'] = df_compra_mapa_barri.apply(calcular_lloguer_ajustat, axis=1)


gdf_compra_barris = gdf_barris.merge(df_compra_mapa_barri, how='left', left_on=['BARRI'], right_on=['codi'])





# VISUALITZACIÓ


gdf_districtes = gpd.read_file('0301100100_UNITATS_ADM_POLIGONS.json')
gdf_districtes = gdf_districtes[gdf_districtes['TIPUS_UA'] == 'DISTRICTE']
gdf_lloguer_districtes = gdf_districtes.merge(df_lloguer_mapa, how='left', left_on=['FID'], right_on=['codi'])

anys = df_padro_obra_nova_districtes['any'].unique()

def categoria_lloguer(row, quantile_33, quantile_66):
    if row['lloguer_ajustat'] == 'nd':
        return 'nd'
    elif row['lloguer_ajustat'] < quantile_33:
        return 'rang baix'
    elif quantile_33 <= row['lloguer_ajustat'] < quantile_66:
        return 'rang mitjà'
    elif row['lloguer_ajustat'] >= quantile_66:
        return 'rang alt'


gdf_lloguer_districtes['categoria'] = gdf_lloguer_districtes.apply(lambda row: categoria_lloguer(row, quantile_33, quantile_66), axis=1)
gdf_lloguer_barris['categoria'] = gdf_lloguer_barris.apply(lambda row: categoria_lloguer(row, quantile_33, quantile_66), axis=1)


gdf_compra_districtes['categoria'] = None
for index, row in gdf_compra_districtes.iterrows():
    if row['lloguer_ajustat'] == 'nd':
        gdf_compra_districtes.at[index, 'categoria'] = 'nd'
    elif row['lloguer_ajustat'] < quantile_33_compra:
        gdf_compra_districtes.at[index, 'categoria'] = 'rang baix'
    elif quantile_33_compra <= row['lloguer_ajustat'] < quantile_66_compra:
        gdf_compra_districtes.at[index, 'categoria'] = 'rang mitjà'
    elif row['lloguer_ajustat'] >= quantile_66_compra:
        gdf_compra_districtes.at[index, 'categoria'] = 'rang alt'


gdf_compra_barris['categoria'] = None
for index, row in gdf_compra_barris.iterrows():
    if row['lloguer_ajustat'] == 'nd':
        gdf_compra_barris.at[index, 'categoria'] = 'nd'
    elif row['lloguer_ajustat'] < quantile_33_compra:
        gdf_compra_barris.at[index, 'categoria'] = 'rang baix'
    elif quantile_33_compra <= row['lloguer_ajustat'] < quantile_66_compra:
        gdf_compra_barris.at[index, 'categoria'] = 'rang mitjà'
    elif row['lloguer_ajustat'] >= quantile_66_compra:
        gdf_compra_barris.at[index, 'categoria'] = 'rang alt'



def mapa_districtes (any, compra_lloguer, habitatges_turistics):
    if compra_lloguer == 'Lloguer':
        gdf_districtes_mapa = gdf_lloguer_districtes[gdf_lloguer_districtes['any'] == any]
    else:
        gdf_districtes_mapa = gdf_compra_districtes[gdf_compra_districtes['any'] == any]
    
    colors = {'rang baix': 'green', 'rang mitjà': 'yellow', 'rang alt': 'red'}
    mapa = folium.Map(location=[41.3851, 2.1734], zoom_start=11)

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
            aliases=['Districte:'],
            localize=True,
        ),
        popup=folium.GeoJsonPopup(
            fields=['NOM', 'lloguer'],
            aliases=['Barri:', 'Preu mitjà:'],
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



def mapa_barris (any, compra_lloguer, habitatges_turistics):
    if compra_lloguer == 'Lloguer':
        gdf_barris_mapa = gdf_lloguer_barris[gdf_lloguer_barris['any_y'] == any]
    else:
        gdf_barris_mapa = gdf_compra_barris[gdf_compra_barris['any_y'] == any]
    
    colors = {'rang baix': 'green', 'rang mitjà': 'yellow', 'rang alt': 'red'}
    mapa = folium.Map(location=[41.3851, 2.1734], zoom_start=11)

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
            aliases=['Barri:', 'Preu mitjà:'],
            localize=True
        ),
        highlight_function=lambda x: {'weight': 2, 'color': 'blue'}
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




app = dash.Dash(__name__)
# CANVI PER RENDER
server = app.server

app.layout = html.Div([
    html.H1("Sector de l'habitatge a Barcelona"),
    dcc.RadioItems(
        id='opcio_barris_districtes',
        options=[
            {'label': 'Mapa de Barris', 'value': 'barris'},
            {'label': 'Mapa de Districtes', 'value': 'districtes'}
        ],
        value='barris',
        labelStyle={'display': 'inline-block'}
    ),
    html.Br(),
    html.P("Selecciona entre les opcions compra i lloguer:"),
    dcc.RadioItems(
        id='opcio_compra_lloguer',
        options=[
            {'label': 'Compra', 'value': 'Compra'},
            {'label': 'Lloguer', 'value': 'Lloguer'}
        ],
        value='Lloguer',
        labelStyle={'display': 'inline-block'}
    ),
    html.Br(),
    html.P("Prémer l'àrea del districte o barri per a més informació"),
    dcc.Dropdown(
        id='opcio_any',
        options=[{'label': str(year), 'value': year} for year in range(2013, 2024)],
        value=2023
    ),
    dcc.Checklist(
        id='opcio_habitatges_turistics',
        options=[
            {'label': 'Habitatges turístics', 'value': 'habitatges'}
        ],
        value=[]
    ),
    html.Div([
        html.Iframe(id='map', width='100%', height='500')
        ]),
    html.Br(),
    html.H1("Lloguer i renda per districtes del 2015 al 2021"),
    dcc.Checklist(
        id='opcio_districte',
        options=[{'label': districte, 'value': districte} for districte in df_renda_lloguer['Districtes municipals'].unique()],
        value=['Barcelona'],
        labelStyle={'display': 'block'}
    ),
    dcc.Graph(id='grafic'),
    html.Br(),
    html.H1("Evolució de l'obra nova i el padró a Barcelona"),
    dcc.Dropdown(
        id='opcio_grafic_barres',
        options=[{'label': str(any), 'value': any} for any in anys],
        value=anys[0]
    ),
    dcc.Graph(id='grafic_barres')
    ])



@app.callback(
    Output('map', 'srcDoc'),
    [Input('opcio_barris_districtes', 'value'),
     Input('opcio_any', 'value'),
     Input('opcio_compra_lloguer', 'value'),
     Input('opcio_habitatges_turistics', 'value')]
)



def creacio_mapa (opcio_barris_districte, opcio_any, opcio_lloguer_renda, opcio_habitatges_turistics):
    hab_tur = 'habitatges' in opcio_habitatges_turistics
    if opcio_barris_districte == 'barris':
        barrio_map = mapa_barris(opcio_any, opcio_lloguer_renda, hab_tur)
        barrio_map.save('mapa_barrios_barcelona.html')
        return open('mapa_barrios_barcelona.html', 'r').read()
    else:
        distrito_map = mapa_districtes(opcio_any, opcio_lloguer_renda, hab_tur)
        distrito_map.save('mapa_distritos_barcelona.html')
        return open('mapa_distritos_barcelona.html', 'r').read()

@app.callback(
    Output('grafic', 'figure'),
    [Input('opcio_districte', 'value')]
)


def grafic_despres_seleccio(districtes_seleccionats):
    df_compra_seleccio = df_renda_lloguer[df_renda_lloguer['Districtes municipals'].isin(districtes_seleccionats)]
    
    linea_lloguer = px.line(df_compra_seleccio, x='Any', y='mitjana_preu_lloguer', color='Districtes municipals',
                  labels={'mitjana_preu_lloguer': 'Mitjana Preu Lloguer'}, title="Mitjana Preu Lloguer")
    
    linea_renda = px.line(df_compra_seleccio, x='Any', y='renda_mitjana_mensual', color='Districtes municipals',
                   labels={'renda_mitjana_mensual': 'Renda Mitjana Mensual'}, title="Renda Mitjana Mensual")
    
    for tipus_linea in linea_renda.data:
        tipus_linea.update(line=dict(dash='dash'))
        linea_lloguer.add_trace(tipus_linea)
    
    linea_lloguer.update_layout(
        xaxis_title="Any",
        yaxis_title="Cantidad",
        legend_title="Districtes municipals",
        template="plotly_white"
    )
    
    linea_lloguer.update_traces(mode='lines+markers')
    linea_lloguer.update_yaxes(title_text="Mitjana preu lloguer / Renda mitjana mensual")

    return linea_lloguer




@app.callback(
    Output('grafic_barres', 'figure'),
    [Input('opcio_grafic_barres', 'value')]
)
def grafic_barres (any_seleccionat):
    df_any = df_padro_obra_nova_districtes[df_padro_obra_nova_districtes['any'] == any_seleccionat]
    fig = go.Figure(data=[
        go.Bar(name='Obra Nova', x=df_any['districtes municipals'], y=df_any['obra_nova']),
        go.Bar(name='Evolució del Padró', x=df_any['districtes municipals'], y=df_any['evolucio_padro'], marker_pattern_shape="/")
    ])
    fig.update_layout(
        title=f"Evolució de l'obra nova i el padró a Barcelona - {any_seleccionat}",
        xaxis_title="Districtes",
        yaxis_title="Valor",
        barmode='group',
        xaxis_tickangle=-45,
        yaxis=dict(range=[-25000, 25000])
    )
    return fig



if __name__ == '__main__':
    app.run_server(debug=True)
