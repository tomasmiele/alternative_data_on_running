import streamlit as st
import json
from pipeline import plot_wordcloud_streamlit, heatmap_dataframe
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def load_json_file(filename):
    with open(f"{filename}.json", "r") as f:
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

for model in top_models_data["models"]:
    st.markdown(f"- **{model['Name']}** – *{model.get('Adjective', 'N/A')}*")
    st.markdown(f"  - Score: {model['Score']}")
    if pros := model.get("Pros"):
        st.markdown("  - Pros: " + ", ".join(pros))
    if cons := model.get("Cons"):
        st.markdown("  - Cons: " + ", ".join(cons))
    st.markdown("---")

