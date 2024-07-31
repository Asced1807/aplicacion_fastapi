from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import geopandas as gpd
import psycopg2
from shapely import wkb
import cachetools

def create_dash_app(requests_pathname_prefix="/dash/"):
    dash_app = Dash(__name__, requests_pathname_prefix=requests_pathname_prefix)

    # Crear un caché en memoria
    cache = cachetools.LRUCache(maxsize=2)

    dash_app.layout = html.Div([
        html.H4('Mapa de la República Dominicana por Minerales'),
        html.P("Selecciona un mineral:"),
        dcc.Dropdown(
            id='mineral', 
            options=[],
            value=None
        ),
        dcc.Graph(id="graph"),
        dcc.Graph(id="bar-chart"),  # Añadir un nuevo gráfico de barras
        dcc.Interval(
            id='interval-component',
            interval=30*60*1000,  # Intervalo en milisegundos (aquí se refresca cada 30 minutos)
            n_intervals=0
        ),
        html.Div([
            html.P(
                "Creado por Elvin Coronado Reyes",
                style={'textAlign': 'center', 'marginTop': '20px', 'marginBottom': '5px'}
            ),
        ], style={'padding': '10px', 'textAlign': 'center'})
    ])

    def load_data():
        conn = psycopg2.connect(
            dbname="formulario",
            user="postgres",
            password="gohan2015",
            host="localhost",
            port="5432"
        )
        
        cur = conn.cursor()
        
        update_query = """
            WITH suma_cantidades AS (
                SELECT 
                    provincia,
                    tipo_recurso AS mineral,
                    SUM(cantidad_calculada) AS total_cantidad_calculada
                FROM 
                    datos_formulario
                GROUP BY 
                    provincia, tipo_recurso
            )
            UPDATE datos_mapa
            SET cantidad_calculada = sc.total_cantidad_calculada
            FROM suma_cantidades sc
            WHERE datos_mapa.provincia = sc.provincia
              AND datos_mapa.mineral = sc.mineral;
        """
        cur.execute(update_query)
        conn.commit()
        
        select_query = """
            SELECT df.nombre_completo, df.cantidad_calculada AS cantidad, dm.*
            FROM datos_formulario df
            JOIN datos_mapa dm ON df.provincia = dm.provincia AND df.tipo_recurso = dm.mineral
            ORDER BY dm.provincia ASC, dm.mineral ASC;
        """
        cur.execute(select_query)
        
        data = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        df = pd.DataFrame(data, columns=columns)
        
        cur.close()
        conn.close()
        
        df['geometry'] = df['geometry'].apply(lambda x: wkb.loads(x, hex=True))
        gdf = gpd.GeoDataFrame(df, geometry='geometry')
        
        # Guardar los datos en la caché
        cache['data'] = gdf
        
        return gdf

    @dash_app.callback(
        [Output('mineral', 'options'), Output('mineral', 'value')],
        Input('interval-component', 'n_intervals')
    )
    def update_dropdown(n):
        gdf = load_data()
        
        minerales = gdf['mineral'].unique()
        options = [{'label': mineral, 'value': mineral} for mineral in minerales]
        value = minerales[0] if minerales.size > 0 else None
        
        return options, value

    @dash_app.callback(
        [Output("graph", "figure"), Output("bar-chart", "figure")],
        [Input("mineral", "value"), Input('interval-component', 'n_intervals')]
    )
    def update_graphs(mineral, n):
        # Verificar si los datos están en caché
        if 'data' in cache:
            gdf = cache['data']
        else:
            gdf = load_data()
        
        gdf_filtered = gdf[gdf['mineral'] == mineral]
        
        # Gráfico de mapa
        fig_map = px.choropleth_mapbox(
            gdf_filtered,
            geojson=gdf_filtered.geometry.__geo_interface__,
            locations=gdf_filtered.index,
            color='cantidad_calculada',
            color_continuous_scale="Viridis",
            range_color=(gdf_filtered['cantidad_calculada'].min(), gdf_filtered['cantidad_calculada'].max()),
            mapbox_style="carto-positron",
            zoom=7,
            center={"lat": 18.7357, "lon": -70.1627},
            opacity=0.5,
            labels={'cantidad_calculada': 'Cantidad Calculada'}
        )
        
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        fig_map.update_traces(
            hovertemplate=gdf_filtered['provincia'] + '<br>Cantidad: %{z}<extra></extra>'
        )
        
        # Gráfico de barras horizontales
        top_5 = gdf_filtered.nlargest(5, 'cantidad')[['nombre_completo', 'cantidad']]
        
        fig_bar = px.bar(
            top_5,
            x='cantidad',
            y='nombre_completo',
            orientation='h',
            title=f'Top 5 personas con mayor cantidad de {mineral}',
            labels={'cantidad': 'Cantidad', 'nombre_completo': 'Nombre'}
        )
        
        fig_bar.update_layout(
            margin={"r": 0, "t": 60, "l": 0, "b": 0},  # Aumentar el margen superior
            title={
                'y': 0.95,  # Ajustar la posición del título
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {
                    'color': '#007bff',  # Color del título
                    'size': 24  # Tamaño de la fuente
                }
            }
        )
        
        return fig_map, fig_bar

    return dash_app

# Esta parte se queda fuera de la función create_dash_app
if __name__ == '__main__':
    app = create_dash_app()
    app.run_server(debug=True)
    