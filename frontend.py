import os
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from sqlalchemy import text
from database import engine, criar_tabelas

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="DF Imóveis", page_icon="🏠", layout="wide")
st.title("🏠 DF Imóveis — Dashboard")

criar_tabelas()


@st.cache_data(ttl=60)
def carregar_dados():
    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT i.id, i.endereco, i.tamanho_m2, i.preco, i.quartos, i.vagas,
                   i.suites, i.data_coleta,
                   op.nome_operacao AS operacao,
                   tp.nome_tipo_imovel AS tipo
            FROM tb_imoveis i
            LEFT JOIN tb_tipo_operacao op ON i.id_operacao = op.id
            LEFT JOIN tb_tipo_imovel tp ON i.id_tipo_imovel = tp.id
        """), conn)
    return df


# ─── Sidebar: Scraping ───────────────────────────────────────────────────────
with st.sidebar:
    st.header("Executar Scraping")
    tipo = st.selectbox("Tipo de negócio", ["ALUGUEL", "VENDA"])
    tipos = st.selectbox("Tipo de imóvel", ["APARTAMENTO", "CASA", "COMERCIAL"])
    estado = st.text_input("Estado", value="DF")
    cidade = st.text_input("Cidade", value="TAGUATINGA")
    bairro = st.text_input("Bairro", value="TAGUATINGA NORTE")

    if st.button("▶ Iniciar Scraping", use_container_width=True):
        try:
            resp = requests.post(
                f"{API_URL}/scraping",
                params={"tipo": tipo, "tipos": tipos, "estado": estado,
                        "cidade": cidade, "bairro": bairro},
                timeout=5,
            )
            if resp.status_code == 200:
                st.success("Scraping iniciado em background!")
            else:
                st.warning(resp.json().get("mensagem", "Erro."))
        except Exception:
            st.error("API não está rodando. Inicie com: uvicorn api:app --reload")

    st.markdown("---")
    if st.button("🔄 Atualizar dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ─── Dados ───────────────────────────────────────────────────────────────────
df = carregar_dados()

if df.empty:
    st.info("Nenhum dado encontrado. Execute o scraping pelo painel lateral.")
    st.stop()

# ─── Métricas ─────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de imóveis", len(df))
col2.metric("Preço médio", f"R$ {df['preco'].mean():,.2f}" if df['preco'].notna().any() else "—")
col3.metric("Preço mínimo", f"R$ {df['preco'].min():,.2f}" if df['preco'].notna().any() else "—")
col4.metric("Preço máximo", f"R$ {df['preco'].max():,.2f}" if df['preco'].notna().any() else "—")

st.markdown("---")

# ─── Gráficos ─────────────────────────────────────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Distribuição de Preços")
    df_preco = df[df["preco"].notna()]
    if not df_preco.empty:
        fig = px.histogram(df_preco, x="preco", nbins=30, labels={"preco": "Preço (R$)"},
                           color_discrete_sequence=["#1f77b4"])
        fig.update_layout(bargap=0.1)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados de preço.")

with col_b:
    st.subheader("Preço Médio por Número de Quartos")
    df_quartos = df[df["quartos"].notna() & df["preco"].notna()]
    if not df_quartos.empty:
        media = df_quartos.groupby("quartos")["preco"].mean().reset_index()
        media.columns = ["Quartos", "Preço Médio"]
        fig2 = px.bar(media, x="Quartos", y="Preço Médio",
                      labels={"Preço Médio": "Preço Médio (R$)"},
                      color="Quartos", color_continuous_scale="Blues")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Sem dados de quartos.")

col_c, col_d = st.columns(2)

with col_c:
    st.subheader("Quantidade por Tipo de Imóvel")
    if "tipo" in df.columns and df["tipo"].notna().any():
        contagem = df["tipo"].value_counts().reset_index()
        contagem.columns = ["Tipo", "Quantidade"]
        fig3 = px.pie(contagem, names="Tipo", values="Quantidade")
        st.plotly_chart(fig3, use_container_width=True)

with col_d:
    st.subheader("Preço por Tamanho (m²)")
    df_m2 = df[df["tamanho_m2"].notna() & df["preco"].notna()]
    if not df_m2.empty:
        fig4 = px.scatter(df_m2, x="tamanho_m2", y="preco",
                          labels={"tamanho_m2": "Tamanho (m²)", "preco": "Preço (R$)"},
                          opacity=0.6, color_discrete_sequence=["#2ca02c"])
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("Sem dados suficientes.")

# ─── Tabela ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Tabela de Imóveis")
st.dataframe(
    df[["endereco", "tipo", "operacao", "preco", "tamanho_m2", "quartos", "vagas", "data_coleta"]],
    use_container_width=True,
    hide_index=True,
)
