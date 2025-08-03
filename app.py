import streamlit as st
import json
from pipeline import plot_wordcloud_streamlit, heatmap_dataframe
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import io
import base64
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.spatial.distance import pdist

st.set_page_config(layout="wide")
st.markdown("""<style>
    div.block-container {padding-top: 1rem;}
    .stApp {background-color: #1F2A35; color: #ecf0f1;}
    section.main > div {padding-top: 0rem;}
</style>""", unsafe_allow_html=True)

if "current_tab" not in st.session_state:
    st.session_state.current_tab = "competitor"

st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        min-width: 160px !important;
        max-width: 160px !important;
        background-color: #ecf0f1;
        padding-top: 30vh !important;
    }
    .sidebar-buttons button {
        width: 120px !important;
        height: 40px !important;
        margin: 8px auto !important;
        display: block;
        font-size: 14px !important;
        color: #1F2A35 !important;
    }
    .stSelectbox label {
        color: #1F2A35 !important;
    }
    .stSelectbox div[role="combobox"] {
        color: #1F2A35 !important;
    }
    .stMultiSelect > label {
        color: #1F2A35 !important;
    }
    .stMultiSelect div[role="combobox"] {
        color: #3498db !important;
    }
    .stSelectbox div[data-baseweb="select"] > div {
        text-transform: uppercase;
    }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.image("img/logo.png", width=140)
    st.markdown("<div class='sidebar-buttons'>", unsafe_allow_html=True)
    if st.button("Competitor", key="competitor"):
        st.session_state.current_tab = "competitor"
    if st.button("On View", key="on"):
        st.session_state.current_tab = "on"
    st.markdown("</div>", unsafe_allow_html=True)

def load_json_file(filename):
    with open(f"{filename}.json", "r", encoding="utf-8") as f:
        return json.load(f)

avg_table = load_json_file("avg_table")
brands = set()
tables = {}

def add_to_table(label, sub_dict):
    for subcat, brand_scores in sub_dict.items():
        for brand, score in brand_scores.items():
            brands.add(brand)
            col = subcat if isinstance(subcat, str) else str(subcat)
            if brand not in tables:
                tables[brand] = {}
            tables[brand][label if label in ['masc', 'fem'] else col] = score

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

if st.session_state.current_tab == "competitor":
    st.markdown("<h1 style='text-align: center;'>Competitor Analysis</h1>", unsafe_allow_html=True)
    with st.container():
        available_brands = df.index.tolist()
        selected_brands = st.multiselect("Filter brands", available_brands, default=available_brands)
        filtered_df = df.loc[selected_brands]
        styled_df = filtered_df.style.format("{:.2f}").set_properties(**{"text-align": "center", "min-width": "100px", "max-width": "200px"})
        st.dataframe(styled_df, height=len(filtered_df) * 35 + 35, use_container_width=True)

    col1, col2 = st.columns([1,1])

    with col1:
        df_heatmap = heatmap_dataframe(avg_table)
        selected_category = st.selectbox("Select category", df_heatmap["Categoria"].unique(), label_visibility="collapsed")
        pivot = df_heatmap[df_heatmap["Categoria"] == selected_category].pivot(index="Subcategoria", columns="Marca", values="Nota Média")
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.heatmap(pivot, annot=True, fmt=".1f", cmap="YlGnBu", ax=ax, annot_kws={"size": 12})
        ax.tick_params(axis='x', labelsize=10)
        ax.tick_params(axis='y', labelsize=9)
        ax.grid(False)
        st.pyplot(fig)

    with col2:
        index_on = available_brands.index("On") if "On" in available_brands else 0
        brand_a = st.selectbox("Brand A", available_brands, index=index_on)
        brand_b = st.selectbox("Brand B", [m for m in available_brands if m != brand_a], index=1)
        compare_cols = [col for col in df.columns if col not in ["Avg Score"]]
        df_compare = pd.DataFrame({"Category": compare_cols, brand_a: df.loc[brand_a, compare_cols], brand_b: df.loc[brand_b, compare_cols]})
        df_compare = df_compare.melt(id_vars="Category", var_name="Brand", value_name="Score")
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.barplot(data=df_compare, x="Category", y="Score", hue="Brand", ax=ax)
        ax.set_title(f"Comparison between {brand_a} and {brand_b}", fontsize=14)
        ax.set_ylabel("Avg Score")
        ax.set_xlabel("")
        ax.tick_params(axis='x', rotation=45)
        ax.grid(False)
        st.pyplot(fig)

