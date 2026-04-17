import multiprocessing
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from sqlalchemy import text
from database import engine, criar_tabelas
from scraper import executar_scraping

app = FastAPI(title="DF Imóveis API", version="1.0.0")

_processo_scraping: multiprocessing.Process | None = None


@app.on_event("startup")
def startup():
    criar_tabelas()


@app.post("/scraping")
def post_scraping(
    tipo: str = Query(default="ALUGUEL"),
    tipos: str = Query(default="APARTAMENTO"),
    estado: str = Query(default="DF"),
    cidade: str = Query(default="TAGUATINGA"),
    bairro: str = Query(default="TAGUATINGA NORTE"),
):
    global _processo_scraping
    if _processo_scraping and _processo_scraping.is_alive():
        return JSONResponse(
            status_code=409,
            content={"mensagem": "Scraping já está em andamento."},
        )

    _processo_scraping = multiprocessing.Process(
        target=executar_scraping,
        args=(tipo, tipos, estado, cidade, bairro),
        daemon=True,
    )
    _processo_scraping.start()

    return {"mensagem": "Scraping iniciado.", "parametros": {
        "tipo": tipo, "tipos": tipos, "estado": estado,
        "cidade": cidade, "bairro": bairro,
    }}


@app.get("/imoveis-resumo")
def get_resumo():
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM tb_imoveis")).scalar()
        preco_medio = conn.execute(
            text("SELECT ROUND(AVG(preco), 2) FROM tb_imoveis WHERE preco IS NOT NULL")
        ).scalar()
        preco_min = conn.execute(
            text("SELECT MIN(preco) FROM tb_imoveis WHERE preco IS NOT NULL")
        ).scalar()
        preco_max = conn.execute(
            text("SELECT MAX(preco) FROM tb_imoveis WHERE preco IS NOT NULL")
        ).scalar()

        por_quartos = conn.execute(text("""
            SELECT quartos, COUNT(*) as quantidade, ROUND(AVG(preco), 2) as preco_medio
            FROM tb_imoveis
            WHERE quartos IS NOT NULL
            GROUP BY quartos
            ORDER BY quartos
        """)).fetchall()

        por_tipo = conn.execute(text("""
            SELECT t.nome_tipo_imovel, COUNT(*) as quantidade
            FROM tb_imoveis i
            JOIN tb_tipo_imovel t ON i.id_tipo_imovel = t.id
            GROUP BY t.nome_tipo_imovel
        """)).fetchall()

    return {
        "total_imoveis": total,
        "preco_medio": preco_medio,
        "preco_minimo": preco_min,
        "preco_maximo": preco_max,
        "por_quartos": [
            {"quartos": r[0], "quantidade": r[1], "preco_medio": r[2]}
            for r in por_quartos
        ],
        "por_tipo": [
            {"tipo": r[0], "quantidade": r[1]}
            for r in por_tipo
        ],
    }


@app.get("/imoveis")
def get_imoveis(limit: int = Query(default=100, le=500)):
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT i.id, i.endereco, i.tamanho_m2, i.preco, i.quartos, i.vagas,
                   i.suites, i.data_coleta,
                   op.nome_operacao, tp.nome_tipo_imovel
            FROM tb_imoveis i
            LEFT JOIN tb_tipo_operacao op ON i.id_operacao = op.id
            LEFT JOIN tb_tipo_imovel tp ON i.id_tipo_imovel = tp.id
            ORDER BY i.id DESC
            LIMIT :limit
        """), {"limit": limit}).fetchall()

    return [
        {
            "id": r[0], "endereco": r[1], "tamanho_m2": r[2],
            "preco": r[3], "quartos": r[4], "vagas": r[5],
            "suites": r[6], "data_coleta": r[7],
            "operacao": r[8], "tipo": r[9],
        }
        for r in rows
    ]
