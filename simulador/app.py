from flask import Flask, render_template, make_response, request
import requests
import pandas as pd
from flask_bootstrap import Bootstrap
import matplotlib.pyplot as plt
import os
import io
import plotly.express as px
app = Flask(__name__)
bootstrap = Bootstrap(app)


def consulta_api():
    api_url = "https://www.datos.gov.co/resource/u958-pr9h.json"
    try:
        response = requests.get(api_url)
        data = response.json()
        df = pd.DataFrame(data)
        df['produccion_t'] = pd.to_numeric(df['produccion_t'], errors='coerce')
        return df
    except Exception as e:
        print(e)
        return None


def procesar_datos(df):
    produccion_por_cultivo = df.groupby(
        'cultivo')['produccion_t'].sum().reset_index()
    produccion_por_cultivo = produccion_por_cultivo.sort_values(
        by='produccion_t', ascending=False)
    produccion_por_cultivo = produccion_por_cultivo.head()

    produccion_por_municipio = df.groupby(
        'municipio')['produccion_t'].sum().reset_index()
    produccion_por_municipio = produccion_por_municipio.sort_values(
        by='produccion_t', ascending=False)
    produccion_por_municipio = produccion_por_municipio.head()

    fig = px.pie(data_frame=produccion_por_municipio, names='municipio',
                 values='produccion_t', title='Produccion por municipio')
    fig2 = px.bar(data_frame=produccion_por_cultivo, x='cultivo',
                  y='produccion_t', title='Produccion por productos')
    fig3 = px.line(data_frame=produccion_por_cultivo, x='cultivo',
                   y='produccion_t', title='Produccion por productos')
    plot_html = fig.to_html(full_html=False)
    plot_html2 = fig2.to_html(full_html=False)
    plot_html3 = fig3.to_html(full_html=False)
    return produccion_por_cultivo, plot_html, plot_html2, plot_html3


def ajustar_produccion(produccion_por_cultivo, temperatura):
    if temperatura > 60:
        # Definir ajustes para cada cultivo
        ajustes = {
            'PAPA': -500000,
            'CAÑA PANELERA': -100,
            'PLATANO': -300,
            'ZANAHORIA': -800,
            'TOMATE INVERNADERO': -500000
        }
        # Aplicar el ajuste correspondiente a cada cultivo
        produccion_por_cultivo['produccion_t'] = produccion_por_cultivo.apply(
            lambda row: row['produccion_t'] + ajustes.get(row['cultivo'], 0), axis=1)
       
    elif temperatura <= 0:
         # Definir ajustes para cada cultivo
        ajustes = {
            'PAPA': -200000,
            'CAÑA PANELERA': -600000,
            'PLATANO': -500000,
            'ZANAHORIA': -200000,
            'TOMATE INVERNADERO': -600000
        }
        produccion_por_cultivo['produccion_t'] = produccion_por_cultivo.apply(lambda row: row['produccion_t'] + ajustes.get(row['cultivo'], 0), axis=1)
    
    elif temperatura > 1 and temperatura < 10:
         # Definir ajustes para cada cultivo
        ajustes = {
            'PAPA': -20000,
            'CAÑA PANELERA': -300000,
            'PLATANO': -300000,
            'ZANAHORIA': -30000,
            'TOMATE INVERNADERO': -400000
        }
        produccion_por_cultivo['produccion_t'] = produccion_por_cultivo.apply(lambda row: row['produccion_t'] + ajustes.get(row['cultivo'], 0), axis=1)
    
    elif temperatura > 30 and temperatura < 60:
         # Definir ajustes para cada cultivo
        ajustes = {
            'PAPA': -600000,
            'CAÑA PANELERA': -3000,
            'PLATANO': -3000,
            'ZANAHORIA': -600000,
            'TOMATE INVERNADERO': -500000
        }
        produccion_por_cultivo['produccion_t'] = produccion_por_cultivo.apply(lambda row: row['produccion_t'] + ajustes.get(row['cultivo'], 0), axis=1)
        
    return produccion_por_cultivo


@app.route('/')
def index():

    try:
        df = consulta_api()
        if df is not None:
            produccion_por_cultivo, plot_html, plot_html2, plot_html3 = procesar_datos(
                df)
            return render_template('index.html', data=produccion_por_cultivo, plot_html=plot_html, plot_html2=plot_html2,  plot_html3=plot_html3)

    except Exception as e:
        print(e)
        error_message = f"Error al obtener datos de la API: {str(e)}"
        return render_template('error.html', error_message=error_message)


@app.route('/procesar', methods=['POST'])
def procesar():
    try:
        if request.method == 'POST':
            temperatura = int(request.form['temperatura'])
            print(temperatura)
            df = consulta_api()
            if df is not None:
                produccion_por_cultivo, plot_html, plot_html2, plot_html3 = procesar_datos(
                    df)
                produccion_por_cultivo_ajustado = ajustar_produccion(
                    produccion_por_cultivo, temperatura)
                print(produccion_por_cultivo_ajustado)
                fig2 = px.bar(data_frame=produccion_por_cultivo_ajustado,x='cultivo', y='produccion_t', title='Produccion por productos')
                plot_html2 = fig2.to_html(full_html=False)
                fig3 = px.line(data_frame=produccion_por_cultivo, x='cultivo',y='produccion_t', title='Produccion por productos')
                plot_html3 = fig3.to_html(full_html=False)
            return render_template('index.html', data=produccion_por_cultivo_ajustado,  plot_html=plot_html, plot_html2=plot_html2, plot_html3=plot_html3)

    except Exception as e:
        print(e)
        error_message = f"Error al obtener datos de la API: {str(e)}"
        return render_template('error.html', error_message=error_message)


if __name__ == '__main__':
    app.run(debug=True)
