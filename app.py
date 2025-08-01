import streamlit as st
import json
from pipeline import plot_wordcloud_streamlit, heatmap_dataframe
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def load_json_file(filename):
    with open(f"{filename}.json", "r", encoding="utf-8") as f:
        return json.load(f)

st.title("Análisede Alternativa *On Running*")

# Tabela com as médias por marca e com diferentes aspectos

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

if "masc" in avg_table:
    for brand, score in avg_table["masc"].items():
        brands.add(brand)
        if brand not in tables:
            tables[brand] = {}
        tables[brand]["masc"] = score

if "fem" in avg_table:
    for brand, score in avg_table["fem"].items():
        brands.add(brand)
        if brand not in tables:
            tables[brand] = {}
        tables[brand]["fem"] = score

df = pd.DataFrame.from_dict(tables, orient="index").sort_index()
df.index.name = "Brand"
df = df.sort_index(axis=1) 
st.title("Média de Notas por Marca e Categoria")
st.dataframe(df)

# Palavras mais utilizadas para descrever os tenis da On em aspectos positivos e negativos
st.title("WordCloud – Shoe Review Analysis")

dict_pros, dict_cons = load_json_file("positive_words"), load_json_file("negative_words")

st.subheader("Words Indicating Positivity")
plot_wordcloud_streamlit(dict_pros, "Positivity")

st.subheader("Words Indicating Negativity")
plot_wordcloud_streamlit(dict_cons, "Negativity")

# Mapa de calor para verificar oportunidades para a On Running
st.header("Consistência de Avaliação por Categoria")

df_heatmap = heatmap_dataframe(avg_table)

selected_category = st.selectbox("Selecione uma categoria", df_heatmap["Categoria"].unique())

pivot = df_heatmap[df_heatmap["Categoria"] == selected_category].pivot(
    index="Subcategoria", columns="Marca", values="Nota Média"
)

st.write(f"### Heatmap: {selected_category}")
fig, ax = plt.subplots(figsize=(10, 6))
sns.heatmap(pivot, annot=True, fmt=".1f", cmap="YlGnBu", ax=ax)
st.pyplot(fig)

# Marcador de performance comparado a média das outras empresas
st.header("On's Performance Marker by Category")

performance = load_json_file("on_performance")

status_icons = {
    "above": "🟩",
    "average": "🟨",
    "below": "🟥"
}

for category, subcats in performance.items():
    valid_items = {
        subcat: info for subcat, info in subcats.items()
        if "status" in info and "on_score" in info and "others_avg" in info
    }

    if not valid_items:
        continue

    st.subheader(f"{category.title()}")
    for subcat, info in valid_items.items():
        icon = status_icons.get(info["status"], "⬜️")
        st.markdown(
            f"{icon} **{subcat}** – On: {info['on_score']} | Others' Average: {info['others_avg']} → *{info['status'].capitalize()}*"
        )


# Melhor(es) tênis da On
st.header("Best Rated On Running Shoes")

top_models_data = load_json_file("top_on_models")

st.markdown(f"**Top Score:** {top_models_data['top_score']}")

st.markdown("**Top Models:**")
for model_name in top_models_data["models"]:
    st.markdown(f"- **{model_name}**")

# Comentários mais negativos
st.header("Comentários Negativos Mais Frequentes (On)")

worst_comments = load_json_file("worst_on_comments")

st.markdown("**Comentários mais citados nos reviews negativos:**")
for comment in worst_comments:
    st.markdown(f"- {comment}")

# Gráfico de desempenho da evolução do modelo
st.header("Evolução da nota dos modelos da On")

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

    available_models = sorted(df_evolution["Base Model"].unique())
    selected_models = st.multiselect(
        "Selecione os modelos base para visualizar:",
        available_models,
        default=available_models
    )

    if selected_models:
        filtered_df = df_evolution[df_evolution["Base Model"].isin(selected_models)]

        fig, ax = plt.subplots(figsize=(20, 8))
        sns.barplot(
            data=filtered_df,
            x="Base Model",
            y="Score",
            hue="Version",
            dodge=True,
            ax=ax
        )

        ax.set_title("Notas das Versões por Modelo Base – On", fontsize=16)
        ax.set_ylabel("Score")
        ax.set_xlabel("Modelo Base")
        ax.grid(True, axis='y', linestyle="--", alpha=0.3)
        plt.xticks(rotation=45, ha="right")

        ax.get_legend().remove()

        st.pyplot(fig)
    else:
        st.info("Selecione pelo menos um modelo base para visualizar o gráfico.")