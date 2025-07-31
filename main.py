import pandas as pd
import os
from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter

from scraper import start_browser, get_reviews
from pipeline import extract_pros_cons, get_classification, generate_difference_dictionaries, plotar_nuvens

if __name__ == "__main__":
    data = {}
    companies = ["On", "Hoka", "Nike", "Adidas", "New Balance"]

    for company in companies:
        data[company] = {"M": {}, "F": {}}

    driver = start_browser()
    data["On"]["M"] = get_reviews(driver, "on", "m")
    # data["On"]["F"] = get_reviews(driver, "on", "f")
    # data["Hoka"]["M"] = get_reviews(driver, "hoka", "m")
    # data["Hoka"]["F"] = get_reviews(driver, "hoka", "f")
    # data["Nike"]["M"] = get_reviews(driver, "nike", "m")
    # data["Nike"]["F"] = get_reviews(driver, "nike", "f")
    # data["Adidas"]["M"] = get_reviews(driver, "adidas", "m")
    # data["Adidas"]["F"] = get_reviews(driver, "adidas", "f")
    # data["New Balance"]["M"] = get_reviews(driver, "new-balance", "m")
    # data["New Balance"]["F"] = get_reviews(driver, "new-balance", "f")
    driver.quit()

    pros_dict, cons_dict = extract_pros_cons(data)
    pros_class, cons_class = get_classification(pros_dict, cons_dict)
    print(pros_class, "\n\n", pros_class)
    dict_pros, dict_cons = generate_difference_dictionaries(pros_class, cons_class)
    plotar_nuvens(dict_pros, dict_cons)