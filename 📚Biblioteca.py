from datetime import datetime
import streamlit as st
import pandas as pd
from streamlit_extras.dataframe_explorer import dataframe_explorer
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

from db import get_livros, livros_cadastrar, livros_editar

livros = get_livros()
livros_df = pd.DataFrame(livros)
livros_df["Editar"] = False
total_livros = len(livros_df)

FOLDER_ID = '1d-vkue1X6aVP97J6ETUnLkqzDeSge-jS' # biblioteca

# 🔑 Configuração das credenciais
SERVICE_ACCOUNT_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive']

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

service = build('drive', 'v3', credentials=credentials)


# 🚀 Função para upload no Drive
def upload_arquivo_drive(file, file_name):
    nome_arquivo = datetime.now().strftime("%d-%m-%Y") + '_' + file_name
    file_metadata = {'name': nome_arquivo,
                     'parents': [FOLDER_ID]
                     }

    media = MediaIoBaseUpload(
        io.BytesIO(file.read()), mimetype=file.type, resumable=True
    )

    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    file_id = uploaded_file.get('id')

    # 🔓 Permissão pública
    service.permissions().create(
        fileId=file_id,
        body={'type': 'anyone', 'role': 'reader'}
    ).execute()

    # 🔗 Link público
    link = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"

    return link




st.subheader("Biblioteca")

    

@st.dialog("Novo Livro")
def livro():
    citacao_url = ''
    nota_url = ''
    with st.form("Livro"):
        nome = st.text_input("Nome")
        data = datetime.combine(st.date_input('Data', min_value='2000-01-01', format="DD/MM/YYYY"), datetime.min.time())
        capa = st.text_input("Capa")
        autor = st.text_input("Autor")
        
        nota = st.file_uploader("Notas sobre o Livro")
        if nota:
            nota_url = upload_arquivo_drive(nota, 'nota_' + nota.name)
            st.success("Arquivo enviado com sucesso!")
            
        citacao = st.file_uploader("Citação do Livro")
        if citacao:
            citacao_url = upload_arquivo_drive(citacao, 'citacao_' + citacao.name)
            st.success("Arquivo enviado com sucesso!")                
                
        if st.form_submit_button("Salvar"):
            livros_cadastrar(nome, data, capa, citacao_url, nota_url, autor)
            st.rerun()

col1, col2 = st.columns(2)
with col1:
    st.badge(f"Total de livros: {total_livros}", color="green", icon="📚")
with col2:
    if st.button("📖 Novo Livro"):
        livro()


@st.dialog("Editar Livro")
def editar(id, nome, data, capa, citacao, nota, autor):
    citacao_url = ''
    nota_url = ''
    with st.form("Editar Livro"):
        nome = st.text_input("Nome", value=nome)
        data = datetime.combine(st.date_input('Data', value=data, format="DD/MM/YYYY"), datetime.min.time())
        capa = st.text_input("Capa", value=capa)
        autor = st.text_input("Autor", value=autor)
        nota = st.file_uploader("Notas sobre o Livro")
        if nota:
            nota_url = upload_arquivo_drive(nota, 'nota_' + nota.name)
            st.success("Arquivo enviado com sucesso!")
                
        citacao = st.file_uploader("Citação do Livro")
        if citacao:
            citacao_url = upload_arquivo_drive(citacao, 'citacao_' + citacao.name)
            st.success("Arquivo enviado com sucesso!")
            
        if st.form_submit_button("Salvar"):
            livros_editar(id, nome, data, capa, citacao_url, nota_url, autor)
            st.rerun()


livros = dataframe_explorer(livros_df, case=False)   
edited_df = st.data_editor(
    livros,
    column_order=['Editar', 'nome','autor', 'data', 'capa', 'citacao', 'nota'],
    column_config={
        "Editar": st.column_config.CheckboxColumn(
            "Editar",
            help="Selecione para editar",
            default=False,
        ),
        "nome": st.column_config.TextColumn(
            "Nome",
            help="Nome do livro",
            disabled=True,
        ),
        "capa": st.column_config.ImageColumn(
            "Capa", help="Capa do livro",
            
        ),
        "data": st.column_config.DateColumn(
            "Data", format="DD/MM/YYYY",
            disabled=True,
        ),
        "citacao": st.column_config.LinkColumn(
            "Citação", display_text="💬",
            disabled=True,
        ),
        "nota": st.column_config.LinkColumn(
            "Nota", display_text="📝",
            disabled=True,
        ),
        "autor": st.column_config.TextColumn(
            "Autor",
            help="Autor do livro",
            disabled=True,
        ),
    },
    hide_index=True,
    num_rows="fixed"
)

if st.button("Editar", type='secondary', icon="✍🏻"):
    linha_selecionada = edited_df[edited_df["Editar"] == True]
    if not linha_selecionada.empty:
        # Convertendo os valores da Series para valores únicos
        id = linha_selecionada["_id"].iloc[0]
        nome = linha_selecionada["nome"].iloc[0]
        data = linha_selecionada["data"].iloc[0]
        capa = linha_selecionada["capa"].iloc[0]
        citacao = linha_selecionada["citacao"].iloc[0]
        nota = linha_selecionada["nota"].iloc[0]
        autor = linha_selecionada["autor"].iloc[0]
        editar(id, nome, data, capa, citacao, nota, autor)
    else:
        st.warning("Selecione uma linha para editar")