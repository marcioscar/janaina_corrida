from bson import ObjectId
from dotenv import load_dotenv
import pandas as pd
from pymongo import MongoClient
import streamlit as st
import pymongo
from datetime import datetime
import os

filtro = {
    "data": {"$gte": datetime(2025, 1, 1)}  # Data maior ou igual a 1 de janeiro de 2025
}

filtro_despesas = {
    "data": {"$gte": datetime(2025, 1, 1)},  # Data maior ou igual a 1 de janeiro de 2025
    "$or": [
        {"pago": True},   # Registros onde pago é True
        {"pago": {"$exists": False}}  # Registros onde pago não existe
    ]
}




@st.cache_resource
def conexao():
    try:
        load_dotenv()
        uri = os.getenv("DATABASE_URL")
        client = MongoClient(uri, server_api=pymongo.server_api.ServerApi(
        version="1", strict=True, deprecation_errors=True))
    except Exception as e:
        raise Exception(
            "Erro: ", e)
    db = client["corridas"]
    st.session_state.db = db
    return  db


def get_contas():
    db = conexao()
    contas = db["despesas"]
    data_despesas = list(contas.find(filtro_despesas))
    return data_despesas

def get_receitas():
    db = conexao()
    receitas = db["receitas"]
    data_receitas = list(receitas.find())
    return data_receitas

def get_livros():
    db = conexao()
    livros = db["biblioteca"]
    data_livros = list(livros.find())
    return data_livros



@st.cache_resource
def despesas_cadastrar(nome, categoria, data, valor, brassaco, comprovante, conta, fatura, obs):
    db = conexao()
    despesas = db["despesas"]
    print(data)
    # Determina a data da fatura para Cartão Itau
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
                
    data_despesas_cadastrar = despesas.insert_one({
        "nome": nome,
        "categoria": categoria,
        "valor": valor,
        "data": data,
        "brassaco": brassaco,
        "comprovante": comprovante ,
        "conta": conta,
        "fatura":fatura,
        "obs": obs
    })
    return data_despesas_cadastrar

def despesas_editar(id,nome, categoria, data, valor, brassaco, comprovante,conta, fatura, obs):
    if comprovante == '':
        comprovante = 'Conta'
    filtro = {"_id": ObjectId(id)}
    db = conexao()
    despesas = db["despesas"]
    despesas.update_one(filtro, {"$set": {"nome": nome, "categoria": categoria, "data": data, "valor": valor, "brassaco": brassaco, "comprovante": comprovante, "conta": conta, "fatura": fatura, "obs": obs}})
    return despesas

def df_desp_apagar(id):
    db = conexao()
    try:
        # Converte a string do ID para ObjectId
        object_id = ObjectId(id)
        filtro = {"_id": object_id}
        print(f"ID: {id}")
        despesas = db["despesas"]
        despesas.delete_one(filtro)
        print(f"Despesa deletada com sucesso: {id}")
    except Exception as e:
        print(f"Erro ao deletar despesas: {e}")


@st.cache_resource
def receitas_cadastrar(nome, data, valor, pagador):
    db = conexao()
    receitas = db["receitas"]
    data_receitas_cadastrar = receitas.insert_one({
        "nome": nome,
        "data": data,
        "valor": valor,
        "pagador": pagador
    })
    return data_receitas_cadastrar


@st.cache_resource
def livros_cadastrar(nome, data, capa, citacao, nota, autor):
    db = conexao()
    livros = db["biblioteca"]
    data_livros_cadastrar = livros.insert_one({
        "nome": nome,
        "data": data,
        "capa": capa,
        "citacao": citacao,
        'nota': nota,
        'autor': autor
    })
    return data_livros_cadastrar

@st.cache_resource
def livros_editar(id, nome, data, capa, citacao, nota, autor):
    db = conexao()
    livros = db["biblioteca"]
    livros.update_one({"_id": ObjectId(id)}, {"$set": {"nome": nome, "data": data, "capa": capa, "citacao": citacao, "nota": nota, "autor": autor}})
    return livros

@st.cache_resource
def get_corridas():
    db = conexao()
    db1 = db["corridas"]
    colecao_corridas = db1["corridas"]
    return colecao_corridas

@st.cache_resource
def get_corridas_janaina():
    db = conexao()
    db1 = db["corridas"]
    colecao_corridas = db1["corridas_janaina"]
    return colecao_corridas

@st.cache_resource
def get_corridas_strava_janaina(id_strava):
    id_strava = int(id_strava)
    db = conexao()
    db1 = db["corridas"]
    colecao_corridas = db1["corridas_janaina"]
    data_maratonas_strava = list(colecao_corridas.find({"id": id_strava}))
    return data_maratonas_strava


@st.cache_resource
def get_corridas_strava(id_strava):
    id_strava = int(id_strava)
    db = conexao()
    db1 = db["corridas"]
    colecao_corridas = db1["corridas"]
    data_maratonas_strava = list(colecao_corridas.find({"id": id_strava}))
    return data_maratonas_strava

    

# @st.cache_resource
def get_maratonas():
    try:
        db = conexao()
        maratonas = db["maratonas"]
        data_maratonas = list(maratonas.find())
        if not data_maratonas:
            print("Nenhuma maratona encontrada no banco de dados")
            return pd.DataFrame()
        df_maratonas = pd.DataFrame(data_maratonas)
        return df_maratonas
    except Exception as e:
        return pd.DataFrame()

# @st.cache_resource
def get_maratonas_janaina():
    try:
        db = conexao()
        maratonas = db["maratonas_janaina"]
        data_maratonas = list(maratonas.find())
        if not data_maratonas:
            print("Nenhuma maratona encontrada no banco de dados")
            return pd.DataFrame()
        df_maratonas = pd.DataFrame(data_maratonas)
        return df_maratonas
    except Exception as e:
        return pd.DataFrame()


def maratonas_cadastrar_janaina(nome, data,local, tempo, link, mapa, documentos, gpx, id):
    db = conexao()
    maratonas = db["maratonas_janaina"]
    data_maratonas_cadastrar = maratonas.insert_one({
        "nome": nome,
        "data": data,
        "local": local,
        "tempo": tempo,
        "mapa": mapa  ,
        "link": link  ,
        "documentos": documentos ,
        "gpx": gpx ,
        "id_strava": id
    })
    return data_maratonas_cadastrar  

def maratonas_editar_janaina(id, nome, data, local, tempo, link, documentos, gpx, id_strava):
    db = conexao()
    maratonas = db["maratonas_janaina"]
    maratonas.update_one({"_id": ObjectId(id)}, {"$set": {"nome": nome, "data": data, "local": local, "tempo": tempo, "link": link, "documentos": documentos, "gpx": gpx, "id_strava": id_strava}})
    return maratonas

