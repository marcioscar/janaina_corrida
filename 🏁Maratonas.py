from datetime import datetime
import polyline
import streamlit as st
import pandas as pd
from streamlit_extras.dataframe_explorer import dataframe_explorer
from streamlit_globe import streamlit_globe
from streamlit_js_eval import streamlit_js_eval
import folium
from streamlit_folium import st_folium
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import altair as alt
from dotenv import load_dotenv
import json
import os

from db import  get_maratonas_janaina  , maratonas_cadastrar_janaina, maratonas_editar_janaina, get_corridas_strava_janaina

# Carregar variáveis de ambiente
load_dotenv()




def tempo_para_minutos(tempo_str):
    try:
        # Remove espaços e divide em horas, minutos e segundos
        partes = tempo_str.strip().split(':')
        if len(partes) == 3:  # Formato HH:MM:SS
            horas = int(partes[0])
            minutos = int(partes[1])
            segundos = int(partes[2])
            # Converte tudo para minutos (incluindo os segundos)
            total_minutos = (horas * 60) + minutos + (segundos / 60)
            return total_minutos
        return 0
    except:
        return 0


maratonas = get_maratonas_janaina()

# Função segura para decodificar polyline
def decode_polyline_safe(polyline_str):
    try:
        if pd.isna(polyline_str) or polyline_str == '':
            return []
        return polyline.decode(polyline_str)
    except Exception as e:
        print(f"Erro ao decodificar polyline: {str(e)}")
        return []

# Aplicar a decodificação segura
maratonas_mapa = maratonas.copy()
maratonas_mapa['mapa'] = maratonas_mapa['mapa'].apply(decode_polyline_safe)


# Lista de cores para os pontos
cores = ['red', 'blue', 'green', 'yellow', 'purple', 'orange', 'pink', 'cyan', 'magenta', 'lime', 'teal', 'fuchsia', 'aqua', 'coral', 'crimson', 'gold', 'goldenrod']


# Converter os dados para o formato do streamlit_globe
pointsData = []
labelsData = []


for idx, row in maratonas.iterrows():
    if pd.notna(row['local']) and row['local'] != '':
        try:
            # Converter string de local para lat/lng
            lat, lng = map(float, row['local'].split(','))
            # Usar cores diferentes para cada local
            cor = cores[idx % len(cores)]
            # Converter tempo para minutos e usar como tamanho
            minutos = tempo_para_minutos(row['tempo'])
            tamanho = minutos / 720
            
            # Dados para o globo
            pointsData.append({
                'lat': lat,
                'lng': lng,
                'size': tamanho,
                'color': cor
            })
            labelsData.append({
                'lat': lat,
                'lng': lng,
                'size': tamanho + 0.1,
                'color': cor,
                'text': f"{row['nome']} - {row['tempo']}"
            })
            
            # Dados para o mapa
            
        except (ValueError, AttributeError):
            continue


tela = streamlit_js_eval(js_expressions="screen.width", key="SCR")

st.subheader("Maratonas Pelo Mundo") 
if pointsData:  # Só mostra o globo se houver pontos
    if tela > 1200:
        
            streamlit_globe(width=950, height=600, pointsData=pointsData, labelsData=labelsData)
    else:
        with st.container(border=True):
            streamlit_globe(width=370, height=350, pointsData=pointsData, labelsData=labelsData)

# Converter para DataFrame para o mapa


@st.dialog("Nova Maratona")
def maratona():
    
    link = ''
    
    with st.form("Maratona"):
        nome = st.text_input("Nome")
        col1, col2 = st.columns(2)
        with col1:
            id = st.text_input("ID")
            data = datetime.combine(st.date_input('Data', min_value='2000-01-01', format="DD/MM/YYYY"), datetime.min.time())
            local = st.text_input("Local (longitude, latitude)")
        with col2:
            tempo = st.text_input("Tempo")
            
         #enviar recibo de pagamento
                   

        submitted = st.form_submit_button("Cadastrar")
        if submitted:    
            maratonas_cadastrar_janaina(nome, data,local, tempo, id)
            st.success("Maratona cadastrada com sucesso! sem arquivo")
            st.rerun()        


