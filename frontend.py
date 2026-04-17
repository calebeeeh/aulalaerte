import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import text
from database import engine, criar_tabelas

st.set_page_config(page_title="DF Imóveis — Taguatinga Norte", page_icon="🏠", layout="wide")

criar_tabelas()

CORES = ["#2563eb", "#16a34a", "#dc2626"]


@st.cache_data(ttl=60)
def carregar_dados():
    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT i.id, i.endereco, i.tamanho_m2, i.preco, i.quartos, i.vagas,
                   i.data_coleta, op.nome_operacao AS operacao
            FROM tb_imoveis i
            LEFT JOIN tb_tipo_operacao op ON i.id_operacao = op.id
        """), conn)
    # remove outliers de coleta incorreta
    df = df[df["preco"].notna() & (df["preco"] <= 8000) & (df["preco"] >= 400)]
    df["quartos"] = df["quartos"].fillna(0).astype(int)
    df["vagas"] = df["vagas"].fillna(0).astype(int)
    df["quartos_cat"] = df["quartos"].astype(str) + " quarto(s)"
    return df


with st.sidebar:
    st.markdown("### 📍 Taguatinga Norte, DF")
    st.info("Dados coletados de **dfimoveis.com.br**")
    if st.button("🔄 Atualizar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

df = carregar_dados()

if df.empty:
    st.warning("Nenhum dado encontrado.")
    st.stop()

# ── Cabeçalho ────────────────────────────────────────────────────────────────
st.markdown("## 🏠 Mercado de Aluguel — Taguatinga Norte, DF")
st.caption(f"Baseado em {len(df)} anúncios coletados do dfimoveis.com.br")
st.markdown("---")

# ── Métricas ──────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Imóveis analisados", len(df))
c2.metric("Aluguel médio", f"R$ {df['preco'].mean():,.0f}")
c3.metric("Aluguel mínimo", f"R$ {df['preco'].min():,.0f}")
c4.metric("Aluguel máximo", f"R$ {df['preco'].max():,.0f}")
c5.metric("Mediana", f"R$ {df['preco'].median():,.0f}")

st.markdown("---")

# ── Linha 1 ───────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Distribuição dos Aluguéis")
    st.caption("Faixa de preço mais comum na região")
    fig1 = px.histogram(
        df, x="preco", nbins=25,
        labels={"preco": "Aluguel (R$)", "count": "Qtd. imóveis"},
        color_discrete_sequence=["#2563eb"],
    )
    fig1.add_vline(
        x=df["preco"].median(), line_dash="dash", line_color="#f59e0b",
        annotation_text=f"Mediana: R$ {df['preco'].median():,.0f}",
        annotation_position="top right",
        annotation_font_color="#f59e0b",
    )
    fig1.update_layout(
        bargap=0.05,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis_title="Qtd. imóveis",
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.markdown("#### Quantidade de Imóveis por Nº de Quartos")
    st.caption("Como o estoque está distribuído na região")
    contagem = df["quartos_cat"].value_counts().reset_index()
    contagem.columns = ["Quartos", "Quantidade"]
    contagem = contagem.sort_values("Quartos")
    fig2 = px.bar(
        contagem, x="Quartos", y="Quantidade",
        text="Quantidade",
        color="Quartos",
        color_discrete_sequence=CORES,
    )
    fig2.update_traces(textposition="outside", textfont_size=14)
    fig2.update_layout(
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Linha 2 ───────────────────────────────────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.markdown("#### Aluguel Médio por Nº de Quartos")
    st.caption("Impacto do número de quartos no preço")
    media_q = df.groupby("quartos_cat")["preco"].mean().reset_index().sort_values("quartos_cat")
    media_q.columns = ["Quartos", "Aluguel Médio"]
    fig3 = px.bar(
        media_q, x="Quartos", y="Aluguel Médio",
        text=media_q["Aluguel Médio"].apply(lambda x: f"R$ {x:,.0f}"),
        color="Quartos",
        color_discrete_sequence=CORES,
    )
    fig3.update_traces(textposition="outside", textfont_size=13)
    fig3.update_layout(
        showlegend=False,
        yaxis_tickprefix="R$ ",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.markdown("#### Variação de Preço por Nº de Quartos")
    st.caption("Min, mediana e máximo de aluguel em cada categoria")
    df_box = df[df["quartos"] > 0].copy()
    fig4 = px.box(
        df_box, x="quartos_cat", y="preco",
        color="quartos_cat",
        color_discrete_sequence=CORES,
        labels={"quartos_cat": "Quartos", "preco": "Aluguel (R$)"},
        points="outliers",
        category_orders={"quartos_cat": ["1 quarto(s)", "2 quarto(s)", "3 quarto(s)"]},
    )
    fig4.update_layout(
        showlegend=False,
        yaxis_tickprefix="R$ ",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig4, use_container_width=True)

# ── Linha 3 ───────────────────────────────────────────────────────────────────
col5, col6 = st.columns(2)

with col5:
    st.markdown("#### Tamanho × Aluguel")
    st.caption("Imóveis maiores custam proporcionalmente mais?")
    df_m2 = df[df["tamanho_m2"].notna() & (df["tamanho_m2"] > 0) & (df["quartos"] > 0)].copy()
    fig5 = px.scatter(
        df_m2, x="tamanho_m2", y="preco",
        color="quartos_cat",
        color_discrete_sequence=CORES,
        labels={"tamanho_m2": "Tamanho (m²)", "preco": "Aluguel (R$)", "quartos_cat": "Quartos"},
        hover_data={"endereco": True},
        opacity=0.75,
        category_orders={"quartos_cat": ["1 quarto(s)", "2 quarto(s)", "3 quarto(s)"]},
    )
    fig5.update_layout(
        yaxis_tickprefix="R$ ",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig5, use_container_width=True)

with col6:
    st.markdown("#### Custo por m² — Por Nº de Quartos")
    st.caption("Qual categoria oferece melhor custo-benefício?")
    df_cpm2 = df_m2.copy()
    df_cpm2["preco_m2"] = df_cpm2["preco"] / df_cpm2["tamanho_m2"]
    ranking = df_cpm2.groupby("quartos_cat")["preco_m2"].mean().reset_index().sort_values("quartos_cat")
    ranking.columns = ["Quartos", "R$/m²"]
    fig6 = px.bar(
        ranking, x="Quartos", y="R$/m²",
        text=ranking["R$/m²"].apply(lambda x: f"R$ {x:.0f}/m²"),
        color="Quartos",
        color_discrete_sequence=CORES,
    )
    fig6.update_traces(textposition="outside", textfont_size=13)
    fig6.update_layout(
        showlegend=False,
        yaxis_tickprefix="R$ ",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig6, use_container_width=True)

# ── Tabela ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("#### Todos os Imóveis")
df_tabela = df[["endereco", "preco", "tamanho_m2", "quartos", "vagas", "data_coleta"]].copy()
df_tabela.columns = ["Endereço", "Aluguel (R$)", "Tamanho (m²)", "Quartos", "Vagas", "Data Coleta"]
df_tabela["Aluguel (R$)"] = df_tabela["Aluguel (R$)"].apply(lambda x: f"R$ {x:,.0f}")
st.dataframe(df_tabela, use_container_width=True, hide_index=True)
