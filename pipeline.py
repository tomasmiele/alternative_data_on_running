import re
import math
from collections import Counter
from nltk.corpus import stopwords
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import streamlit as st
from collections import defaultdict
import pandas as pd

stopwords_set = set(stopwords.words("english"))

def dehyphenize(word):
    if re.fullmatch(r"(?:[a-zA-Z]-){1,}[a-zA-Z]", word):
        return word.replace("-", "")
    return word

def fix_hyphenated_sentence(sentence):
    words = sentence.lower().split()
    corrected_words = [dehyphenize(w) for w in words]
    return " ".join(corrected_words)

def extract_pros_cons(data):
    brands = ["On", "Hoka", "Nike", "Adidas", "New Balance"]
    pros = {}
    cons = {}

    for brand in brands:
        pros[brand] = []
        cons[brand] = []
        for gender in ['M', 'F']:
            for shoe in data[brand][gender]:
                raw_pros = shoe.get("Pros", [])
                raw_cons = shoe.get("Cons", [])

                processed_pros = [fix_hyphenated_sentence(p) for p in raw_pros]
                processed_cons = [fix_hyphenated_sentence(c) for c in raw_cons]

                pros[brand].extend(processed_pros)
                cons[brand].extend(processed_cons)

    return pros, cons

def clean_word(word):
    cleaned = re.sub(r"[^\w]", "", word)
    if cleaned.isdigit():
        return ""
    if not re.search(r"[a-zA-Z]", cleaned):
        return ""
    return cleaned

def compute_log_frequency(word_count_tuples):
    total = sum(count for _, count in word_count_tuples)
    log_freq = {
        word: math.log10(count / total)
        for word, count in word_count_tuples
    }
    return log_freq

def get_classification(pros_dict, cons_dict):
    pros = {"total": set()}
    cons = {"total": set()}

    for brand, sentences in pros_dict.items():
        cleaned_words = {
            clean_word(w) for w in " ".join(sentences).lower().split()
            if clean_word(w) not in stopwords_set and clean_word(w) != ""
        }
        pros[brand] = cleaned_words
        pros["total"].update(cleaned_words)

    for brand, sentences in cons_dict.items():
        cleaned_words = {
            clean_word(w) for w in " ".join(sentences).lower().split()
            if clean_word(w) not in stopwords_set and clean_word(w) != ""
        }
        cons[brand] = cleaned_words
        cons["total"].update(cleaned_words)

    print("\n[+] Pros Word Count and Log Frequency")
    pros_counter = Counter(pros["total"])
    pros_tuples = list(pros_counter.items())
    print(pros_tuples)
    compute_log_frequency(pros_tuples)

    print("\n[-] Cons Word Count and Log Frequency")
    cons_counter = Counter(cons["total"])
    cons_tuples = list(cons_counter.items())
    print(cons_tuples)
    compute_log_frequency(cons_tuples)

    print(f"\nTotal unique words in pros: {len(pros_tuples)}")
    print(f"Total unique words in cons: {len(cons_tuples)}")

    pros = {k: list(v) for k, v in pros.items()}
    cons = {k: list(v) for k, v in cons.items()}

    return pros, cons

def generate_difference_dictionaries(pros, cons, top_n=100):
    pros_counter = Counter(pros["total"])
    cons_counter = Counter(cons["total"])

    all_words = set(pros_counter.keys()) | set(cons_counter.keys())

    differences = [
        (word, pros_counter.get(word, 0) - cons_counter.get(word, 0))
        for word in all_words
    ]

    most_negative = sorted(differences, key=lambda x: x[1])[:top_n]
    most_positive = sorted(differences, key=lambda x: -x[1])[:top_n]

    negative_dict = {word: abs(value) for word, value in most_negative if value < 0}
    positive_dict = {word: abs(value) for word, value in most_positive if value > 0}

    return positive_dict, negative_dict

def plot_wordcloud_streamlit(word_freq_dict, title, font_path=None):
    wc = WordCloud(
        width=1000, height=500,
        background_color="white",
        font_path=font_path
    ).generate_from_frequencies(word_freq_dict)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_title(title)
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    st.pyplot(fig)