elif st.session_state.current_tab == "on":
    st.markdown("<h1 style='text-align: center;'>On Running Analysis</h1>", unsafe_allow_html=True)

    col1, col_spacer, col2 = st.columns([1, 0.35, 1])

    with col1:
        data = load_json_file("data")
        model_scores = {}
        if "On" in data:
            seen = set()
            for gender in ['M', 'F']:
                for shoe in data["On"].get(gender, []):
                    name = shoe.get("Name")
                    try:
                        score = float(shoe.get("Score"))
                    except:
                        continue
                    if name and name not in seen:
                        seen.add(name)
                        model_scores[name] = score

        if model_scores:
            sorted_models = sorted(model_scores.keys())
            selected_model = st.selectbox("Model", sorted_models, index=0)
            selected_score = model_scores[selected_model]
            on_avg = df.loc["On"]["Avg Score"] if "On" in df.index else None
            if on_avg is not None:
                if selected_score > on_avg:
                    color = "#2ecc71"
                    arrow = "⬆️"
                elif selected_score < on_avg - on_avg / 10:
                    color = "#e74c3c"
                    arrow = "⬇️"
                else:
                    color = "#f1c40f"
                    arrow = "➡️"
            else:
                color = "#3498db"
                arrow = ""

            fig, ax = plt.subplots(figsize=(2, 2), dpi=150)
            ax.pie([selected_score, 100 - selected_score], startangle=90, colors=[color, "#f0f2f6"], wedgeprops={"width": 0.15, "edgecolor": "white"})
            ax.text(0, 0, f"{selected_score:.1f}{arrow}", ha='center', va='center', fontsize=16, fontweight="bold", color=color)
            ax.axis("equal")
            buf = io.BytesIO()
            plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
            buf.seek(0)
            plt.close(fig)
            encoded = base64.b64encode(buf.getvalue()).decode()
            st.markdown(f"<div style='text-align: center;'><img src='data:image/png;base64,{encoded}'></div>", unsafe_allow_html=True)
            if on_avg is not None:
                st.markdown(f"<p style='text-align: center; font-size: 1rem;'>On Avg: {on_avg:.1f}</p>", unsafe_allow_html=True)

    with col_spacer:
        st.markdown("<h1 style='text-align: center;'></h1>", unsafe_allow_html=True)

    with col2:
        model_evolution = load_json_file("model_score_evolution")
        if model_evolution:
            evolution_data = []
            for base_model, versions in model_evolution.items():
                for model_name, score in versions:
                    clean_version = model_name.replace("On", "").strip()
                    evolution_data.append({"Base Model": base_model.title(), "Version": clean_version, "Score": score})
            df_evolution = pd.DataFrame(evolution_data)
            df_evolution["VersionNum"] = df_evolution.groupby("Base Model").cumcount() + 1
            df_evolution["VersionLabel"] = "V" + df_evolution["VersionNum"].astype(str)
            base_models = sorted(df_evolution["Base Model"].unique())
            selected_base = st.selectbox("Model", base_models, index=0)
            df_filtered = df_evolution[df_evolution["Base Model"] == selected_base]
            fig, ax = plt.subplots(figsize=(2.8, 2.2))
            sns.barplot(data=df_filtered, x="VersionLabel", y="Score", ax=ax, palette="Blues_d")
            ax.set_ylim(bottom=max(df_filtered["Score"].min() - 5, 0))
            ax.set_title("", fontsize=10)
            ax.set_ylabel("")
            ax.set_xlabel("")
            ax.tick_params(axis='x', labelsize=8)
            ax.tick_params(axis='y', labelsize=8)
            ax.grid(False)
            st.pyplot(fig)

    col3, col4 = st.columns([1, 1])

    with col3:
        selected_pros = []
        selected_cons = []

        for gender in ["M", "F"]:
            for shoe in data["On"].get(gender, []):
                if shoe.get("Name") == selected_model:
                    selected_pros = shoe.get("Pros", [])
                    selected_cons = shoe.get("Cons", [])
                    break

        st.markdown(f"### Comments for – **{selected_model}**", unsafe_allow_html=True)
        col_pros, col_cons = st.columns(2)

        with col_pros:
            st.markdown("### Pros")
            for item in selected_pros:
                st.markdown(f"- {item}")

        with col_cons:
            st.markdown("### Cons")
            for item in selected_cons:
                st.markdown(f"- {item}")

    with col4:
        scores_by_year = []

        for gender in ['M', 'F']:
            for shoe in data["On"].get(gender, []):
                raw_year = shoe.get("ReleaseYear", [""])[0]
                raw_score = shoe.get("Score")

                try:
                    year = 2021 if raw_year == "2021 or older" else int(raw_year)
                    score = float(raw_score)
                    scores_by_year.append({"Year": year, "Score": score})
                except:
                    continue

        df_years = pd.DataFrame(scores_by_year)

        if not df_years.empty:
            avg_by_year = (
                df_years.groupby("Year")["Score"]
                .mean()
                .round(2)
                .reset_index()
                .sort_values("Year")
            )

            fig, ax = plt.subplots(figsize=(4, 2.5))
            sns.lineplot(data=avg_by_year, x="Year", y="Score", marker="o", ax=ax)
            ax.set_title("Average Score by Release Year", fontsize=10)
            ax.set_ylabel("Avg Score")
            ax.set_xlabel("")
            ax.set_xticks(avg_by_year["Year"])
            ax.tick_params(labelsize=9)
            ax.grid(False)
            st.pyplot(fig)
        else:
            st.info("No release year data available.")