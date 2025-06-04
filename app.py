from datetime import datetime, timedelta
import locale
import streamlit as st
import pandas as pd
from streamlit_extras.dataframe_explorer import dataframe_explorer
from db import get_contas

def formatar_moeda(valor):
    try:
        return locale.currency(valor, grouping=True)
    except:
        # Fallback para formatação manual
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Configurar o locale para português do Brasil
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except:
        locale.setlocale(locale.LC_ALL, 'C')

st.set_page_config(page_title="Janaina Runner", page_icon="icon.png", layout="wide")
st.logo('logo4.png', size = 'large', icon_image='logop.png',)


def Dashboard():
    

    contas = get_contas()
    contas_df = pd.DataFrame(contas)

    with st.sidebar:
        
        data_inicio = datetime.now().replace(day=1)  # Primeiro dia do mês atual
        data_fim = (data_inicio.replace(month=data_inicio.month % 12 + 1, day=1) - timedelta(days=1))  # Último dia do mês atual
        
    col1, col2, col3 = st.columns(3, border=True, gap='small')
    with col1:
        st.badge(f'Total das Despesas', icon=":material/payments:", color='blue')
        filtro_data = st.date_input("Período", value=(data_inicio, data_fim), format="DD/MM/YYYY")
        if contas_df.empty:
            st.warning("Nenhuma despesa encontrada")
        else:       
            # Filtrar por período
            if len(filtro_data) == 2:
                data_inicio, data_fim = filtro_data
                # Converter as datas do filtro para datetime64[ns]
                data_inicio = pd.to_datetime(data_inicio)
                data_fim = pd.to_datetime(data_fim)
                # Converter a coluna de data do DataFrame
                contas_df['data'] = pd.to_datetime(contas_df['data'])
                # Filtrar o DataFrame
                contas_df = contas_df[(contas_df['data'] >= data_inicio) & (contas_df['data'] <= data_fim)]
        
        with st.expander(f'Despesas: {formatar_moeda(contas_df["valor"].sum())}' ):
            if contas_df.empty:
                st.warning("Nenhuma despesa encontrada")
            else:
                despesas_agrupadas = contas_df.groupby('categoria')['valor'].sum()
                despesas_agrupadas = despesas_agrupadas.reset_index()
                
                despesas_agrupadas = despesas_agrupadas.rename(columns={'categoria': 'Categoria', 'valor': 'Valor'})
                if despesas_agrupadas['Valor'].sum() > 0:
                    despesas_agrupadas['Valor'] = despesas_agrupadas['Valor'].apply(formatar_moeda)
                else:
                    despesas_agrupadas['Valor'] = 0
                st.dataframe(despesas_agrupadas, use_container_width=True, hide_index=True)
            # Criar gráfico de pizza
                valores_formatados = [formatar_moeda(val) for val in contas_df.groupby('categoria')['valor'].sum()]
                fig = {
                    'data': [{
                        'labels': despesas_agrupadas['Categoria'],
                        'values': contas_df.groupby('categoria')['valor'].sum(),
                        'type': 'pie',
                        'hole': 0.4,
                        'textinfo': 'percent',
                        'hovertemplate': '%{label}<br>%{customdata}<extra></extra>',
                        'customdata': valores_formatados
                    }],
                    'layout': {
                        'showlegend': True,
                        'legend': {'orientation': 'h', 'yanchor': 'bottom', 'y': -0.2},
                        'margin': {'t': 0, 'l': 0, 'r': 0, 'b': 0},
                        'height': 500,
                        
                        
                    }
                }
        if not contas_df.empty:
            st.plotly_chart(fig, use_container_width=True, key='chart_despesas')    
        
    with col2:
        st.badge(f'Cartão Itaú ', icon=":material/credit_card:", color='orange')
        
        contas_df_itau = contas_df[contas_df['conta'] == 'Cartão Itau']
        faturas_unicas = ["Todas"] + sorted([f.strftime("%d-%B") for f in contas_df_itau['fatura'].dropna().unique()])
        filtro_fatura_itau = st.selectbox("Fatura", faturas_unicas, key='fatura_itau')

        if filtro_fatura_itau != "Todas":
            contas_df_itau = contas_df_itau[contas_df_itau['fatura'].dt.strftime("%d-%B") == filtro_fatura_itau]
            
        with st.expander(f'Despesas: {formatar_moeda(contas_df_itau["valor"].sum())}' ):
            if contas_df_itau.empty:
                st.warning("Nenhuma despesa encontrada")
            else:
                despesas_agrupadas_itau = contas_df_itau.copy()
                despesas_agrupadas_itau["valor"] = despesas_agrupadas_itau["valor"].apply(formatar_moeda)
                
                st.data_editor(despesas_agrupadas_itau,
                            column_order=["data",'nome',"categoria", "valor",'obs'], 
                            column_config={
                                "data": st.column_config.DateColumn(
                                    "Data", format="DD/MM/YYYY",
                                ),
                            },
                            hide_index=True
                            )
                
        valores_formatados = [formatar_moeda(val) for val in contas_df_itau.groupby('categoria')['valor'].sum()]
        df_agrupado_itau = contas_df_itau.groupby('categoria')['valor'].sum().reset_index()
        fig = {
            'data': [{
                'labels': df_agrupado_itau['categoria'],
                'values': df_agrupado_itau['valor'],
                'type': 'pie',
                'hole': 0.4,
                'textinfo': 'percent',
                'hovertemplate': '%{label}<br>%{customdata}<extra></extra>',
                'customdata': valores_formatados,
                 'marker': {
                    'colors': ['#fda61a', '#fdbc3d', '#F06800', '#F08C65', '#ffffa8', '#F0C513', '#cd852a', '#a4621c', '#7a3e0e', '#511b00']
                }
            }],
            'layout': {
                'showlegend': True,
                'legend': {'orientation': 'h', 'yanchor': 'bottom', 'y': -0.2},
                'margin': {'t': 0, 'l': 0, 'r': 0, 'b': 0},
                'height': 500,
               
            }
        }
        st.plotly_chart(fig, use_container_width=True)            
                
    with col3:
        st.badge(f'Cartão Nubank ', icon=":material/credit_card:", color='violet')
        
        contas_df_nubank = contas_df[contas_df['conta'] == 'Nubank']
        faturas_unicas = ["Todas"] + sorted([f.strftime("%d-%B") for f in contas_df_nubank['fatura'].dropna().unique()])
        filtro_fatura_nubank = st.selectbox("Fatura", faturas_unicas, key='fatura_nubank')

        if filtro_fatura_nubank != "Todas":
            contas_df_nubank = contas_df_nubank[contas_df_nubank['fatura'].dt.strftime("%d-%B") == filtro_fatura_nubank]
            
        with st.expander(f'Despesas: {formatar_moeda(contas_df_nubank["valor"].sum())}' ):
            if contas_df_nubank.empty:
                st.warning("Nenhuma despesa encontrada")
            else:
                
                # contas_df_nubank["valor"] = contas_df_nubank["valor"].apply(formatar_moeda)
                
                st.data_editor(contas_df_nubank,
                            column_order=["data",'nome',"categoria", "valor"], 
                            column_config={
                                "data": st.column_config.DateColumn(
                                    "Data", format="DD/MM/YYYY",
                                ),
                            },
                            hide_index=True
                            )
                
        valores_formatados = [formatar_moeda(val) for val in contas_df_nubank.groupby('categoria')['valor'].sum()]
        # Criar DataFrame agrupado para garantir a ordem correta
        df_agrupado = contas_df_nubank.groupby('categoria')['valor'].sum().reset_index()
        fig = {
            'data': [{
                'labels': df_agrupado['categoria'],
                'values': df_agrupado['valor'],
                'type': 'pie',
                'hole': 0.4,
                'textinfo': 'percent',
                'hovertemplate': '%{label}<br>%{customdata}<extra></extra>',
                'customdata': valores_formatados,
                'marker': {
                    'colors': ['#7c137b', '#b158f2', '#570959', '#963ce6', '#330037', '#7a1879', '#9b3d9a', '#bc61bc', '#de86dd', '#ffaaff']
                },
            }],
            'layout': {
                'showlegend': True,
                'legend': {'orientation': 'h', 'yanchor': 'bottom', 'y': -0.2},
                'margin': {'t': 0, 'l': 0, 'r': 0, 'b': 0},
                'height': 500
            }
        }
        st.plotly_chart(fig, use_container_width=True, key='chart_nubank')     
        # st.subheader("Total: "+locale.currency(contas_df['valor'].sum(), grouping=True))

pg = st.navigation([ '🏁Maratonas.py',  '🏃🏻‍♂️Corridas.py' ])

pg.run()