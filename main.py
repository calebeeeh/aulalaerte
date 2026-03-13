from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy import create_engine, text
import pandas as pd
from fastapi import FastAPI
# configuracao do conexao com banco de dados
host = "127.0.0.1"
port = 3306
user = "root"
password = "ibmecdf"
banco_dados = "db_escola"
engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/{banco_dados}")
# instaciar
app = FastAPI()

# schema
class Aluno(BaseModel):
    matricula: str
    nome_aluno: str
    email: Optional[str]
    endereco_id: Optional[int] = None

class MsgPost(BaseModel):
    mensagem: str


@app.get("/alunos/", response_model=List[Aluno])
def listar_alunos():
    query = "select * from tb_alunos"
    df_alunos = pd.read_sql(query, con=engine)
    return df_alunos.to_dict(orient="records")

@app.post("/cadastrar-aluno/", response_model=MsgPost)
def cadastrar_alunos(aluno:dict):
    df = pd.DataFrame([aluno])
    df.to_sql("tb_alunos", engine, if_exists="append", index=False)
    return {"mensagem": "Alunos Cadastrado com sucesso."}

@app.put("/atualizar-alunos/{id}")
def atualizar_alunos(id:int, alunos:dict):
    with engine.begin() as conn:
        conn.execute(
            text(
            """
                update tb_alunos
                set matricula = :matricula,
                nome_aluno = :nome_aluno,
                email = :email,
                endereco_id = :endereco_id
                where id = :id
            """
        ), {"id":id, **alunos}
    )
    return {"mensagem": "Alunos Atualizado com sucesso."}

@app.delete("/deletar-alunos/{id}")
def deletar_alunos(id:int):
    with engine.begin() as conn:
        conn.execute(
            text(
            """
                delete from tb_alunos
                where id = :id
            """
        ), {"id":id}
    )
    return {"mensagem": "Aluno Deletado com sucesso."}


