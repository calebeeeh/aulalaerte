from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import create_engine, text
import pandas as pd
import sqlite3
from fastapi import FastAPI
import requests

# configuracao de conexao com o banco de dados
host = "127.0.0.1"
port = 3306
user = "root"
password = "Zen%402425"
banco_dados = "db_escola"

# engine para conectar com o banco de dados
engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/{banco_dados}")

class Aluno(BaseModel):
    matricula: str
    nome_aluno: str
    email: Optional[str] = None
    endereco_id: Optional[int] = None

class MsgPost(BaseModel):
    message: str

# instanciar
app = FastAPI()

@app.get("/alunos/", response_model=list[Aluno])
def listar_alunos():
    query = "select * from tb_alunos"
    df_alunos = pd.read_sql(query, con=engine)
    return df_alunos.to_dict(orient="records")

@app.post("/cadastrar_aluno/{id}", response_model=MsgPost)
def cadastrar_aluno(aluno: dict):
    df = pd.DataFrame([aluno])
    df.to_sql("tb_alunos", engine, if_exists="append", index=False)
    return {"message": "Aluno cadastrado"}

@app.put("/atualizar_aluno/{id}")
def atualizar_aluno(id: int, alunos: dict):
    with engine.begin() as conn:
        conn.execute(
            text(
            '''
            update tb_alunos
            set matricula = :matricula,
            nome_aluno = :nome_aluno,
            email = :email,
            endereco_id = :endereco_id
            where id = :id
            '''
            ), {"id": id, **alunos}
        )
        return {"message": "Aluno atualizado"}

@app.delete("/deletar_aluno/{id}")
def deletar_aluno(id: int):
    with engine.begin() as conn:
        conn.execute(
            text(
            '''
            delete from tb_alunos
            where id = :id
            '''
            ), {"id": id}
        )
        return {"message": "Aluno deletado"}

@app.patch("/atualizar_nome/{id}")
def atualizar_nome(id: int, nome: dict):
    with engine.begin() as conn:
        conn.execute(
            text(
            '''
            update tb_alunos
            set nome_aluno = :nome_aluno
            where id = :id
            '''
            ), {"id": id, **nome}
        )
        return {"message": "Nome do aluno atualizado"}

@app.post("/cadastrar_endereco/", response_model=MsgPost)
def cadastrar_endereco(endereco: dict):
    df = pd.DataFrame([endereco])
    df.to_sql("tb_enderecos", engine, if_exists="append", index=False)
    return {"message": "Endereço cadastrado"}

@app.post("/cadastrar_endereco_cep/", response_model=MsgPost)
def cadastrar_endereco_cep(dados: dict):
    cep_digitado = dados["cep"]
    link = f"https://viacep.com.br/ws/{cep_digitado}/json/"
    resposta = requests.get(link)
    dados_viacep = resposta.json()
    endereco_final = {
        "cep": cep_digitado,
        "endereco": dados_viacep["logradouro"],
        "bairro": dados_viacep["bairro"],
        "cidade": dados_viacep["localidade"],
        "estado": dados_viacep["estado"],
        "regiao": dados_viacep["regiao"]
    }
    df = pd.DataFrame([endereco_final])
    df.to_sql("tb_enderecos", engine, if_exists="append", index=False)
    return {"message": "Endereco cadastrado"}


