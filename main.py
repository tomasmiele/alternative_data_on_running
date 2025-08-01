import json
from scraper import start_browser, get_reviews
from pipeline import extract_pros_cons, get_classification, generate_difference_dictionaries, compute_score_aggregates_with_gender, compare_to_others, compare_others_below, classify_on_performance, get_top_rated_models, get_most_negative_comments, build_model_evolution_table

def save_json(data, filename):
    with open(str(filename) + ".json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    data = {}
    companies = ["On", "Hoka", "Nike", "Adidas", "New Balance"]

    for company in companies:
        data[company] = {"M": {}, "F": {}}

    driver = start_browser()
    data["On"]["M"] = get_reviews(driver, "on", "m")
    data["On"]["F"] = get_reviews(driver, "on", "f")
    data["Hoka"]["M"] = get_reviews(driver, "hoka", "m")
    data["Hoka"]["F"] = get_reviews(driver, "hoka", "f")
    data["Nike"]["M"] = get_reviews(driver, "nike", "m")
    data["Nike"]["F"] = get_reviews(driver, "nike", "f")
    data["Adidas"]["M"] = get_reviews(driver, "adidas", "m")
    data["Adidas"]["F"] = get_reviews(driver, "adidas", "f")
    data["New Balance"]["M"] = get_reviews(driver, "new-balance", "m")
    data["New Balance"]["F"] = get_reviews(driver, "new-balance", "f")
    driver.quit()

    save_json(data, "data")

    pros_dict, cons_dict = extract_pros_cons(data)
    pros_class, cons_class = get_classification(pros_dict, cons_dict)
    print(pros_class, "\n\n", pros_class)
    dict_pros, dict_cons = generate_difference_dictionaries(pros_class, cons_class)

    save_json(dict_pros, "positive_words")
    save_json(dict_cons, "negative_words")

    avg_table = compute_score_aggregates_with_gender(data)

    save_json(avg_table, "avg_table")

    on_vs_others = compare_to_others(avg_table, brand="On")
    below_on = compare_others_below(avg_table)

    save_json(on_vs_others, "on_vs_others")
    save_json(below_on, "below_on")

    on_performance = classify_on_performance(avg_table)
    save_json(on_performance, "on_performance")
