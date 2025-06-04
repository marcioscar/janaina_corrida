from datetime import datetime
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io


st.set_page_config(page_title="Upload para Google Drive", layout="centered")


st.title("📤 Upload de Arquivos para Google Drive")

# 🔑 Configuração das credenciais
SERVICE_ACCOUNT_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive']

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

service = build('drive', 'v3', credentials=credentials)

# 🔥 ID da pasta no Google Drive
#upload-driver@arquivos-461412.iam.gserviceaccount.com #email da conta de serviço
FOLDER_ID = '1sXmhIXEPZUEMlo1xe3MrwpBrmnsexZtW' # recibos
FOLDER_ID = '1d-vkue1X6aVP97J6ETUnLkqzDeSge-jS' # biblioteca
FOLDER_ID ='1faYkjAxJzggR0sAzg6ijuCAG6mD47zuG' # recibos_quattor
FOLDER_ID = '1xmc_etpuUGdrUJgHMwZIXji5vVt_ySfH' # recibos_brassaco


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


# 🗂️ Upload via Streamlit
uploaded_file = st.file_uploader("Escolha um arquivo para enviar", type=None)

if uploaded_file is not None:
    st.write(f"🗂️ Arquivo selecionado: {uploaded_file.name}")

    if st.button("🚀 Enviar para o Google Drive"):
        with st.spinner("Enviando..."):
            link = upload_arquivo_drive(uploaded_file, uploaded_file.name)
        st.success("✅ Upload realizado com sucesso!")
        st.markdown(f"🔗 [Acesse o arquivo aqui]({link})")


st.markdown("---")
st.markdown("Desenvolvido com ❤️ usando Streamlit e Google Drive API")