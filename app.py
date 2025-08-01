import streamlit as st
import json
from pipeline import plot_wordcloud_streamlit, heatmap_dataframe
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import io
import base64

def load_json_file(filename):
    with open(f"{filename}.json", "r", encoding="utf-8") as f:
        return json.load(f)

st.set_page_config(layout="wide")
st.markdown("<style>div.block-container {padding-top: 1rem;}</style>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center;'>Análise de Alternativa <em>On Running</em></h1>", unsafe_allow_html=True)
st.markdown("""<style>.stApp {background-color: #fcfcfc;}</style>""", unsafe_allow_html=True)

avg_table = load_json_file("avg_table")
brands = set()
tables = {}

def add_to_table(category_label, sub_dict):
    for subcat, brand_scores in sub_dict.items():
        for brand, score in brand_scores.items():
            brands.add(brand)
            col = subcat if isinstance(subcat, str) else str(subcat)
            if brand not in tables:
                tables[brand] = {}
            tables[brand][category_label if category_label in ['masc', 'fem'] else col] = score

for brand, score in avg_table.get("brand", {}).items():
    brands.add(brand)
    if brand not in tables:
        tables[brand] = {}
    tables[brand]["Avg Score"] = score

add_to_table("terrain", avg_table.get("terrain", {}))
add_to_table("pace", avg_table.get("pace", {}))
add_to_table("year", avg_table.get("year", {}))

df = pd.DataFrame.from_dict(tables, orient="index")
df.index.name = "Brand"
df = df.sort_index(axis=0).sort_index(axis=1)
df = df.round(2)

col1, col2, col3 = st.columns(3)

with col1:
    st.dataframe(df)

with col2:
    top_models_data = load_json_file("top_on_models")
    top_score = top_models_data["top_score"]
    top_models = top_models_data["models"]

    on_avg_score = df.loc["On"]["Avg Score"] if "On" in df.index else None

    if top_score > 85:
        color = "#2ecc71"
    elif top_score >= 50:
        color = "#f1c40f"
    else:
        color = "#e74c3c"

    arrow = ""
    if on_avg_score is not None:
        arrow = "⬆️" if top_score > on_avg_score else "⬇️"

    st.markdown(
        "<h5 style='text-align: center;'>Melhor Tênis da On</h5>",
        unsafe_allow_html=True
    )

    fig, ax = plt.subplots(figsize=(1.5, 1.5), dpi=150)
    ax.pie(
        [top_score, 100 - top_score],
        startangle=90,
        colors=[color, "#f0f2f6"],
        wedgeprops={"width": 0.12, "edgecolor": "white"}
    )
    ax.text(0, 0, f"{top_score:.1f}{arrow}", ha='center', va='center', fontsize=12, fontweight="bold", color=color)
    ax.axis("equal")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
    buf.seek(0)
    plt.close(fig)

    encoded = base64.b64encode(buf.getvalue()).decode()
    img_html = f"<div style='text-align: center;'><img src='data:image/png;base64,{encoded}'></div>"

    st.markdown(img_html, unsafe_allow_html=True)

    if on_avg_score is not None:
        st.markdown(
            f"<p style='text-align: center; font-size: 0.85rem;'>"
            f"Comparado à média da On ({on_avg_score:.1f})</p>",
            unsafe_allow_html=True
        )

    st.markdown(
        f"<p style='text-align: center; font-size: 0.9rem;'>"
        f"{' | '.join(f'<b>{model}</b>' for model in top_models)}"
        f"</p>",
        unsafe_allow_html=True
    )

    st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)

with col3:
    df_heatmap = heatmap_dataframe(avg_table)
    selected_category = st.selectbox("Selecione a categoria", df_heatmap["Categoria"].unique(), label_visibility="collapsed")

    pivot = df_heatmap[df_heatmap["Categoria"] == selected_category].pivot(
        index="Subcategoria", columns="Marca", values="Nota Média"
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(pivot, annot=True, fmt=".1f", cmap="YlGnBu", ax=ax, annot_kws={"size": 18})
    ax.tick_params(axis='x', labelsize=18)
    ax.tick_params(axis='y', labelsize=12)
    st.pyplot(fig)

col4, col5, col6 = st.columns(3)

with col4:
    st.markdown("<h5 style='text-align: left;'>Comentários Negativos Mais Frequentes</h5>", unsafe_allow_html=True)

    word_scores = load_json_file("worst_on_comments")
    sorted_words = sorted(word_scores.items(), key=lambda x: x[1])

    df_words = pd.DataFrame(sorted_words, columns=["Comentários", "Nota Média"])
    df_words["Nota Média"] = df_words["Nota Média"].round(1)
    df_words.reset_index(drop=True, inplace=True)

    st.dataframe(df_words, use_container_width=True, hide_index=True)

with col5:
    model_evolution = load_json_file("model_score_evolution")

    if not model_evolution:
        st.info("Nenhum modelo com múltiplas versões foi encontrado.")
    else:
        evolution_data = []
        for base_model, versions in model_evolution.items():
            for model_name, score in versions:
                clean_version = model_name.replace("On", "").strip()
                evolution_data.append({
                    "Base Model": base_model.title(),
                    "Version": clean_version,
                    "Score": score
                })

        df_evolution = pd.DataFrame(evolution_data)
        df_evolution["VersaoNum"] = df_evolution.groupby("Base Model").cumcount() + 1
        df_evolution["VersaoLabel"] = "Versão " + df_evolution["VersaoNum"].astype(str)

        unique_versions = df_evolution["VersaoLabel"].unique()
        palette = sns.color_palette("tab10", n_colors=len(unique_versions))
        palette_colors = dict(zip(unique_versions, palette))

        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(
            data=df_evolution,
            x="Base Model",
            y="Score",
            hue="VersaoLabel",
            dodge=True,
            ax=ax,
            palette=palette_colors
        )

        min_score = df_evolution["Score"].min()
        ax.set_ylim(bottom=max(min_score - 5, 0))

        ax.set_title("Desempenho dos modelos conforme suas novas versões", fontsize=18)
        ax.set_ylabel("Score")
        ax.set_xlabel("Modelo Base")
        ax.grid(True, axis='y', linestyle="--", alpha=0.3)
        plt.xticks(rotation=45, ha="right")
        ax.get_legend().set_title("")

        st.pyplot(fig)

with col6:
    dict_pros = load_json_file("positive_words")
    plot_wordcloud_streamlit(dict_pros, "Principais Termos Positivos nas Avaliações")