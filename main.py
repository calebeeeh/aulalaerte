from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import create_engine, text
import pandas as pd
from fastapi import FastAPI
# configuracao do conexao com banco de dados
host = "127.0.0.1"
port = 3306
user = "root"
password = "Zen@2425"
banco_dados = "db_escola"
engine = create_engine("mysql+pymysql://root:Zen%402425@127.0.0.1:3306/db_escola")
# instaciar
app = FastAPI()

#schema
class aluno(BaseModel):
    matricula:str
    nome_aluno:str
    email:Optional[str] = None
    endereco_id: Optional[int] = None

class MsgPost(BaseModel):
    mensagem : str

@app.get("/alunos/", response_model=list[aluno])
def listar_alunos():
    query = "select * from tb_alunos"
    df_alunos = pd.read_sql(query, con=engine)
    return df_alunos.to_dict(orient="records")

@app.post("/cadastrar-aluno/")
def cadastrar_alunos(aluno:dict):
    df = pd.DataFrame([aluno])
    df.to_sql("tb_alunos", engine, if_exists="append", index=False)
    return {"mensagem": "Alunos Cadastrado com sucesso."}

@app.delete("/deletar-aluno/{id}")
def atualizar_alunos(id:int):
    with engine.begin() as conn:
        conn.execute(
            text(
            """
                delete from tb_alunos
                where id = :id


            """
        ), {"id":id}
     )
    return {"mensagem":"aluno deletado com sucesso"}

