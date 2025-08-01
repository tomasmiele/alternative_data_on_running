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

st.header("🎯 On's Performance Marker by Category")

performance = load_json_file("on_performance")

status_icons = {
    "above": "🟩",
    "average": "🟨",
    "below": "🟥"
}

for category, subcats in performance.items():
    st.subheader(f"{category.title()}")
    for subcat, info in subcats.items():
        icon = status_icons[info["status"]]
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
worst_on_comments = load_json_file("worst_on_comments.json")

st.header("Comentários mais Negativos (On)")

st.markdown(f"**Menor nota encontrada:** {worst_on_comments['lowest_score']}")
st.markdown("**Modelos com essa nota:**")
for model in worst_on_comments["models"]:
    st.markdown(f"- {model}")

st.markdown("**Principais comentários negativos:**")
for cons in worst_on_comments["comments"]:
    st.markdown(f"- {cons}")

# Gráfico de desempenho da evolução do modelo
st.header("Evolução da nota dos modelos da On")

model_evolution = load_json_file("model_score_evolution.json")

if not model_evolution:
    st.info("Nenhum modelo com múltiplas versões foi encontrado.")
else:
    selected_model = st.selectbox(
        "Escolha um modelo base para visualizar a evolução:",
        list(model_evolution.keys())
    )

    if selected_model:
        versions = model_evolution[selected_model]
        names = [v[0] for v in versions]
        scores = [v[1] for v in versions]

        df = pd.DataFrame({
            "Model": names,
            "Score": scores
        })

        # Plot com Matplotlib
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df["Model"], df["Score"], marker="o")
        ax.set_title(f"Evolução da nota – {selected_model.title()}")
        ax.set_ylabel("Score")
        ax.set_xlabel("Versão do modelo")
        ax.grid(True)

        st.pyplot(fig)

# Associação de lifestyle e emoções com a marca
st.header("Lifestyle & Emotional Mentions")

mentions = load_json_file("emotion_lifestyle_mentions")

st.subheader("Lifestyle Mentions")
for item in mentions["lifestyle"]:
    st.markdown(f"- **{item['model']}** → Palavras-chave: `{', '.join(item['matched_keywords'])}`")
    st.markdown(f"  - Pros: {', '.join(item['pros'])}")

st.subheader("Emotional Mentions")
for item in mentions["emotion"]:
    st.markdown(f"- **{item['model']}** → Palavras-chave: `{', '.join(item['matched_keywords'])}`")
    st.markdown(f"  - Pros: {', '.join(item['pros'])}")
