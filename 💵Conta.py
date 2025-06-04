from datetime import datetime, timedelta
import locale
import streamlit as st
import pandas as pd
from streamlit_extras.dataframe_explorer import dataframe_explorer
from db import despesas_cadastrar, despesas_editar, df_desp_apagar, get_contas, get_receitas, receitas_cadastrar
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
lista_categorias = ["Padaria", "Supermercado", 'Educação','Saúde','Entretenimento', 'Corrida', "Farmacia", "Refeicao", "Transporte",'Viagem', 'Vinho', "Outros",'Energia','Agua','Apps']

FOLDER_ID = '1sXmhIXEPZUEMlo1xe3MrwpBrmnsexZtW' # recibos

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


def formatar_moeda(valor):
    try:
        return locale.currency(valor, grouping=True)
    except:
        # Fallback para formatação manual
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

contas = get_contas()
receitas = get_receitas()

col1, col2, col3 = st.columns(3)

with col1:  
    st.subheader("Conta Márcio")   

server_url = "http://marcioscar.tplinkdns.com:5000/"

@st.dialog("Nova Conta")
def conta():
    file_url = ''
    with st.form("Conta"):
        nome = st.text_input("Nome")
        data = datetime.combine(st.date_input('Data', min_value='2000-01-01', format="DD/MM/YYYY"), datetime.min.time())
        valor = st.number_input("Valor")
        brassaco = st.toggle("Brassaco")
        categoria = st.selectbox("Categoria", lista_categorias)
        conta = st.selectbox("Conta", ["Corrente", "Cartão Itau", "Nubank", "Camila"])
        obs = st.text_input("Observação")
        # Calcular a data da fatura para Cartão Itau
        fatura = None
        if conta == "Cartão Itau":
            dia = data.day
            if dia <= 30:
                # Para compras até dia 30, fatura cai no dia 6 do próximo mês
                fatura = data.replace(day=6, month=data.month % 12 + 1)
            else:
                # Para compras entre 30 e 6, fatura cai no dia 6 do mês seguinte ao próximo
                fatura = data.replace(day=6)
                fatura = fatura.replace(month=fatura.month % 12 + 1)
                if fatura.month == 12:
                    fatura = fatura.replace(year=fatura.year + 1)
        
        uploaded_file = st.file_uploader("Recibo de pagamento")
        if uploaded_file:
            file_url = upload_arquivo_drive(uploaded_file, 'recibo_' + uploaded_file.name)
            st.success("Arquivo enviado com sucesso!")
        if st.form_submit_button("Cadastrar"):
            despesas_cadastrar(nome, categoria, data, valor, brassaco, file_url, conta, fatura, obs)   
            st.rerun()   


@st.dialog("Nova Receita")
def receita():
    with st.form("Receita"):
        nome = st.text_input("Nome")
        data = datetime.combine(st.date_input('Data', min_value='2000-01-01', format="DD/MM/YYYY"), datetime.min.time())
        valor = st.number_input("Valor")
        pagador = st.selectbox("Conta", ["Brassaco", "Quattor",'Outros'])
        if st.form_submit_button("Cadastrar"):
            receitas_cadastrar(nome, data, valor, pagador)
            st.rerun()
    
with col2:
    st.button("➕ Nova Despesa", on_click=conta, type="primary")
with col3:  
    st.button("➕ Nova Receita", on_click=receita, type="secondary")


@st.dialog("Editar despesa")
def editar(id, nome, categoria, data, valor, brassaco, conta, obs):
    file_url = ''
    with st.form("Editar despesa"):
        categoria = st.selectbox("Categoria", lista_categorias, key='categoria')
        categorias = lista_categorias
        contas = ["Corrente", "Cartão Itau", "Nubank", "Camila"]
        
        categoria_index = categorias.index(categoria) if categoria in categorias else 0
        conta_index = contas.index(conta) if conta in contas else 0
        
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome", value=nome)
            categoria = st.selectbox("Categoria", categorias, index=categoria_index)
            data = datetime.combine(st.date_input('Data', value=data, format="DD/MM/YYYY"), datetime.min.time())
        with col2:
            valor_atual = float(valor.replace('R$', '').replace('.', '').replace(',', '.').strip())
            valor = st.number_input("Valor", value=valor_atual)
            conta = st.selectbox("Conta", contas, index=conta_index)
            brassaco = st.toggle("Brassaco", value=brassaco)
            obs = st.text_input("Observação", value=obs)
            # Calcular a data da fatura para Cartão Itau
            fatura = None
            if conta == "Cartão Itau":
                dia = data.day
                if dia <= 30:
                    fatura = data.replace(day=6, month=data.month % 12 + 1)
                else:
                    fatura = data.replace(day=6)
                    fatura = fatura.replace(month=fatura.month % 12 + 1)
                    if fatura.month == 12:
                        fatura = fatura.replace(year=fatura.year + 1)
            if conta == "Nubank":
                dia = data.day
                if dia <= 18:
                    # Para compras até dia 18, fatura cai no dia 10 do próximo mês
                    fatura = data.replace(day=25)
                    
                else:
                    # Para compras após dia 18, fatura cai no dia 25 do mesmo mês
                    fatura = data.replace(day=25, month=data.month % 12 + 1)
                    if fatura.month == 12:
                        fatura = fatura.replace(year=fatura.year + 1)
        
        uploaded_file = st.file_uploader("Recibo de pagamento")
        if uploaded_file:
            file_url = upload_arquivo_drive(uploaded_file, 'recibo_' + uploaded_file.name)
            st.success("Arquivo enviado com sucesso!")
            

        if st.form_submit_button("Gravar"):
            try:
                despesas_editar(id, nome, categoria, data, valor, brassaco, file_url, conta, fatura, obs)
                st.success("Despesa atualizada com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao atualizar despesa: {str(e)}")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Apagar", type='secondary', icon="❌"):
            df_desp_apagar(id)
            st.success("Despesa apagada com sucesso!")
            st.rerun()        




