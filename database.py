import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///imoveis.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)


def criar_tabelas():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tb_tipo_imovel (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_tipo_imovel TEXT NOT NULL UNIQUE
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tb_tipo_operacao (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_operacao TEXT NOT NULL UNIQUE
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tb_imobiliaria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_imobiliaria TEXT NOT NULL UNIQUE
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tb_imoveis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endereco TEXT,
                tamanho_m2 REAL,
                preco REAL,
                quartos INTEGER,
                vagas INTEGER,
                suites INTEGER,
                data_coleta TEXT DEFAULT (datetime('now')),
                id_operacao INTEGER REFERENCES tb_tipo_operacao(id),
                id_imobiliaria INTEGER REFERENCES tb_imobiliaria(id),
                id_tipo_imovel INTEGER REFERENCES tb_tipo_imovel(id)
            )
        """))
