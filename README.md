# DF Imóveis — Dashboard de Aluguel em Taguatinga Norte

Dashboard interativo com dados coletados automaticamente do site [dfimoveis.com.br](https://www.dfimoveis.com.br), exibindo análises do mercado de aluguel em Taguatinga Norte, DF.

## Acesso Online

O projeto está disponível em:

- **Dashboard:** https://dfimoveis-frontend.onrender.com
- **API:** https://dfimoveis-api-795z.onrender.com/docs

---

## Tecnologias

| Ferramenta | Função |
|---|---|
| Selenium + undetected_chromedriver | Web scraping do dfimoveis.com.br |
| SQLite + SQLAlchemy | Banco de dados e ORM |
| FastAPI | API REST |
| Streamlit + Plotly | Dashboard interativo |
| Docker | Containerização |
| Render.com | Deploy em nuvem |

---

## Rodar Localmente com Docker

### Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- [Git](https://git-scm.com/downloads)

### Passo 1 — Clonar o repositório

```bash
git clone https://github.com/calebeeeh/aulalaerte.git
cd aulalaerte
```

### Passo 2 — Subir o projeto

```bash
docker-compose up --build
```

> Na primeira vez demora ~5 minutos porque instala Python, dependências e Google Chrome automaticamente.

Quando aparecer no terminal:
```
api       | Uvicorn running on http://0.0.0.0:8000
frontend  | You can now view your Streamlit app
```
o projeto está pronto.

### Passo 3 — Acessar o dashboard

Abra o browser em: **http://localhost:8501**

### Passo 4 — Rodar o scraping

Com o projeto rodando, abra outro terminal e execute:

```bash
docker-compose exec api python -c "from scraper import executar_scraping; executar_scraping()"
```

O Chrome roda invisível (headless) dentro do container e coleta os dados automaticamente. Ao finalizar, clique em **Atualizar dados** no dashboard.

### Passo 5 — Parar o projeto

```bash
docker-compose down
```

---

## Comandos Úteis

| Ação | Comando |
|---|---|
| Subir o projeto | `docker-compose up --build` |
| Parar o projeto | `docker-compose down` |
| Executar scraping | `docker-compose exec api python -c "from scraper import executar_scraping; executar_scraping()"` |
| Ver logs em tempo real | `docker-compose logs -f` |

---

## Endpoints da API

| Método | Rota | Descrição |
|---|---|---|
| POST | `/scraping` | Inicia a coleta de dados |
| GET | `/imoveis-resumo` | Retorna estatísticas gerais |
| GET | `/imoveis` | Lista todos os imóveis |
| GET | `/docs` | Documentação interativa |

---

## Estrutura do Projeto

```
aulalaerte/
├── api.py            # API FastAPI
├── scraper.py        # Web scraping com Selenium
├── database.py       # Banco de dados SQLite
├── frontend.py       # Dashboard Streamlit
├── requirements.txt  # Dependências Python
├── Dockerfile        # Imagem Docker
├── docker-compose.yml
└── imoveis.db        # Banco de dados
```