def formatar_tempo_minutos(minutos):
    horas = int(minutos // 60)
    mins = int(minutos % 60)
    return f"{horas}:{mins:02d}"

maratonas_mapa['detalhes'] = False
visivel = maratonas_mapa.drop(columns=['mapa'])
grafico = visivel.copy()
grafico['tempo'] = grafico['tempo'].apply(tempo_para_minutos)
grafico['tempo_formatado'] = grafico['tempo'].apply(formatar_tempo_minutos)

# Remover a palavra 'maratona' dos nomes
grafico['nome'] = grafico['nome'].str.replace('maratona de', '', case=False).str.strip()
grafico['nome'] = grafico['nome'].str.replace('maratona do', '', case=False).str.strip()
grafico['nome'] = grafico['nome'].str.replace('maratona da', '', case=False).str.strip()
grafico['nome'] = grafico['nome'].str.replace('maratona', '', case=False).str.strip()

# Criar gráfico com Altair
bars = alt.Chart(grafico).mark_bar().encode(
    y=alt.Y('nome:N', sort='x'),
    x='tempo:Q',
    color='tempo:Q',
    tooltip=['nome', 'tempo_formatado']
).properties(
    width='container'
)

# Adicionar texto sobre as barras
text = alt.Chart(grafico).mark_text(
    align='left',
    baseline='middle',
    dx=5
).encode(
    y=alt.Y('nome:N', sort='x'),
    x='tempo:Q',
    text='tempo_formatado'
)

# Combinar as camadas
chart = (bars + text)

st.altair_chart(chart, use_container_width=True)

maratonas_df = dataframe_explorer(visivel, case=False )
edited_df = st.data_editor(
    maratonas_df, 
    column_order=[ 'detalhes',"nome", "data", "tempo"], 
    column_config={
        "data": st.column_config.DateColumn(
            "Data", format="DD/MM/YYYY",
        ),
       
       
        "tempo": st.column_config.TimeColumn(
            "Tempo", 
        ),
        "detalhes": st.column_config.CheckboxColumn(
            "Detalhes",
            default=False,
        ),
      
    },
    hide_index=True, 
    height=300, 
    num_rows="fixed"
)

@st.dialog("Editar Maratona", width="large")
def editar_maratona(linha_selecionada):
    file_url = ''
    file_url_gpx = ''
    if not linha_selecionada.empty:
        nome = st.text_input("Nome", value=linha_selecionada['nome'].iloc[0])
        data = datetime.combine(st.date_input('Data', value=linha_selecionada['data'].iloc[0], format="DD/MM/YYYY"), datetime.min.time())
        local = st.text_input("Local", value=linha_selecionada['local'].iloc[0])
        tempo = st.text_input("Tempo", value=linha_selecionada['tempo'].iloc[0])
        
        id_strava = st.text_input("Id Strava", value=linha_selecionada['id_strava'].iloc[0])
        
                 
        if st.button("Salvar", type='secondary', icon="💾"):
            maratonas_editar_janaina(linha_selecionada['_id'].iloc[0], nome, data, local, tempo, id_strava)
            st.success("Maratona editada com sucesso!")
            st.rerun()
    else:
        st.warning("Por favor, selecione uma maratona para editar.")


@st.dialog("Detalhes da Maratona", width="large")
def detalhes_maratona(linha_selecionada):    
    if not linha_selecionada.empty:
        # Pegar o índice da linha selecionada no DataFrame original
        idx_selecionado = linha_selecionada.index[0]
        id_strava = maratonas_mapa.iloc[idx_selecionado]['id_strava']
        st.header(f"{maratonas_mapa.iloc[idx_selecionado]['nome']}")
        if pd.notna(id_strava) and id_strava != '':
            corrida_strava = get_corridas_strava_janaina(id_strava)
            # transformar valores de corrida_strava em dataframe
            corrida_strava = pd.DataFrame(corrida_strava)
            corrida_strava['moving_time_minutes'] = round(corrida_strava['moving_time']/60, 2)
            corrida_strava['moving_time_minutes'].head()
            corrida_strava['distance_km'] = round(corrida_strava['distance'] / 1000, 2)
            corrida_strava['pace'] = corrida_strava['moving_time_minutes'] / corrida_strava['distance_km']
            corrida_strava['Tempo'] = corrida_strava['moving_time_minutes'].apply(
                lambda x: f"{int(x // 60)}h {int(x % 60)}m"
            )
            corrida_strava['avg_speed_kmh'] = round(60/corrida_strava['pace'], 2)
            def kmh_to_min_km(speed_kmh):
                if speed_kmh > 0:  # Evitar divisão por zero
                    pace = 60 / speed_kmh
                    minutes = int(pace)
                    seconds = int((pace - minutes) * 60)
                    return f"{minutes}:{seconds:02d} min/km"
                else:  
                    return None  # Retorna None para velocidades inválidas

            corrida_strava['avg_speed_kmh'] = pd.to_numeric(corrida_strava['avg_speed_kmh'], errors='coerce')
            corrida_strava['pace_real'] = corrida_strava['avg_speed_kmh'].apply(kmh_to_min_km)

            #mapa percurso
            rota = decode_polyline_safe(corrida_strava['map.summary_polyline'].iloc[0])
            # rota = maratonas_mapa.iloc[idx_selecionado]['mapa']
            m = folium.Map(location=rota[0], zoom_start=12)
            
                
            col1, col2 = st.columns(2)
            with col1:
                st.metric( border=True,label = 'Distância', value= f"{corrida_strava['distance_km'].iloc[0]:.2f} km")
            with col2:
                st.metric( border=True,label = 'Tempo', value= f"{corrida_strava['Tempo'].iloc[0]}")

            col1, col2 = st.columns(2)
            with col1:
                st.metric( border=True,label = 'Pace', value= f"{corrida_strava['pace_real'].iloc[0]}")
            with col2:
                 st.metric( border=True,label = 'Ganho de Altimetria', value= f"{corrida_strava['total_elevation_gain'].iloc[0]} m")

                
            # Adiciona a polyline (rota) ao mapa
            folium.PolyLine(rota, color='blue', weight=5, opacity=0.7).add_to(m)

            # Adiciona marcador verde na primeira posição
            folium.Marker(location=rota[0], tooltip="Inicio", icon=folium.Icon(color='green', icon='play')).add_to(m)

            # Adiciona marcador vermelho na última posição
            folium.Marker(location=rota[-1], tooltip="Final",icon=folium.Icon(color='red', icon='flag')).add_to(m)

            # Exibe o mapa no Streamlit
            st_folium(m, center=True, width="100%", height=400)                    
            
            
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric( border=True,label = 'Data', value= f"{maratonas_mapa.iloc[idx_selecionado]['data'].strftime('%d/%m/%Y')}")
            with col2:
                st.metric( border=True,label = 'Tempo', value= f"{maratonas_mapa.iloc[idx_selecionado]['tempo']}")

        # Mostrar todos os detalhes da linha selecionada
        # for coluna in linha_selecionada.columns:
        #     if coluna != "detalhes":
        #         st.write(f"**{coluna}**: {linha_selecionada[coluna].iloc[0]}")
        
        # # Mostrar o mapa da linha correspondente do DataFrame original
        # st.write("**Mapa**:", maratonas_mapa.iloc[idx_selecionado]['mapa'])
    else:
        st.warning("Por favor, selecione uma maratona para ver os detalhes.")

col1, col2 = st.columns(2)
with col1:
    if st.button("Detalhes", type='secondary', icon="🕵🏼‍♂️"):
        linha_selecionada = edited_df[edited_df["detalhes"] == True]
        detalhes_maratona(linha_selecionada)

with col2:
    if st.button("Editar", type='secondary', icon="🖊️"):
        linha_selecionada = edited_df[edited_df["detalhes"] == True]
        editar_maratona(linha_selecionada)

with st.sidebar:
      if st.button("Nova Maratona", type='secondary',icon="🏆"):
        maratona()