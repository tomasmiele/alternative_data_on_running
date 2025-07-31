import re
import math
from collections import Counter
from nltk.corpus import stopwords
from wordcloud import WordCloud
import matplotlib.pyplot as plt

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

def plotar_nuvens(dict_positividade, dict_negatividade):
    wordcloud_pos = WordCloud(
        width=1000, height=500,
        background_color='white',
        max_words=100,
        min_font_size=10,
        relative_scaling=0.5
    ).generate_from_frequencies(dict_positividade)

    wordcloud_neg = WordCloud(
        width=1000, height=500,
        background_color='white',
        max_words=100,
        min_font_size=10,
        relative_scaling=0.5
    ).generate_from_frequencies(dict_negatividade)

    plt.figure(figsize=(12, 6))
    plt.title("Palavras que indicam Positividade")
    plt.imshow(wordcloud_pos, interpolation='bilinear')
    plt.axis("off")
    plt.show()

    plt.figure(figsize=(12, 6))
    plt.title("Palavras que indicam Negatividade")
    plt.imshow(wordcloud_neg, interpolation='bilinear')
    plt.axis("off")
    plt.show()