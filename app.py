import streamlit as st
import json
from pipeline import plot_wordcloud_streamlit, heatmap_dataframe
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def load_json_file(filename):
    with open(f"{filename}.json", "r", encoding="utf-8") as f:
        return json.load(f)

st.set_page_config(layout="wide")
st.markdown("<style>div.block-container {padding-top: 1rem;}</style>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center;'>Análise de Alternativa <em>On Running</em></h1>", unsafe_allow_html=True)

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
    st.subheader("Melhores Tênis da On")
    top_models_data = load_json_file("top_on_models")
    st.markdown(f"**Top Score:** {top_models_data['top_score']}")
    st.markdown("**Top Models:**")
    for model_name in top_models_data["models"]:
        st.markdown(f"- **{model_name}**")

with col3:
    st.subheader("Comentários Negativos Mais Frequentes da On")
    worst_comments = load_json_file("worst_on_comments")
    for comment in worst_comments:
        st.markdown(f"- {comment}")

col4, col5, col6 = st.columns(3)

with col4:
    dict_pros = load_json_file("positive_words")
    plot_wordcloud_streamlit(dict_pros, "Positivity")

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

        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(
            data=df_evolution,
            x="Base Model",
            y="Score",
            hue="Version",
            dodge=True,
            ax=ax
        )

        min_score = df_evolution["Score"].min()
        ax.set_ylim(bottom=max(min_score - 5, 0))

        ax.set_title("Notas das Versões por Modelo Base – On", fontsize=14)
        ax.set_ylabel("Score")
        ax.set_xlabel("Modelo Base")
        ax.grid(True, axis='y', linestyle="--", alpha=0.3)
        plt.xticks(rotation=45, ha="right")
        ax.get_legend().remove()

        st.pyplot(fig)

with col6:
    df_heatmap = heatmap_dataframe(avg_table)
    selected_category = st.selectbox("Selecione uma categoria", df_heatmap["Categoria"].unique())

    pivot = df_heatmap[df_heatmap["Categoria"] == selected_category].pivot(
        index="Subcategoria", columns="Marca", values="Nota Média"
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(pivot, annot=True, fmt=".1f", cmap="YlGnBu", ax=ax)
    st.pyplot(fig)