def compute_score_aggregates_with_gender(data):
    def nested_dict(): 
        return defaultdict(list)

    brand_scores = defaultdict(list)
    terrain_scores = defaultdict(nested_dict)
    pace_scores = defaultdict(nested_dict)
    year_scores = defaultdict(nested_dict)

    masc_scores = defaultdict(list)
    fem_scores = defaultdict(list)

    for brand, genders in data.items():
        for gender, shoes in genders.items():
            for shoe in shoes:
                try:
                    score = float(shoe["Score"])
                except (ValueError, TypeError):
                    continue

                brand_scores[brand].append(score)

                if gender == "M":
                    masc_scores[brand].append(score)
                elif gender == "F":
                    fem_scores[brand].append(score)

                for terrain in shoe.get("Terrain", []):
                    terrain_scores[terrain][brand].append(score)

                for pace in shoe.get("Pace", []):
                    pace_scores[pace][brand].append(score)

                year = shoe.get("Release Year")
                if year:
                    year_scores[str(year)][brand].append(score)

    def avg(lst):
        return round(sum(lst) / len(lst), 2) if lst else None

    def process_nested(d):
        return {
            key: {
                subkey: avg(scores)
                for subkey, scores in subdict.items()
            } for key, subdict in d.items()
        }

    return {
        "brand": {brand: avg(scores) for brand, scores in brand_scores.items()},
        "terrain": process_nested(terrain_scores),
        "pace": process_nested(pace_scores),
        "year": process_nested(year_scores),
        "masc": {brand: avg(scores) for brand, scores in masc_scores.items()},
        "fem": {brand: avg(scores) for brand, scores in fem_scores.items()}
    }

def compare_to_others(data, brand="On"):
    result = defaultdict(lambda: defaultdict(list))

    def format_msg(category, subkey, brand_score, other_brand, other_score):
        return f"A {brand} está com uma avaliação baixa em {category} ({subkey}) ({brand_score}) enquanto a {other_brand} apresenta bom desempenho ({other_score})"

    def check_and_add(category_name, subkey, brand_score, other_brand, other_score):
        if brand_score < other_score:
            msg = format_msg(category_name, subkey, brand_score, other_brand, other_score)
            result[other_brand][category_name].append(msg)

    for terrain, brands in data.get("terrain", {}).items():
        if brand not in brands:
            continue
        for other_brand, other_score in brands.items():
            if other_brand == brand:
                continue
            check_and_add("terrain", terrain, brands[brand], other_brand, other_score)

    for pace, brands in data.get("pace", {}).items():
        if brand not in brands:
            continue
        for other_brand, other_score in brands.items():
            if other_brand == brand:
                continue
            check_and_add("pace", pace, brands[brand], other_brand, other_score)

    for year, brands in data.get("year", {}).items():
        if brand not in brands:
            continue
        for other_brand, other_score in brands.items():
            if other_brand == brand:
                continue
            check_and_add("year", year, brands[brand], other_brand, other_score)

    if "masc" in data and brand in data["masc"]:
        for other_brand, other_score in data["masc"].items():
            if other_brand == brand:
                continue
            check_and_add("gender", "masculino", data["masc"][brand], other_brand, other_score)

    if "fem" in data and brand in data["fem"]:
        for other_brand, other_score in data["fem"].items():
            if other_brand == brand:
                continue
            check_and_add("gender", "feminino", data["fem"][brand], other_brand, other_score)

    return {k: dict(v) for k, v in result.items()}

def compare_others_below(data, brand="On"):
    result = defaultdict(lambda: defaultdict(list))

    def format_msg(other_brand, category, subkey, diff):
        return f"{other_brand} está {diff:.1f} pontos abaixo da {brand} na categoria {subkey} ({category})"

    def check_and_add(category_name, subkey, brand_score, other_brand, other_score):
        if other_score < brand_score:
            diff = brand_score - other_score
            msg = format_msg(other_brand, category_name, subkey, diff)
            result[other_brand][category_name].append(msg)

    for terrain, brands in data.get("terrain", {}).items():
        if brand not in brands:
            continue
        for other_brand, other_score in brands.items():
            if other_brand == brand:
                continue
            check_and_add("terrain", terrain, brands[brand], other_brand, other_score)

    for pace, brands in data.get("pace", {}).items():
        if brand not in brands:
            continue
        for other_brand, other_score in brands.items():
            if other_brand == brand:
                continue
            check_and_add("pace", pace, brands[brand], other_brand, other_score)

    for year, brands in data.get("year", {}).items():
        if brand not in brands:
            continue
        for other_brand, other_score in brands.items():
            if other_brand == brand:
                continue
            check_and_add("year", year, brands[brand], other_brand, other_score)

    if "masc" in data and brand in data["masc"]:
        for other_brand, other_score in data["masc"].items():
            if other_brand == brand:
                continue
            check_and_add("gender", "masculino", data["masc"][brand], other_brand, other_score)

    if "fem" in data and brand in data["fem"]:
        for other_brand, other_score in data["fem"].items():
            if other_brand == brand:
                continue
            check_and_add("gender", "feminino", data["fem"][brand], other_brand, other_score)

    return {k: dict(v) for k, v in result.items()}

def heatmap_dataframe(avg_table):
    records = []

    for category, subdict in avg_table.items():
        for subcat, brands in subdict.items():
            for brand, score in brands.items():
                records.append({
                    "Categoria": category,
                    "Subcategoria": subcat,
                    "Marca": brand,
                    "Nota Média": score
                })

    df = pd.DataFrame(records)
    return df

