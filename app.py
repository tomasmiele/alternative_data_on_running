import streamlit as st
import json
from pipeline import plot_wordcloud_streamlit, heatmap_dataframe
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import io
import base64

st.set_page_config(layout="wide")
st.markdown("""<style>
    div.block-container {padding-top: 1rem;}
    .stApp {background-color: #fcfcfc;}
    section.main > div {padding-top: 0rem;}
</style>""", unsafe_allow_html=True)

if "aba_atual" not in st.session_state:
    st.session_state.aba_atual = "concorrencial"

st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        min-width: 160px !important;
        max-width: 160px !important;
        background-color: #f2f2f2;
        padding-top: 30vh !important;
    }
    .sidebar-buttons button {
        width: 120px !important;
        height: 40px !important;
        margin: 8px auto !important;
        display: block;
        font-size: 14px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

with st.sidebar:
    st.markdown("<div class='sidebar-buttons'>", unsafe_allow_html=True)
    if st.button("Concorrência", key="concorrencia"):
        st.session_state.aba_atual = "concorrencial"
    if st.button("Visão On", key="on"):
        st.session_state.aba_atual = "on"
    st.markdown("</div>", unsafe_allow_html=True)

def load_json_file(filename):
    with open(f"{filename}.json", "r", encoding="utf-8") as f:
        return json.load(f)

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

if st.session_state.aba_atual == "concorrencial":
    st.markdown("<h1 style='text-align: center;'>Análise Concorrencial</h1>", unsafe_allow_html=True)

    with st.container():
        _, col_table, _ = st.columns([1, 2.5, 1])
        with col_table:
            st.dataframe(df, height=400)

    df_heatmap = heatmap_dataframe(avg_table)
    selected_category = st.selectbox("Selecione a categoria", df_heatmap["Categoria"].unique(), label_visibility="collapsed")

    pivot = df_heatmap[df_heatmap["Categoria"] == selected_category].pivot(
        index="Subcategoria", columns="Marca", values="Nota Média"
    )

    fig, ax = plt.subplots(figsize=(8, 4))
    sns.heatmap(pivot, annot=True, fmt=".1f", cmap="YlGnBu", ax=ax, annot_kws={"size": 12})
    ax.tick_params(axis='x', labelsize=10)
    ax.tick_params(axis='y', labelsize=9)
    st.pyplot(fig)


elif st.session_state.aba_atual == "on":
    st.markdown("<h1 style='text-align: center;'>Análise On Running</h1>", unsafe_allow_html=True)

    col1, col_v1, col_v2, col2 = st.columns([1, 0.35, 0.35, 1])

    with col1:
        data = load_json_file("data")
        model_scores = {}

        if "On" in data:
            seen_models = set()
            for gender in ['M', 'F']:
                for shoe in data["On"].get(gender, []):
                    name = shoe.get("Name")
                    try:
                        score = float(shoe.get("Score"))
                    except (ValueError, TypeError):
                        continue
                    if name and name not in seen_models:
                        seen_models.add(name)
                        model_scores[name] = score

        if model_scores:
            sorted_models = sorted(model_scores.keys())
            selected_model = st.selectbox("Modelo", sorted_models, index=0)
            selected_score = model_scores[selected_model]

            on_avg_score = df.loc["On"]["Avg Score"] if "On" in df.index else None
            if on_avg_score is not None:
                if selected_score > on_avg_score:
                    color = "#2ecc71"
                    arrow = "⬆️"
                elif selected_score < on_avg_score - on_avg_score / 10:
                    color = "#e74c3c"
                    arrow = "⬇️"
                else:
                    color = "#f1c40f"
                    arrow = "➡️"
            else:
                color = "#3498db"
                arrow = ""

            fig, ax = plt.subplots(figsize=(2, 2), dpi=150)
            ax.pie(
                [selected_score, 100 - selected_score],
                startangle=90,
                colors=[color, "#f0f2f6"],
                wedgeprops={"width": 0.15, "edgecolor": "white"}
            )
            ax.text(0, 0, f"{selected_score:.1f}{arrow}", ha='center', va='center', fontsize=16, fontweight="bold", color=color)
            ax.axis("equal")

            buf = io.BytesIO()
            plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
            buf.seek(0)
            plt.close(fig)
            encoded = base64.b64encode(buf.getvalue()).decode()
            img_html = f"<div style='text-align: center;'><img src='data:image/png;base64,{encoded}'></div>"
            st.markdown(img_html, unsafe_allow_html=True)

            if on_avg_score is not None:
                st.markdown(f"<p style='text-align: center; font-size: 1rem;'>Média da On: {on_avg_score:.1f}</p>", unsafe_allow_html=True)

    with col_v1:
        st.markdown("<h1 style='text-align: center;'></h1>", unsafe_allow_html=True)

    with col_v2:
        st.markdown("<h1 style='text-align: center;'></h1>", unsafe_allow_html=True)

    with col2:
        model_evolution = load_json_file("model_score_evolution")
        if model_evolution:
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
            df_evolution["VersaoLabel"] = "V" + df_evolution["VersaoNum"].astype(str)

            base_models = sorted(df_evolution["Base Model"].unique())
            selected_base_model = st.selectbox("Modelo", base_models, index=0)

            df_filtered = df_evolution[df_evolution["Base Model"] == selected_base_model]
            fig, ax = plt.subplots(figsize=(2.8, 2.2))
            sns.barplot(data=df_filtered, x="VersaoLabel", y="Score", ax=ax, palette="Blues_d")
            ax.set_ylim(bottom=max(df_filtered["Score"].min() - 5, 0))
            ax.set_title("", fontsize=10)
            ax.set_ylabel("")
            ax.set_xlabel("")
            ax.tick_params(axis='x', labelsize=8)
            ax.tick_params(axis='y', labelsize=8)
            ax.grid(True, axis='y', linestyle="--", alpha=0.3)
            st.pyplot(fig)

    col3, col4 = st.columns([1, 1])

    with col3:
        word_scores = load_json_file("worst_on_comments")
        sorted_words = sorted(word_scores.items(), key=lambda x: x[1])
        df_words = pd.DataFrame(sorted_words, columns=["Comentário", "Nota"])
        df_words["Nota"] = df_words["Nota"].round(1)
        st.dataframe(df_words, use_container_width=True, hide_index=True, height=200)

    with col4:
        dict_pros = load_json_file("positive_words")
        st.markdown("<div style='font-size: 10px;'>", unsafe_allow_html=True)
        plot_wordcloud_streamlit(dict_pros, "")