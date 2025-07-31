import pandas as pd
import os
from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter

from scraper import start_browser, get_reviews

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
    print(data)
    driver.quit()