with st.sidebar:
    st.subheader("Filtros")
    data_inicio = datetime.now().replace(day=1)  # Primeiro dia do mês atual
    data_fim = (data_inicio.replace(month=data_inicio.month % 12 + 1, day=1) - timedelta(days=1))  # Último dia do mês atual
    filtro_data = st.date_input("Período", value=(data_inicio, data_fim), format="DD/MM/YYYY")
    filtro_categoria = st.selectbox("Categoria", ["Todas"] + lista_categorias)
    filtro_brassaco = st.toggle("Brassaco")
    filtro_conta = st.selectbox("Conta", ["Todas", "Corrente", "Cartão Itau", "Nubank", "Camila"])
    
    # Converter contas para DataFrame e obter faturas únicas
    contas_df_temp = pd.DataFrame(contas)
    if not contas_df_temp.empty:
        faturas_unicas = ["Todas"] + sorted([f.strftime("%d-%B") for f in contas_df_temp['fatura'].dropna().unique()])
        filtro_fatura = st.selectbox("Fatura", faturas_unicas)


# Converter a lista para DataFrame
contas_df = pd.DataFrame(contas)
contas_df_sem_filtros = pd.DataFrame(contas)

receitas_df = pd.DataFrame(receitas)
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

# Filtrar por categoria
if filtro_categoria != "Todas":
    contas_df = contas_df[contas_df['categoria'] == filtro_categoria]

# Filtrar por brassaco
if filtro_brassaco:
    contas_df = contas_df[contas_df['brassaco'] == True]

# Filtrar por conta
if filtro_conta != "Todas":
    contas_df = contas_df[contas_df['conta'] == filtro_conta]

# Filtrar por fatura
if not contas_df.empty:
    if filtro_fatura != "Todas":
        contas_df = contas_df[contas_df['fatura'].dt.strftime("%d-%B") == filtro_fatura]

contas_df["Editar"] = False

contas = dataframe_explorer(contas_df, case=False)   
if contas_df.empty:
    st.warning("Nenhuma despesa encontrada")
else:
    # Criar uma cópia para exibição
    contas_display = contas.copy()
    contas_display["valor"] = contas["valor"].apply(lambda x: formatar_moeda(x))
    edited_df = st.data_editor(
        contas_display, 
        column_order=[ 'Editar','nome',"categoria", "data", "valor", 'brassaco','conta','fatura' ,'comprovante','obs'], 
        column_config={
            "data": st.column_config.DateColumn(
                "Data", format="DD/MM/YYYY",
            ),
            "fatura": st.column_config.DateColumn(
                "Fatura", format="DD-MMMM",
            ),
            "comprovante": st.column_config.LinkColumn(
                "Comprovante", display_text="📂",
                disabled=True,
            ),
            "Editar": st.column_config.CheckboxColumn(
                "Editar",
                width="small",
                pinned=True,
                help="Marque para editar esta linha",
                default=False,
            )
        },
        hide_index=True, 
        height=300, 
        num_rows="fixed"
    )

col1, col2 = st.columns(2)
with col1:
    if st.button("Editar", type='secondary', icon="✍🏻"):
            linha_selecionada = edited_df[edited_df["Editar"] == True]
            if not linha_selecionada.empty:
                # Convertendo os valores da Series para valores únicos
                id = linha_selecionada["_id"].iloc[0]
                nome = linha_selecionada["nome"].iloc[0]
                data = linha_selecionada["data"].iloc[0]
                valor = linha_selecionada["valor"].iloc[0]
                categoria = linha_selecionada["categoria"].iloc[0]
                brassaco = linha_selecionada["brassaco"].iloc[0]
                conta = linha_selecionada["conta"].iloc[0]
                obs = linha_selecionada["obs"].iloc[0]
                editar(id, nome, categoria, data, valor, brassaco, conta, obs)
            else:
                st.warning("Selecione uma linha para editar")

with col2:
    if not contas_df.empty:
        st.subheader("Total: "+formatar_moeda(contas_df['valor'].sum()))

st.subheader("Receitas")
receitas_df = pd.DataFrame(receitas)
if receitas_df.empty:
    st.warning("Nenhuma receita encontrada")
else:
    # Criar uma cópia para exibição
    receitas_display = receitas_df.copy()
    receitas_display["valor"] = receitas_df["valor"].apply(lambda x: formatar_moeda(x))
    edited_df_receitas = st.data_editor(
        receitas_display, 
        column_order=['nome',"categoria", "data", "valor", 'conta'], 
        column_config={
            "data": st.column_config.DateColumn(
                "Data", format="DD/MM/YYYY",
            ),
        },
        hide_index=True, 
        height=100, 
        num_rows="fixed"
    )

col1, col2 = st.columns(2)
with col1:
    st.subheader("Total: "+formatar_moeda(receitas_df['valor'].sum()))
with col2:
    # Filtrar apenas contas com brassaco True
    if not contas_df_sem_filtros.empty:
        contas_brassaco = contas_df_sem_filtros[contas_df_sem_filtros['brassaco'] == True]
        st.subheader("Saldo Brassaco: "+formatar_moeda( receitas_df['valor'].sum() - contas_brassaco['valor'].sum() ))
        

    