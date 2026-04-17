import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import text
from database import engine, criar_tabelas

st.set_page_config(page_title="DF Imóveis — Taguatinga Norte", page_icon="🏠", layout="wide")

criar_tabelas()


@st.cache_data(ttl=60)
def carregar_dados():
    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT i.id, i.endereco, i.tamanho_m2, i.preco, i.quartos, i.vagas,
                   i.data_coleta,
                   op.nome_operacao AS operacao,
                   tp.nome_tipo_imovel AS tipo
            FROM tb_imoveis i
            LEFT JOIN tb_tipo_operacao op ON i.id_operacao = op.id
            LEFT JOIN tb_tipo_imovel tp ON i.id_tipo_imovel = tp.id
        """), conn)
    return df


with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/Bras%C3%ADlia_DF_01.jpg/320px-Bras%C3%ADlia_DF_01.jpg", width=250)
    st.markdown("### Filtros")
    st.info("Dados coletados de **Taguatinga Norte, DF** via dfimoveis.com.br")
    if st.button("🔄 Atualizar dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

df = carregar_dados()

if df.empty:
    st.warning("Nenhum dado encontrado.")
    st.stop()

df_valido = df[df["preco"].notna() & (df["preco"] > 0)]

# ── Cabeçalho ────────────────────────────────────────────────────────────────
st.markdown("## 🏠 Mercado de Aluguel — Taguatinga Norte, DF")
st.caption(f"Fonte: dfimoveis.com.br · {len(df)} imóveis analisados")
st.markdown("---")

# ── Métricas ──────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total de imóveis", len(df))
c2.metric("Aluguel médio", f"R$ {df_valido['preco'].mean():,.0f}")
c3.metric("Aluguel mínimo", f"R$ {df_valido['preco'].min():,.0f}")
c4.metric("Aluguel máximo", f"R$ {df_valido['preco'].max():,.0f}")
c5.metric("Mediana", f"R$ {df_valido['preco'].median():,.0f}")

st.markdown("---")

# ── Linha 1: Distribuição de preços + Preço por quartos ──────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Distribuição dos Aluguéis")
    st.caption("Como os preços estão concentrados na região")
    fig1 = px.histogram(
        df_valido, x="preco", nbins=20,
        labels={"preco": "Aluguel (R$)", "count": "Qtd. imóveis"},
        color_discrete_sequence=["#2563eb"],
    )
    fig1.add_vline(
        x=df_valido["preco"].median(), line_dash="dash", line_color="orange",
        annotation_text=f"Mediana R$ {df_valido['preco'].median():,.0f}",
        annotation_position="top right"
    )
    fig1.update_layout(bargap=0.05, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.markdown("#### Aluguel Médio por Número de Quartos")
    st.caption("Quanto custa a mais cada quarto adicional")
    df_q = df_valido[df_valido["quartos"].notna()].copy()
    df_q["quartos"] = df_q["quartos"].astype(int)
    media_q = df_q.groupby("quartos").agg(
        preco_medio=("preco", "mean"),
        quantidade=("preco", "count")
    ).reset_index()
    fig2 = px.bar(
        media_q, x="quartos", y="preco_medio",
        text=media_q["preco_medio"].apply(lambda x: f"R$ {x:,.0f}"),
        labels={"quartos": "Quartos", "preco_medio": "Aluguel Médio (R$)"},
        color="preco_medio", color_continuous_scale="Blues",
        hover_data={"quantidade": True},
    )
    fig2.update_traces(textposition="outside")
    fig2.update_layout(coloraxis_showscale=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig2, use_container_width=True)

# ── Linha 2: Preço por m² + Box plot ─────────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.markdown("#### Relação Tamanho × Aluguel")
    st.caption("Imóveis maiores tendem a custar mais?")
    df_m2 = df_valido[df_valido["tamanho_m2"].notna() & (df_valido["tamanho_m2"] > 0)].copy()
    df_m2["quartos_str"] = df_m2["quartos"].fillna(0).astype(int).astype(str) + " qto"
    fig3 = px.scatter(
        df_m2, x="tamanho_m2", y="preco",
        color="quartos_str",
        labels={"tamanho_m2": "Tamanho (m²)", "preco": "Aluguel (R$)", "quartos_str": "Quartos"},
        hover_data={"endereco": True},
    )
    fig3.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.markdown("#### Faixas de Preço por Quartos")
    st.caption("Variação e outliers de aluguel em cada categoria")
    df_box = df_valido[df_valido["quartos"].notna()].copy()
    df_box["quartos"] = df_box["quartos"].astype(int).astype(str) + " quarto(s)"
    fig4 = px.box(
        df_box, x="quartos", y="preco",
        labels={"quartos": "Quartos", "preco": "Aluguel (R$)"},
        color="quartos",
        points="outliers",
    )
    fig4.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig4, use_container_width=True)

# ── Linha 3: Preço por m² calculado + vagas ───────────────────────────────────
col5, col6 = st.columns(2)

with col5:
    st.markdown("#### Custo por m² — Ranking")
    st.caption("Qual número de quartos oferece melhor custo-benefício por m²?")
    df_cpm2 = df_valido[df_valido["tamanho_m2"].notna() & (df_valido["tamanho_m2"] > 0) & df_valido["quartos"].notna()].copy()
    df_cpm2["preco_m2"] = df_cpm2["preco"] / df_cpm2["tamanho_m2"]
    df_cpm2["quartos"] = df_cpm2["quartos"].astype(int)
    ranking = df_cpm2.groupby("quartos")["preco_m2"].mean().reset_index()
    ranking.columns = ["Quartos", "R$/m²"]
    ranking = ranking.sort_values("R$/m²")
    fig5 = px.bar(
        ranking, x="Quartos", y="R$/m²",
        text=ranking["R$/m²"].apply(lambda x: f"R$ {x:.0f}/m²"),
        color="R$/m²", color_continuous_scale="RdYlGn_r",
        labels={"Quartos": "Nº de Quartos"},
    )
    fig5.update_traces(textposition="outside")
    fig5.update_layout(coloraxis_showscale=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig5, use_container_width=True)

with col6:
    st.markdown("#### Vagas de Garagem × Aluguel")
    st.caption("Imóveis com mais vagas cobram mais?")
    df_vagas = df_valido[df_valido["vagas"].notna()].copy()
    df_vagas["vagas"] = df_vagas["vagas"].astype(int)
    media_v = df_vagas.groupby("vagas").agg(
        preco_medio=("preco", "mean"),
        quantidade=("preco", "count")
    ).reset_index()
    fig6 = px.bar(
        media_v, x="vagas", y="preco_medio",
        text=media_v["preco_medio"].apply(lambda x: f"R$ {x:,.0f}"),
        labels={"vagas": "Vagas de Garagem", "preco_medio": "Aluguel Médio (R$)"},
        color="preco_medio", color_continuous_scale="Purples",
    )
    fig6.update_traces(textposition="outside")
    fig6.update_layout(coloraxis_showscale=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig6, use_container_width=True)

# ── Tabela ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("#### Todos os Imóveis")

df_tabela = df[["endereco", "preco", "tamanho_m2", "quartos", "vagas", "operacao", "data_coleta"]].copy()
df_tabela.columns = ["Endereço", "Aluguel (R$)", "Tamanho (m²)", "Quartos", "Vagas", "Operação", "Data Coleta"]
df_tabela["Aluguel (R$)"] = df_tabela["Aluguel (R$)"].apply(lambda x: f"R$ {x:,.0f}" if pd.notna(x) else "—")

st.dataframe(df_tabela, use_container_width=True, hide_index=True)
