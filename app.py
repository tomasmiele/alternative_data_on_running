import streamlit as st
import json
from pipeline import plot_wordcloud_streamlit
import pandas as pd

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